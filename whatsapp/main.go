// whatsapp-notify: conexão WhatsApp mínima para o painel de demandas.
//
// - Conecta por QR code (lido no painel) e guarda a sessão fora do git.
// - Envia texto somente para o grupo configurado.
// - Escuta somente esse grupo e guarda apenas as mensagens que citam uma task.
// - Atende apenas em 127.0.0.1. Ações de WhatsApp só funcionam com o número conectado.
//
// Dados: ~/.config/uzapi/whatsapp/ (session.db, config.json, feedback.jsonl).
// Regras: ai.context/demandas/regras/FONTE_BACKLOG.md
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"github.com/skip2/go-qrcode"
	"go.mau.fi/whatsmeow"
	"go.mau.fi/whatsmeow/proto/waE2E"
	"go.mau.fi/whatsmeow/store/sqlstore"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	"google.golang.org/protobuf/proto"
)

const listenAddr = "127.0.0.1:9011"

// "DEM-80", "dem 80", "#80", "task 80", "tarefa 80"
var taskRef = regexp.MustCompile(`(?i)(?:\bdem[-\s]?|#|\btasks?\s*|\btarefas?\s*)(\d{1,4})\b`)

type config struct {
	GroupJID  string `json:"group_jid"`
	GroupName string `json:"group_name"`
}

type feedback struct {
	Data   string   `json:"data"`
	Tasks  []string `json:"tasks"`
	Autor  string   `json:"autor"`
	Numero string   `json:"numero"`
	Texto  string   `json:"texto"`
	MsgID  string   `json:"msg_id"`
}

type app struct {
	dir       string
	container *sqlstore.Container
	mu        sync.Mutex
	client    *whatsmeow.Client
	qr        string
	pairing   bool
	cfg       config
}

func main() {
	home, _ := os.UserHomeDir()
	a := &app{dir: filepath.Join(home, ".config", "uzapi", "whatsapp")}
	if err := os.MkdirAll(a.dir, 0o700); err != nil {
		log.Fatal(err)
	}
	a.loadConfig()

	ctx := context.Background()
	dsn := "file:" + filepath.Join(a.dir, "session.db") + "?_foreign_keys=on"
	container, err := sqlstore.New(ctx, "sqlite3", dsn, nil)
	if err != nil {
		log.Fatal(err)
	}
	a.container = container
	// A sessão equivale a estar logado no WhatsApp: só o dono lê.
	os.Chmod(filepath.Join(a.dir, "session.db"), 0o600)
	if err := a.newClient(ctx); err != nil {
		log.Fatal(err)
	}
	if a.client.Store.ID != nil {
		if err := a.client.Connect(); err != nil {
			log.Printf("conexão: %v", err)
		}
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/status", a.handleStatus)
	mux.HandleFunc("/pair", a.handlePair)
	mux.HandleFunc("/qr.png", a.handleQR)
	mux.HandleFunc("/logout", a.handleLogout)
	mux.HandleFunc("/groups", a.handleGroups)
	mux.HandleFunc("/group", a.handleSetGroup)
	mux.HandleFunc("/send", a.handleSend)
	mux.HandleFunc("/feedback", a.handleFeedback)
	log.Printf("whatsapp-notify em http://%s (dados em %s)", listenAddr, a.dir)
	log.Fatal(http.ListenAndServe(listenAddr, mux))
}

func (a *app) newClient(ctx context.Context) error {
	device, err := a.container.GetFirstDevice(ctx)
	if err != nil {
		return err
	}
	cli := whatsmeow.NewClient(device, nil)
	cli.AddEventHandler(a.onEvent)
	a.mu.Lock()
	a.client = cli
	a.mu.Unlock()
	return nil
}

func (a *app) connected() bool {
	return a.client != nil && a.client.IsConnected() && a.client.IsLoggedIn()
}

// ---- eventos ----

func (a *app) onEvent(evt interface{}) {
	switch v := evt.(type) {
	case *events.Message:
		a.onMessage(v)
	case *events.LoggedOut:
		log.Printf("sessão encerrada pelo WhatsApp")
	}
}

func (a *app) onMessage(m *events.Message) {
	a.mu.Lock()
	group := a.cfg.GroupJID
	a.mu.Unlock()
	if group == "" || m.Info.Chat.String() != group || m.Info.IsFromMe {
		return
	}
	text := m.Message.GetConversation()
	if text == "" {
		text = m.Message.GetExtendedTextMessage().GetText()
	}
	if text == "" {
		return
	}
	seen := map[string]bool{}
	var tasks []string
	for _, g := range taskRef.FindAllStringSubmatch(text, -1) {
		if !seen[g[1]] {
			seen[g[1]] = true
			tasks = append(tasks, g[1])
		}
	}
	if len(tasks) == 0 {
		return // só guarda mensagens que citam task
	}
	fb := feedback{
		Data:   m.Info.Timestamp.Format(time.RFC3339),
		Tasks:  tasks,
		Autor:  m.Info.PushName,
		Numero: m.Info.Sender.User,
		Texto:  text,
		MsgID:  m.Info.ID,
	}
	line, _ := json.Marshal(fb)
	f, err := os.OpenFile(filepath.Join(a.dir, "feedback.jsonl"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
	if err != nil {
		log.Printf("feedback: %v", err)
		return
	}
	defer f.Close()
	f.Write(append(line, '\n'))
}

// ---- HTTP ----

func writeJSON(w http.ResponseWriter, code int, v interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(v)
}

func (a *app) requireConnected(w http.ResponseWriter) bool {
	if !a.connected() {
		writeJSON(w, http.StatusConflict, map[string]string{"error": "WhatsApp desconectado"})
		return false
	}
	return true
}

func (a *app) handleStatus(w http.ResponseWriter, r *http.Request) {
	a.mu.Lock()
	defer a.mu.Unlock()
	st := map[string]interface{}{
		"connected": a.connected(),
		"pairing":   a.pairing,
		"has_qr":    a.qr != "",
		"group_jid": a.cfg.GroupJID,
		"group":     a.cfg.GroupName,
	}
	if a.client != nil && a.client.Store.ID != nil {
		st["number"] = a.client.Store.ID.User
	}
	writeJSON(w, 200, st)
}

// POST /pair: inicia o pareamento por QR (se não houver sessão).
func (a *app) handlePair(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, 405, map[string]string{"error": "use POST"})
		return
	}
	a.mu.Lock()
	if a.client.Store.ID != nil || a.pairing {
		a.mu.Unlock()
		writeJSON(w, 200, map[string]bool{"ok": true})
		return
	}
	a.pairing = true
	cli := a.client
	a.mu.Unlock()

	qrChan, err := cli.GetQRChannel(context.Background())
	if err == nil {
		err = cli.Connect()
	}
	if err != nil {
		a.mu.Lock()
		a.pairing = false
		a.mu.Unlock()
		writeJSON(w, 500, map[string]string{"error": err.Error()})
		return
	}
	go func() {
		for item := range qrChan {
			a.mu.Lock()
			if item.Event == "code" {
				a.qr = item.Code
			} else {
				a.qr = ""
				a.pairing = false
				log.Printf("pareamento: %s", item.Event)
			}
			a.mu.Unlock()
		}
		a.mu.Lock()
		a.pairing = false
		a.qr = ""
		a.mu.Unlock()
	}()
	writeJSON(w, 200, map[string]bool{"ok": true})
}

func (a *app) handleQR(w http.ResponseWriter, r *http.Request) {
	a.mu.Lock()
	code := a.qr
	a.mu.Unlock()
	if code == "" {
		http.Error(w, "sem QR no momento", http.StatusNotFound)
		return
	}
	png, err := qrcode.Encode(code, qrcode.Medium, 320)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.Header().Set("Content-Type", "image/png")
	w.Header().Set("Cache-Control", "no-store")
	w.Write(png)
}

func (a *app) handleLogout(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, 405, map[string]string{"error": "use POST"})
		return
	}
	ctx := context.Background()
	if a.client.Store.ID != nil {
		if err := a.client.Logout(ctx); err != nil {
			log.Printf("logout: %v", err)
		}
	}
	a.client.Disconnect()
	if err := a.newClient(ctx); err != nil {
		writeJSON(w, 500, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]bool{"ok": true})
}

func (a *app) handleGroups(w http.ResponseWriter, r *http.Request) {
	if !a.requireConnected(w) {
		return
	}
	groups, err := a.client.GetJoinedGroups(context.Background())
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": err.Error()})
		return
	}
	out := make([]map[string]string, 0, len(groups))
	for _, g := range groups {
		out = append(out, map[string]string{"jid": g.JID.String(), "name": g.GroupName.Name})
	}
	sort.Slice(out, func(i, j int) bool { return strings.ToLower(out[i]["name"]) < strings.ToLower(out[j]["name"]) })
	writeJSON(w, 200, out)
}

// POST /group {"jid","name"}: define o grupo da empresa.
func (a *app) handleSetGroup(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, 405, map[string]string{"error": "use POST"})
		return
	}
	if !a.requireConnected(w) {
		return
	}
	var body struct{ JID, Name string }
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil || !strings.HasSuffix(body.JID, "@g.us") {
		writeJSON(w, 400, map[string]string{"error": "grupo inválido"})
		return
	}
	a.mu.Lock()
	a.cfg = config{GroupJID: body.JID, GroupName: body.Name}
	err := a.saveConfig()
	a.mu.Unlock()
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]bool{"ok": true})
}

// POST /send {"text"}: envia texto para o grupo configurado.
func (a *app) handleSend(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, 405, map[string]string{"error": "use POST"})
		return
	}
	if !a.requireConnected(w) {
		return
	}
	var body struct{ Text string }
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil || strings.TrimSpace(body.Text) == "" {
		writeJSON(w, 400, map[string]string{"error": "texto vazio"})
		return
	}
	a.mu.Lock()
	group := a.cfg.GroupJID
	a.mu.Unlock()
	if group == "" {
		writeJSON(w, 409, map[string]string{"error": "nenhum grupo configurado"})
		return
	}
	jid, err := types.ParseJID(group)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	resp, err := a.client.SendMessage(context.Background(), jid, &waE2E.Message{Conversation: proto.String(body.Text)})
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]interface{}{"ok": true, "id": resp.ID, "timestamp": resp.Timestamp})
}

// GET /feedback?since=RFC3339: mensagens do grupo que citam tasks.
func (a *app) handleFeedback(w http.ResponseWriter, r *http.Request) {
	since := time.Time{}
	if s := r.URL.Query().Get("since"); s != "" {
		if t, err := time.Parse(time.RFC3339, s); err == nil {
			since = t
		}
	}
	data, err := os.ReadFile(filepath.Join(a.dir, "feedback.jsonl"))
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		writeJSON(w, 500, map[string]string{"error": err.Error()})
		return
	}
	out := []feedback{}
	for _, line := range strings.Split(string(data), "\n") {
		var fb feedback
		if json.Unmarshal([]byte(line), &fb) != nil {
			continue
		}
		if t, err := time.Parse(time.RFC3339, fb.Data); err == nil && t.After(since) {
			out = append(out, fb)
		}
	}
	writeJSON(w, 200, out)
}

// ---- configuração ----

func (a *app) loadConfig() {
	data, err := os.ReadFile(filepath.Join(a.dir, "config.json"))
	if err == nil {
		json.Unmarshal(data, &a.cfg)
	}
}

func (a *app) saveConfig() error {
	data, _ := json.MarshalIndent(a.cfg, "", "  ")
	return os.WriteFile(filepath.Join(a.dir, "config.json"), data, 0o600)
}

