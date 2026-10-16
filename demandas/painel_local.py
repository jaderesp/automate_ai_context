import http.server
import socketserver
import csv
import json
import os
import glob
import sys
import threading
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "planilha"))

PORT = 9000
CSV_PATH = "csv/10092026.csv"
EXEC_DIR = "csv/exec"

# Fonte do backlog: "csv" (padrão) ou "planilha" (--fonte planilha).
# No modo planilha uma thread regrava o CSV local a partir da planilha Google
# a cada SYNC_INTERVAL segundos (somente leitura; ver regras/FONTE_BACKLOG.md).
FONTE = "csv"
SYNC_INTERVAL = 60
_sync = {"ultima": None, "erro": None, "ultima_tentativa": 0.0, "novas": [], "mudancas": []}
_sync_lock = threading.Lock()


def sync_loop():
    """Roda em segundo plano: a exportação da planilha leva dezenas de segundos e
    não pode segurar as requisições da página, que leem sempre o CSV local atual."""
    import planilha_sync
    while True:
        _sync["ultima_tentativa"] = time.time()
        try:
            r = planilha_sync.pull(os.path.abspath(CSV_PATH))
            with _sync_lock:
                _sync.update(ultima=datetime.now().strftime('%d/%m %H:%M:%S'), erro=None,
                             novas=r["novas"], mudancas=r["mudancas"])
        except Exception as err:  # mantém o CSV local e informa no painel
            with _sync_lock:
                _sync["erro"] = str(err)[:300]
        time.sleep(SYNC_INTERVAL)


# Conexão WhatsApp (ai.context/whatsapp/whatsapp-notify, só em 127.0.0.1).
# As ações de WhatsApp do painel só funcionam com o número conectado.
WA_URL = "http://127.0.0.1:9011"
HANDOVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent.session", "HANDOVER.md")


def wa_call(method, path, body=None):
    import urllib.request
    import urllib.error
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(WA_URL + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "application/json")
    except urllib.error.HTTPError as err:
        return err.code, err.read(), err.headers.get("Content-Type", "application/json")
    except Exception:
        msg = {"error": "whatsapp-notify não está rodando", "running": False, "connected": False}
        return 503, json.dumps(msg).encode("utf-8"), "application/json"


def ler_frontmatter(content):
    """Campos simples (chave: valor) do bloco YAML inicial do arquivo da demanda."""
    campos = {}
    if content.startswith('---'):
        for line in content.split('\n')[1:]:
            if line.strip() == '---':
                break
            if ':' in line:
                k, v = line.split(':', 1)
                campos[k.strip()] = v.strip()
    return campos


def registrar_notificacao(task_id, texto, tipo='teste'):
    """Registra o envio no arquivo da demanda (se existir) e no HANDOVER.md."""
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    rotulo = {'producao': "aviso de produção", 'standby': "cobrança de alinhamento"}.get(tipo, "notificação de teste")
    bloco = f"\n\n### 📣 WhatsApp: {rotulo} enviada ao grupo ({agora})\n```\n{texto}\n```\n"
    for pasta in (EXEC_DIR, "csv/standby.solution"):
        arq = f"{pasta}/DEM-{task_id}.md"
        if os.path.exists(arq):
            with open(arq, 'a', encoding='utf-8') as f:
                f.write(bloco)
            break
    if os.path.exists(HANDOVER_PATH):
        with open(HANDOVER_PATH, 'a', encoding='utf-8') as f:
            f.write(f"\n- **{agora} — WhatsApp:** {rotulo} da DEM-{task_id} enviada ao grupo pelo painel (autorizada pelo desenvolvedor no envio).\n")


# Configurar para reaproveitar a porta se o servidor for reiniciado rapidamente
socketserver.TCPServer.allow_reuse_address = True

html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UzAPI - Kanban de Demandas IA</title>
    <script src="https://cdn.tailwindcss.com?plugins=typography">
        async function takeSnapshot() {
            const modal = document.getElementById('taskModalContent');
            const scrollArea = modal.querySelector('.overflow-y-auto');
            const btn = event.currentTarget;
            const originalIcon = btn.innerHTML;
            
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Gerando...';
            
            // Salva estilos originais
            const originalHeight = modal.style.height;
            const originalOverflow = modal.style.overflow;
            const origScrollOverflow = scrollArea.style.overflow;
            const origScrollHeight = scrollArea.style.maxHeight;
            
            // Prepara para tirar foto inteira (expande)
            modal.style.height = 'auto';
            modal.style.overflow = 'visible';
            scrollArea.style.overflow = 'visible';
            scrollArea.style.maxHeight = 'none';
            
            try {
                const canvas = await html2canvas(modal, {
                    scale: 2, // Maior resolução
                    backgroundColor: '#ffffff',
                    windowWidth: modal.scrollWidth,
                    windowHeight: modal.scrollHeight
                });
                
                const imgData = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                // Nome do arquivo amigável
                const safeName = document.getElementById('modalTitle').innerText.replace(/[^a-z0-9]/gi, '_').toLowerCase();
                link.download = `demanda_${safeName}.png`;
                link.href = imgData;
                link.click();
            } catch(e) {
                console.error(e);
                alert('Erro ao gerar imagem da demanda.');
            } finally {
                // Restaura interface
                modal.style.height = originalHeight;
                modal.style.overflow = originalOverflow;
                scrollArea.style.overflow = origScrollOverflow;
                scrollArea.style.maxHeight = origScrollHeight;
                btn.innerHTML = originalIcon;
            }
        }

    </script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
        .kanban-col { min-height: 500px; }
        .task-card { transition: all 0.2s ease; border-left: 4px solid transparent; }
        .task-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .task-alta { border-left-color: #ef4444; }
        .task-media { border-left-color: #f59e0b; }
        .task-baixa { border-left-color: #10b981; }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        
        /* Modo noturno: sobrescreve as classes utilitárias usadas no painel */
        html.dark body { background-color: #0b1220; color: #e2e8f0; }
        html.dark .bg-white { background-color: #1e293b; }
        html.dark .bg-slate-50, html.dark [class~="bg-slate-50/50"] { background-color: #172033; }
        html.dark .bg-slate-100 { background-color: #131c2e; }
        html.dark .bg-slate-200 { background-color: #334155; }
        html.dark .bg-blue-50 { background-color: #101b33; }
        html.dark [class~="bg-blue-100/30"] { background-color: #14223f; }
        html.dark .bg-amber-50 { background-color: #1f1a0e; }
        html.dark [class~="bg-amber-100/40"] { background-color: #2a2210; }
        html.dark .bg-violet-50 { background-color: #1a1430; }
        html.dark [class~="bg-violet-100/40"] { background-color: #231a40; }
        html.dark .bg-emerald-50 { background-color: #0d211b; }
        html.dark [class~="bg-emerald-100/30"] { background-color: #102a22; }
        html.dark .bg-blue-100, html.dark .bg-blue-200 { background-color: #1e3a8a; }
        html.dark .bg-amber-100, html.dark .bg-amber-200 { background-color: #4a3410; }
        html.dark .bg-violet-100, html.dark .bg-violet-200 { background-color: #3b2a70; }
        html.dark .bg-emerald-100, html.dark .bg-emerald-200 { background-color: #064e3b; }
        html.dark .bg-red-100 { background-color: #4c1d1d; }
        html.dark .text-slate-900, html.dark .text-slate-800, html.dark .text-slate-700 { color: #e2e8f0; }
        html.dark .text-slate-600, html.dark .text-slate-500 { color: #94a3b8; }
        html.dark .text-blue-800, html.dark .text-blue-700 { color: #93c5fd; }
        html.dark .text-amber-800, html.dark .text-amber-900 { color: #fcd34d; }
        html.dark .text-violet-800, html.dark .text-violet-900, html.dark .text-violet-700 { color: #c4b5fd; }
        html.dark .text-emerald-800, html.dark .text-emerald-700 { color: #6ee7b7; }
        html.dark .text-red-700 { color: #fca5a5; }
        html.dark .border-slate-100, html.dark .border-slate-200, html.dark .border-slate-300 { border-color: #334155; }
        html.dark .border-blue-100, html.dark .border-blue-200 { border-color: #1e3a8a; }
        html.dark .border-amber-200, html.dark .border-amber-300 { border-color: #713f12; }
        html.dark .border-violet-200 { border-color: #4c3a8f; }
        html.dark .border-emerald-100, html.dark .border-emerald-200 { border-color: #065f46; }
        html.dark [class~="hover:bg-slate-50"]:hover, html.dark [class~="hover:bg-slate-200"]:hover { background-color: #273449; }
        html.dark input, html.dark select, html.dark textarea { background-color: #0f172a; color: #e2e8f0; border-color: #334155; }
        html.dark .prose, html.dark .prose :where(p, li, td, th, strong, h1, h2, h3, h4, code) { color: #e2e8f0; }
        html.dark .prose :where(pre) { background-color: #0b1220; }
        html.dark #loader { background: rgba(11,18,32,0.8); }
        html.dark .custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; }

        /* Loading Overlay */
        #loader { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); z-index: 50; justify-content: center; align-items: center; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3b82f6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
</head>
<body class="text-slate-800 h-screen flex flex-col">

    <div id="loader"><div class="spinner"></div></div>

    <!-- Header & Filters -->
    <header class="bg-white shadow-sm border-b border-slate-200 z-10 sticky top-0">
        <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <div class="bg-blue-600 text-white p-2 rounded-lg"><i class="fa-solid fa-robot"></i></div>
                    <div>
                        <h1 class="text-xl font-bold text-slate-900 leading-tight">UzAPI Demandas</h1>
                        <p class="text-xs text-slate-500">Gestão Integrada Homem + Inteligência Artificial</p>
                    </div>
                </div>

                <!-- Dynamic Filters -->
                <div class="flex flex-wrap items-center md:justify-end gap-3">
                    <div class="relative">
                        <i class="fa-solid fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400"></i>
                        <input type="text" id="searchInput" placeholder="Buscar título ou ID..." class="pl-9 pr-4 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full md:w-64 outline-none transition-all">
                    </div>
                    <select id="prioFilter" class="border border-slate-300 rounded-md text-sm py-2 px-3 outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                        <option value="">Todas Prioridades</option>
                        <option value="alta">🔴 Alta</option>
                        <option value="média">🟡 Média</option>
                        <option value="baixa">🟢 Baixa/Normal</option>
                    </select>
                    <button id="themeBtn" onclick="toggleTheme()" title="Alternar modo noturno" class="whitespace-nowrap shrink-0 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-medium py-2 px-3 rounded-md text-sm transition-colors shadow-sm"><i id="themeIcon" class="fa-solid fa-moon"></i></button>
                    <button id="waBtn" onclick="openWaModal()" class="whitespace-nowrap shrink-0 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-medium py-2 px-4 rounded-md text-sm transition-colors flex items-center gap-2 shadow-sm">
                        <i class="fa-brands fa-whatsapp text-emerald-600"></i> WhatsApp <span id="waDot" class="inline-block w-2 h-2 rounded-full bg-slate-300"></span>
                    </button>
                    <button id="fbBtn" onclick="openFeedback()" class="whitespace-nowrap shrink-0 hidden bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-medium py-2 px-4 rounded-md text-sm transition-colors flex items-center gap-2 shadow-sm">
                        <i class="fa-solid fa-comments text-slate-500"></i> Feedbacks do grupo
                    </button>
                    <button onclick="openNewTaskModal()" class="whitespace-nowrap shrink-0 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md text-sm transition-colors flex items-center gap-2 shadow-sm">
                        <i class="fa-solid fa-plus"></i> Nova Demanda
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Kanban Board -->
    <main class="flex-1 overflow-x-auto p-4 sm:p-6 lg:p-8">
        <div class="flex gap-6 items-start min-w-max h-full">
            
            <!-- Col 1: Backlog -->
            <div class="bg-slate-100 rounded-xl w-96 flex flex-col max-h-[85vh] border border-slate-200 shadow-sm">
                <div class="p-4 border-b border-slate-200 bg-slate-50/50 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-slate-700 flex items-center gap-2"><i class="fa-solid fa-inbox text-slate-400"></i> <span id="backlog-title">Backlog (CSV)</span></h2>
                    <span id="count-backlog" class="bg-slate-200 text-slate-600 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-backlog" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

            <!-- Col 2: Desenvolvimento (Andamento) -->
            <div class="bg-blue-50 rounded-xl w-96 flex flex-col max-h-[85vh] border border-blue-100 shadow-sm">
                <div class="p-4 border-b border-blue-100 bg-blue-100/30 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-blue-800 flex items-center gap-2"><i class="fa-solid fa-code text-blue-500"></i> Desenvolvimento (Andamento)</h2>
                    <span id="count-ia" class="bg-blue-200 text-blue-800 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-ia" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

            <!-- Col 3: Standby (Aguardando Decisão) -->
            <div class="bg-amber-50 rounded-xl w-96 flex flex-col max-h-[85vh] border border-amber-200 shadow-sm">
                <div class="p-4 border-b border-amber-200 bg-amber-100/40 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-amber-800 flex items-center gap-2"><i class="fa-solid fa-pause-circle text-amber-500"></i> Standby (Decisão)</h2>
                    <span id="count-standby" class="bg-amber-200 text-amber-900 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-standby" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

            <!-- Col 4: Em teste (dev) -->
            <div class="bg-violet-50 rounded-xl w-96 flex flex-col max-h-[85vh] border border-violet-200 shadow-sm">
                <div class="p-4 border-b border-violet-200 bg-violet-100/40 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-violet-800 flex items-center gap-2"><i class="fa-solid fa-flask text-violet-500"></i> Em teste (dev)</h2>
                    <span id="count-teste" class="bg-violet-200 text-violet-900 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-teste" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

            <!-- Col 5: Concluídas (produção) -->
            <div class="bg-emerald-50 rounded-xl w-96 flex flex-col max-h-[85vh] border border-emerald-100 shadow-sm">
                <div class="p-4 border-b border-emerald-100 bg-emerald-100/30 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-emerald-800 flex items-center gap-2"><i class="fa-solid fa-check-circle text-emerald-500"></i> Concluídas (produção)</h2>
                    <span id="count-done" class="bg-emerald-200 text-emerald-800 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-done" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

        </div>
    </main>

    <!-- Modal WhatsApp (conexão, notificação e feedbacks) -->
    <div id="waModal" class="fixed inset-0 bg-slate-900/50 hidden z-50 flex justify-center items-center">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-xl mx-4 max-h-[90vh] flex flex-col">
            <div class="p-4 border-b border-slate-200 flex justify-between items-center">
                <h2 id="waModalTitle" class="font-semibold text-slate-800">WhatsApp</h2>
                <button onclick="closeWaModal()" class="text-slate-500 hover:text-slate-800"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div id="waModalBody" class="p-5 overflow-y-auto text-sm text-slate-700"></div>
        </div>
    </div>

    <!-- Modal de Detalhes da Demanda (50% da tela) -->
    <div id="taskModal" class="fixed inset-0 bg-slate-900/50 hidden z-50 flex justify-end transition-opacity">
        <div class="bg-white w-full md:w-1/2 h-full shadow-2xl flex flex-col overflow-hidden transform translate-x-full transition-transform duration-300" id="taskModalContent">
            <div class="flex justify-between items-center p-6 border-b border-slate-200">
                <h2 class="text-xl font-bold text-slate-800" id="modalTitle">Detalhes da Demanda</h2>
                <div class="flex gap-4 items-center" data-html2canvas-ignore>
                    <button onclick="takeSnapshot()" class="text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded text-sm font-bold transition-colors border border-blue-200 flex items-center gap-2">
                        <i class="fa-solid fa-camera"></i> Snapshot
                    </button>
                    <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600 transition-colors">
                        <i class="fa-solid fa-xmark text-2xl"></i>
                    </button>
                </div>
            </div>
            <div class="p-6 flex-1 overflow-y-auto custom-scrollbar min-h-0">
                <div class="flex gap-2 mb-6" id="modalBadges"></div>
                
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2" id="modalDescTitle">Descrição</h3>
                <div id="modalDesc" class="mb-6"></div>
                
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-100">
                        <h3 class="text-xs font-bold text-slate-500 uppercase mb-1">Módulo</h3>
                        <p class="font-medium text-slate-800" id="modalModulo"></p>
                    </div>
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-100">
                        <h3 class="text-xs font-bold text-slate-500 uppercase mb-1">Status (IA)</h3>
                        <p class="font-medium text-slate-800" id="modalStatus"></p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal de Nova Demanda -->
    <div id="newTaskModal" class="fixed inset-0 bg-slate-900/50 hidden z-50 flex justify-center items-center transition-opacity">
        <div class="bg-white w-full max-w-3xl rounded-xl shadow-2xl flex flex-col transform scale-95 transition-transform duration-300" id="newTaskModalContent">
            <div class="flex justify-between items-center p-6 border-b border-slate-200">
                <h2 class="text-xl font-bold text-slate-800">Adicionar Nova Demanda</h2>
                <button onclick="closeNewTaskModal()" class="text-slate-400 hover:text-slate-600 transition-colors">
                    <i class="fa-solid fa-xmark text-2xl"></i>
                </button>
            </div>
            <form id="newTaskForm" onsubmit="submitNewTask(event)" class="p-6 overflow-y-auto max-h-[80vh] custom-scrollbar">
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Título</label>
                        <input type="text" id="nt_titulo" required class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Tipo</label>
                        <select id="nt_tipo" required class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                            <option value="Feature">Feature</option>
                            <option value="Bug">Bug</option>
                            <option value="Melhoria">Melhoria</option>
                            <option value="Refatoração">Refatoração</option>
                        </select>
                    </div>
                </div>
                <div class="mb-4">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Descrição</label>
                    <textarea id="nt_desc" required rows="4" class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none"></textarea>
                </div>
                <div class="grid grid-cols-3 gap-4 mb-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Módulo</label>
                        <input type="text" id="nt_modulo" required class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Prioridade</label>
                        <select id="nt_prio" required class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                            <option value="Baixa">Baixa</option>
                            <option value="Média">Média</option>
                            <option value="Alta">Alta</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Responsável</label>
                        <input type="text" id="nt_resp" required class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Versão (opcional)</label>
                        <input type="text" id="nt_versao" class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Observações (opcional)</label>
                        <input type="text" id="nt_obs" class="w-full border border-slate-300 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                </div>
                <div class="flex justify-end gap-3 pt-4 border-t border-slate-200">
                    <button type="button" onclick="closeNewTaskModal()" class="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors">Cancelar</button>
                    <button type="submit" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">Salvar Demanda</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let allDemands = [];
        let fonteInfo = { fonte: 'csv' };
        const WATCH_COLS = ['Status', 'Observações', 'Testado Em', 'Versão', 'Título', 'Prioridade'];

        async function loadFonte() {
            try {
                fonteInfo = await (await fetch('/api/fonte')).json();
            } catch (e) { return; }
            const el = document.getElementById('backlog-title');
            if (fonteInfo.fonte !== 'planilha') { el.innerText = 'Backlog (CSV)'; return; }
            el.innerText = fonteInfo.erro
                ? 'Backlog (Planilha · falha na sincronização)'
                : 'Backlog (Planilha · ' + (fonteInfo.ultima || 'sincronizando') + ')';
            el.title = fonteInfo.erro || ('Atualiza a cada ' + fonteInfo.intervalo + ' s');
        }

        function diffDemands(oldList, newList) {
            const byId = {};
            oldList.forEach(d => { byId[d.ID] = d; });
            const msgs = [];
            newList.forEach(d => {
                const o = byId[d.ID];
                if (!(d.Título || '').trim()) return;
                if (!o || !(o.Título || '').trim()) { msgs.push('Nova: #' + d.ID + ' ' + d.Título); return; }
                WATCH_COLS.forEach(c => {
                    if ((o[c] || '').trim() !== (d[c] || '').trim()) {
                        const depois = (d[c] || '').trim();
                        msgs.push('#' + d.ID + ' ' + c + ': ' + (depois.length > 60 ? depois.slice(0, 57) + '...' : depois));
                    }
                });
            });
            return msgs;
        }

        function showUpdates(msgs) {
            if (!msgs.length) return;
            let box = document.getElementById('updates-box');
            if (!box) {
                box = document.createElement('div');
                box.id = 'updates-box';
                box.className = 'fixed bottom-4 right-4 z-40 max-w-md bg-amber-50 border border-amber-300 text-amber-900 text-sm rounded-lg shadow-lg p-4';
                document.body.appendChild(box);
            }
            const hora = new Date().toLocaleTimeString();
            box.innerHTML = '<div class="flex justify-between items-center mb-2"><strong>Atualizações da planilha (' + hora + ')</strong>'
                + '<button onclick="this.closest(&quot;#updates-box&quot;).remove()" class="ml-4 text-amber-700">✕</button></div>'
                + '<ul class="list-disc pl-5 space-y-1">' + msgs.slice(0, 15).map(m => '<li></li>').join('') + '</ul>'
                + (msgs.length > 15 ? '<div class="mt-2">+' + (msgs.length - 15) + ' outras</div>' : '');
            const items = box.querySelectorAll('li');
            msgs.slice(0, 15).forEach((m, i) => { items[i].textContent = m; });
        }

        async function silentRefresh() {
            if (fonteInfo.fonte !== 'planilha') return;
            try {
                const res = await fetch('/api/demandas');
                const fresh = await res.json();
                const msgs = diffDemands(allDemands, fresh);
                allDemands = fresh;
                renderBoard();
                showUpdates(msgs);
            } catch (e) { /* tenta de novo no próximo ciclo */ }
            loadFonte();
        }

        async function fetchDemands() {
            document.getElementById('loader').style.display = 'flex';
            try {
                const res = await fetch('/api/demandas');
                allDemands = await res.json();
                renderBoard();
            } catch(e) {
                alert('Erro ao carregar demandas.');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function getPriorityStyle(prio) {
            prio = (prio || '').toLowerCase();
            if (prio === 'alta') return { color: 'text-red-700 bg-red-100', border: 'task-alta', icon: '🔴' };
            if (prio === 'média' || prio === 'media') return { color: 'text-amber-700 bg-amber-100', border: 'task-media', icon: '🟡' };
            return { color: 'text-emerald-700 bg-emerald-100', border: 'task-baixa', icon: '🟢' };
        }

        function openModal(id) {
            const d = allDemands.find(x => x.ID === id);
            if(!d) return;
            
            document.getElementById('modalTitle').innerText = d.Título;
            document.getElementById('modalModulo').innerText = d.Módulo;
            document.getElementById('modalStatus').innerText = (d.ia_status || 'N/A').toUpperCase();
            
            if (d.md_content) {
                document.getElementById('modalDescTitle').innerText = "Histórico de Execução";
                // Remove o cabeçalho YAML frontmatter do markdown
                let cleanMd = d.md_content.replace(/^---\\n[\\s\\S]*?\\n---\\n/, '');
                document.getElementById('modalDesc').innerHTML = `<div class="prose prose-sm md:prose-base max-w-none prose-slate prose-headings:text-blue-800 prose-a:text-blue-600 bg-slate-50 p-5 rounded-xl border border-slate-200">` + marked.parse(cleanMd) + `</div>`;
            } else {
                document.getElementById('modalDescTitle').innerText = "Descrição Original";
                document.getElementById('modalDesc').innerHTML = `<div class="bg-slate-50 p-4 rounded-lg border border-slate-100 text-slate-700 whitespace-pre-wrap">${d.Descrição}</div>`;
            }
            
            const style = getPriorityStyle(d.Prioridade);
            document.getElementById('modalBadges').innerHTML = `
                <span class="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">#${d.ID}</span>
                <span class="text-xs font-bold px-3 py-1 rounded-full ${style.color}">${style.icon} ${d.Prioridade.toUpperCase()}</span>
            `;
            
            const modal = document.getElementById('taskModal');
            const content = document.getElementById('taskModalContent');
            modal.classList.remove('hidden');
            setTimeout(() => {
                content.classList.remove('translate-x-full');
            }, 10);
        }

        function closeModal() {
            const modal = document.getElementById('taskModal');
            const content = document.getElementById('taskModalContent');
            content.classList.add('translate-x-full');
            setTimeout(() => {
                modal.classList.add('hidden');
            }, 300);
        }

        function openNewTaskModal() {
            if (fonteInfo.fonte === 'planilha') {
                alert('Modo planilha: cadastre a task na planilha Google. Ela aparece aqui na próxima sincronização (até 1 minuto).');
                return;
            }
            document.getElementById('newTaskForm').reset();
            const modal = document.getElementById('newTaskModal');
            const content = document.getElementById('newTaskModalContent');
            modal.classList.remove('hidden');
            setTimeout(() => {
                content.classList.remove('scale-95');
                content.classList.add('scale-100');
            }, 10);
        }

        function closeNewTaskModal() {
            const modal = document.getElementById('newTaskModal');
            const content = document.getElementById('newTaskModalContent');
            content.classList.remove('scale-100');
            content.classList.add('scale-95');
            setTimeout(() => {
                modal.classList.add('hidden');
            }, 300);
        }

        async function submitNewTask(e) {
            e.preventDefault();
            
            const payload = {
                Tipo: document.getElementById('nt_tipo').value,
                Título: document.getElementById('nt_titulo').value,
                Descrição: document.getElementById('nt_desc').value,
                Módulo: document.getElementById('nt_modulo').value,
                Prioridade: document.getElementById('nt_prio').value,
                Responsável: document.getElementById('nt_resp').value,
                Versão: document.getElementById('nt_versao').value,
                Observações: document.getElementById('nt_obs').value
            };

            document.getElementById('loader').style.display = 'flex';
            try {
                const res = await fetch('/api/nova-demanda', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if(res.ok) {
                    closeNewTaskModal();
                    await fetchDemands();
                } else {
                    alert('Erro ao salvar demanda.');
                }
            } catch(e) {
                alert('Falha na comunicação com servidor.');
            }
            document.getElementById('loader').style.display = 'none';
        }

        // ---------------- WhatsApp ----------------
        const NL = String.fromCharCode(10);
        let waState = { running: false, connected: false };
        let waNotifyTipo = 'teste';
        let waView = null;
        let waPoll = null;

        async function loadWa() {
            try {
                waState = await (await fetch('/api/wa/status')).json();
            } catch (e) {
                waState = { running: false, connected: false };
            }
            const dot = document.getElementById('waDot');
            dot.className = 'inline-block w-2 h-2 rounded-full ' + (waState.connected ? 'bg-emerald-500' : (waState.running ? 'bg-amber-400' : 'bg-slate-300'));
            document.getElementById('fbBtn').classList.toggle('hidden', !waState.connected);
            renderBoard();
            if (waView === 'conn') renderWaConn();
        }

        function openWaShell(title) {
            document.getElementById('waModalTitle').innerText = title;
            document.getElementById('waModal').classList.remove('hidden');
        }

        function closeWaModal() {
            document.getElementById('waModal').classList.add('hidden');
            waView = null;
            if (waPoll) { clearInterval(waPoll); waPoll = null; }
        }

        function openWaModal() {
            waView = 'conn';
            openWaShell('Conexão WhatsApp');
            renderWaConn();
            if (!waPoll) waPoll = setInterval(loadWa, 2500);
        }

        async function renderWaConn() {
            const body = document.getElementById('waModalBody');
            if (!waState.running) {
                body.innerHTML = '<p>O módulo de WhatsApp não está rodando. Inicie no terminal:</p>'
                    + '<pre class="mt-2 bg-slate-100 p-3 rounded text-xs">ai.context/whatsapp/whatsapp-notify</pre>';
                return;
            }
            if (!waState.connected) {
                if (waState.has_qr) {
                    body.innerHTML = '<p class="mb-3">No celular: WhatsApp → Aparelhos conectados → Conectar aparelho, e leia o QR:</p>'
                        + '<img class="mx-auto border rounded" width="320" height="320" src="/api/wa/qr.png?t=' + Date.now() + '">'
                        + '<p class="mt-3 text-xs text-slate-500">O código muda a cada poucos segundos; a imagem se atualiza sozinha.</p>';
                } else if (waState.pairing) {
                    body.innerHTML = '<p>Gerando QR code...</p>';
                } else {
                    body.innerHTML = '<p class="mb-4">Número desconectado. As ações de WhatsApp do painel ficam desativadas até conectar.</p>'
                        + '<button onclick="waPair()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-md">Conectar (gerar QR code)</button>';
                }
                return;
            }
            if (body.dataset.connected === '1' && body.dataset.number === (waState.number || '')) return;
            body.dataset.connected = '1';
            body.dataset.number = waState.number || '';
            body.innerHTML = '<p class="mb-3">Conectado ao número <strong>' + (waState.number || '?') + '</strong>.</p>'
                + '<label class="block font-medium mb-1">Grupo da empresa</label>'
                + '<div class="flex gap-2 mb-1"><select id="waGroup" class="flex-1 border border-slate-300 rounded-md py-2 px-3"><option>Carregando grupos...</option></select>'
                + '<button onclick="waSaveGroup()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md">Salvar</button></div>'
                + '<p id="waGroupInfo" class="text-xs text-slate-500 mb-5"></p>'
                + '<button onclick="waLogout()" class="text-red-600 hover:text-red-800 text-sm"><i class="fa-solid fa-link-slash"></i> Desconectar número</button>';
            document.getElementById('waGroupInfo').innerText = waState.group ? ('Grupo atual: ' + waState.group) : 'Nenhum grupo configurado.';
            try {
                const groups = await (await fetch('/api/wa/groups')).json();
                const sel = document.getElementById('waGroup');
                sel.innerHTML = '';
                groups.forEach(g => {
                    const o = document.createElement('option');
                    o.value = g.jid; o.textContent = g.name || g.jid;
                    if (g.jid === waState.group_jid) o.selected = true;
                    sel.appendChild(o);
                });
            } catch (e) { /* lista indisponível */ }
        }

        async function waPair() {
            await fetch('/api/wa/pair', { method: 'POST' });
            loadWa();
        }

        async function waSaveGroup() {
            const sel = document.getElementById('waGroup');
            const opt = sel.options[sel.selectedIndex];
            if (!opt) return;
            const res = await fetch('/api/wa/group', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ jid: opt.value, name: opt.textContent }) });
            const r = await res.json();
            if (!res.ok) { alert(r.error || 'Erro ao salvar grupo'); return; }
            document.getElementById('waGroupInfo').innerText = 'Grupo atual: ' + opt.textContent;
            loadWa();
        }

        async function waLogout() {
            if (!confirm('Desconectar o número do WhatsApp? Será preciso ler o QR de novo.')) return;
            await fetch('/api/wa/logout', { method: 'POST' });
            const body = document.getElementById('waModalBody');
            body.dataset.connected = '';
            loadWa();
        }

        function buildNotice(d) {
            const versao = (d.Versão || '').trim();
            const dev = versao.toLowerCase().includes('dev');
            const linhas = [
                '✅ *Task #' + d.ID + ' liberada para teste*',
                '📌 ' + (d.Título || ''),
                '🧪 Ambiente: ' + (dev ? 'dev — painel.dev.uzapi.com.br' : 'produção — painel.uzapi.com.br'),
                '⚙️ Versão do worker: ' + (versao || 'a confirmar'),
            ];
            const obs = (d.Observações || '').trim();
            if (obs) linhas.push('', '📝 ' + obs);
            linhas.push('', 'Após o teste, atualize o status na planilha (Aprovado, ou Devolvido com o motivo).');
            return linhas.join(NL);
        }

        function buildProdNotice(d) {
            const linhas = [
                '🚀 *Task #' + d.ID + ' em produção*',
                '📌 ' + (d.Título || ''),
            ];
            if (d.versao_producao) linhas.push('📦 Versão: ' + d.versao_producao);
            linhas.push('🤖 Worker: ' + (d.versao_worker || '(informar)'));
            linhas.push('Já disponível para os clientes.');
            return linhas.join(NL);
        }

        function buildStandbyNotice(d) {
            const desde = (d.data_standby || '').slice(0, 10).split('-').reverse().join('/');
            const quem = d.aguardando || '(responsável)';
            const linhas = [
                '⏸️ *Task #' + d.ID + ' aguardando alinhamento*',
                '📌 ' + (d.Título || ''),
                '👤 ' + quem + ', pode me dar um retorno?',
                '❓ ' + (d.pendencia || '(pendência)'),
            ];
            if (desde) linhas.push('⏳ Em standby desde ' + desde);
            return linhas.join(NL);
        }

        // Menções: membros do grupo (GET /participants); cada escolhido vira "@<user>" no texto.
        let waMembers = [];
        let waMentions = {};

        async function loadMembers(sugerido) {
            const sel = document.getElementById('ntMention');
            if (!sel) return;
            try {
                const res = await fetch('/api/wa/participants');
                waMembers = res.ok ? await res.json() : [];
            } catch (e) { waMembers = []; }
            sel.innerHTML = '<option value="">@ Mencionar alguém do grupo...</option>' + waMembers.map((m, i) =>
                '<option value="' + i + '">' + (m.nome || m.numero || m.user).replace(/</g, '&lt;') + (m.numero ? ' (' + m.numero + ')' : '') + '</option>').join('');
            if (!waMembers.length) sel.innerHTML = '<option value="">(sem membros para mencionar)</option>';
            if (sugerido) {
                const alvo = sugerido.toLowerCase();
                const i = waMembers.findIndex(m => (m.nome || '').toLowerCase().includes(alvo));
                if (i >= 0) {
                    const ta = document.getElementById('ntText');
                    const m = waMembers[i];
                    ta.value = ta.value.replace(sugerido + ',', '@' + m.user + ',');
                    waMentions[m.user] = m.jid;
                    renderMentions();
                }
            }
        }

        function addMention() {
            const sel = document.getElementById('ntMention');
            const m = waMembers[parseInt(sel.value, 10)];
            sel.value = '';
            if (!m) return;
            const ta = document.getElementById('ntText');
            const pos = ta.selectionStart ?? ta.value.length;
            const tag = '@' + m.user + ' ';
            ta.value = ta.value.slice(0, pos) + tag + ta.value.slice(pos);
            ta.focus();
            ta.selectionStart = ta.selectionEnd = pos + tag.length;
            waMentions[m.user] = m.jid;
            renderMentions();
        }

        function renderMentions() {
            const box = document.getElementById('ntMentions');
            if (!box) return;
            const nomes = Object.keys(waMentions).map(u => {
                const m = waMembers.find(x => x.user === u);
                return (m && (m.nome || m.numero)) || u;
            });
            box.innerText = nomes.length ? 'Menções: ' + nomes.join(', ') + ' (o @número aparece como nome no WhatsApp)' : '';
        }

        function openNotify(id, tipo) {
            if (!waState.connected) { alert('WhatsApp desconectado.'); return; }
            if (!waState.group_jid) { alert('Configure o grupo no botão WhatsApp.'); openWaModal(); return; }
            const d = allDemands.find(x => x.ID === id);
            if (!d) return;
            waView = 'notify';
            const producao = tipo === 'producao';
            const standby = tipo === 'standby';
            openWaShell((producao ? 'Avisar produção — DEM-' : standby ? 'Cobrar alinhamento — DEM-' : 'Notificar QA — DEM-') + id);
            waMentions = {};
            const body = document.getElementById('waModalBody');
            body.dataset.connected = '';
            body.innerHTML = '<p class="mb-2">Grupo: <strong id="ntGroup"></strong>. Revise e edite antes de enviar:</p>'
                + '<textarea id="ntText" rows="14" class="w-full border border-slate-300 rounded-md p-3 text-sm font-mono"></textarea>'
                + '<div class="flex flex-wrap items-center gap-2 mt-2"><select id="ntMention" onchange="addMention()" class="border border-slate-300 rounded-md px-2 py-1 text-sm bg-white"><option value="">Carregando membros...</option></select>'
                + '<span id="ntMentions" class="text-xs text-slate-500"></span></div>'
                + '<div class="flex justify-end gap-2 mt-3"><button onclick="closeWaModal()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-md">Cancelar</button>'
                + '<button id="ntSend" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md"><i class="fa-brands fa-whatsapp"></i> Enviar</button></div>';
            document.getElementById('ntGroup').innerText = waState.group || waState.group_jid;
            document.getElementById('ntText').value = producao ? buildProdNotice(d) : standby ? buildStandbyNotice(d) : buildNotice(d);
            waNotifyTipo = producao ? 'producao' : standby ? 'standby' : 'teste';
            loadMembers(standby ? d.aguardando : '');
            document.getElementById('ntSend').onclick = () => sendNotify(id);
        }

        async function sendNotify(id) {
            const text = document.getElementById('ntText').value.trim();
            if (!text) return;
            // Só vão as menções cujo @<user> continua no texto.
            const mentions = Object.keys(waMentions).filter(u => text.includes('@' + u)).map(u => waMentions[u]);
            const btn = document.getElementById('ntSend');
            btn.disabled = true; btn.innerText = 'Enviando...';
            const res = await fetch('/api/wa/send', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, text: text, tipo: waNotifyTipo, mentions: mentions }) });
            const r = await res.json();
            if (!res.ok) { alert(r.error || 'Falha no envio'); btn.disabled = false; btn.innerText = 'Enviar'; return; }
            closeWaModal();
            alert('Notificação da DEM-' + id + ' enviada ao grupo.');
        }

        async function openFeedback() {
            if (!waState.connected) return;
            waView = 'feedback';
            openWaShell('Feedbacks do grupo (mensagens que citam tasks)');
            const body = document.getElementById('waModalBody');
            body.dataset.connected = '';
            body.innerHTML = '<p>Carregando...</p>';
            const items = await (await fetch('/api/wa/feedback')).json();
            if (!items.length) { body.innerHTML = '<p>Nenhuma mensagem citando task até agora.</p>'; return; }
            const porTask = {};
            items.forEach(fb => (fb.tasks || []).forEach(t => { (porTask[t] = porTask[t] || []).push(fb); }));
            body.innerHTML = '';
            Object.keys(porTask).sort((a, b) => Number(b) - Number(a)).forEach(t => {
                const h = document.createElement('h3');
                h.className = 'font-semibold text-slate-800 mt-4 mb-2';
                h.textContent = 'DEM-' + t;
                body.appendChild(h);
                porTask[t].slice().reverse().forEach(fb => {
                    const div = document.createElement('div');
                    div.className = 'bg-slate-50 border border-slate-200 rounded p-2 mb-2';
                    const meta = document.createElement('div');
                    meta.className = 'text-xs text-slate-500 mb-1';
                    meta.textContent = new Date(fb.data).toLocaleString() + ' — ' + (fb.autor || fb.numero || '');
                    const txt = document.createElement('div');
                    txt.className = 'whitespace-pre-wrap';
                    txt.textContent = fb.texto;
                    div.appendChild(meta); div.appendChild(txt);
                    body.appendChild(div);
                });
            });
        }

        function createCard(d) {
            const style = getPriorityStyle(d.Prioridade);
            let actionBtn = '';
            
            if (d.ia_status === 'backlog') {
                actionBtn = `<button onclick="ativar('${d.ID}')" class="mt-3 w-full bg-white hover:bg-blue-50 text-blue-600 border border-blue-200 font-medium py-1.5 px-3 rounded text-sm transition-colors flex items-center justify-center gap-2"><i class="fa-solid fa-play text-xs"></i> Enviar p/ IA</button>`;
            } else if (d.ia_status === 'pendente') {
                actionBtn = `<div class="mt-3 w-full bg-blue-100 text-blue-700 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-hourglass-half"></i> Aguardando Código</div>`;
            } else if (d.ia_status === 'em_teste') {
                const aprovado = (d.Status || '').trim().toLowerCase() === 'aprovado';
                actionBtn = aprovado
                    ? `<div class="mt-3 w-full bg-amber-100 text-amber-800 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-arrow-up-from-bracket"></i> Aprovado, falta promover</div>`
                    : `<div class="mt-3 w-full bg-violet-100 text-violet-700 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-flask"></i> Em teste no dev${d.Versão ? ' · worker ' + d.Versão : ''}</div>`;
            } else if (d.ia_status === 'concluido') {
                const rotulo = d.historico ? 'Aprovado (histórico)' : ('Em produção' + (d.versao_producao ? ' · ' + d.versao_producao : ''));
                actionBtn = `<div class="mt-3 w-full bg-emerald-100 text-emerald-700 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-check"></i> ${rotulo}</div>`;
            } else {
                actionBtn = `<div class="mt-3 w-full bg-slate-100 text-slate-600 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-pause"></i> ${(d.ia_status || '').toUpperCase()}</div>`;
            }

            // Tratamento de quebras de linha e nulos para UX
            const desc = d.Descrição || 'Sem descrição';
            const descPreview = desc.length > 100 ? desc.substring(0, 100) + '...' : desc;
            const title = d.Título || 'Sem título';
            const modulo = d.Módulo || '-';

            return `
                <div class="task-card bg-white p-4 rounded-lg shadow-sm border border-slate-200 ${style.border}">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs font-bold text-slate-500 cursor-pointer hover:text-blue-600 transition-colors" onclick="openModal('${d.ID}')">#${d.ID} <i class="fa-solid fa-up-right-from-square text-[10px] ml-0.5"></i></span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${style.color}">${style.icon} ${d.Prioridade ? d.Prioridade.toUpperCase() : ''}</span>
                    </div>
                    <h3 class="font-semibold text-slate-800 text-sm mb-1 leading-snug cursor-pointer hover:text-blue-600 transition-colors" onclick="openModal('${d.ID}')">${title}</h3>
                    <div class="text-xs text-slate-500 mb-2 font-medium bg-slate-50 inline-block px-1.5 py-0.5 rounded"><i class="fa-solid fa-cube mr-1"></i>${modulo}</div>
                    <p class="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2 rounded border border-slate-100 cursor-pointer" title="Clique para ver mais" onclick="openModal('${d.ID}')">${descPreview.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
                    ${actionBtn}
                    ${(waState.connected && d.ia_status === 'em_teste') ? `<button onclick="openNotify('${d.ID}', 'teste')" class="mt-2 w-full bg-white hover:bg-violet-50 text-violet-700 border border-violet-200 font-medium py-1.5 px-3 rounded text-sm transition-colors flex items-center justify-center gap-2"><i class="fa-brands fa-whatsapp"></i> Notificar QA</button>` : ''}
                    ${(waState.connected && d.ia_status === 'standby') ? `<button onclick="openNotify('${d.ID}', 'standby')" class="mt-2 w-full bg-white hover:bg-amber-50 text-amber-700 border border-amber-200 font-medium py-1.5 px-3 rounded text-sm transition-colors flex items-center justify-center gap-2"><i class="fa-brands fa-whatsapp"></i> Cobrar alinhamento</button>` : ''}
                    ${(waState.connected && d.ia_status === 'concluido' && !d.historico) ? `<button onclick="openNotify('${d.ID}', 'producao')" class="mt-2 w-full bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium py-1.5 px-3 rounded text-sm transition-colors flex items-center justify-center gap-2"><i class="fa-brands fa-whatsapp"></i> Avisar produção</button>` : ''}
                </div>
            `;
        }

        function renderBoard() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const prioFilter = document.getElementById('prioFilter').value.toLowerCase();

            const filtered = allDemands.filter(d => {
                const titleStr = (d.Título || '').toLowerCase();
                const idStr = (d.ID || '').toString();
                const matchSearch = titleStr.includes(search) || idStr.includes(search);
                const matchPrio = prioFilter === '' || (d.Prioridade || '').toLowerCase() === prioFilter;
                return matchSearch && matchPrio;
            });

            const backlog = filtered.filter(d => d.ia_status === 'backlog');
            const pending = filtered.filter(d => d.ia_status === 'pendente');
            const standby = filtered.filter(d => d.ia_status === 'standby');
            const teste = filtered.filter(d => d.ia_status === 'em_teste');
            const done = filtered.filter(d => d.ia_status === 'concluido');

            document.getElementById('col-backlog').innerHTML = backlog.map(createCard).join('');
            document.getElementById('col-ia').innerHTML = pending.map(createCard).join('');
            document.getElementById('col-standby').innerHTML = standby.map(createCard).join('');
            document.getElementById('col-teste').innerHTML = teste.map(createCard).join('');
            document.getElementById('col-done').innerHTML = done.map(createCard).join('');

            document.getElementById('count-backlog').innerText = backlog.length;
            document.getElementById('count-ia').innerText = pending.length;
            document.getElementById('count-standby').innerText = standby.length;
            document.getElementById('count-teste').innerText = teste.length;
            document.getElementById('count-done').innerText = done.length;
        }

        async function ativar(id) {
            const d = allDemands.find(x => x.ID === id);
            if(!d) return;
            
            document.getElementById('loader').style.display = 'flex';
            try {
                await fetch('/api/ativar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: d.ID, titulo: d.Título, modulo: d.Módulo, descricao: d.Descrição})
                });
                await fetchDemands(); // Recarrega
            } catch(e) {
                alert('Erro ao ativar demanda.');
            }
        }

        // Listeners para filtros
        document.getElementById('searchInput').addEventListener('input', renderBoard);
        document.getElementById('prioFilter').addEventListener('change', renderBoard);

        // Modo noturno (preferência guardada só neste navegador)
        function applyTheme(dark) {
            document.documentElement.classList.toggle('dark', dark);
            const ic = document.getElementById('themeIcon');
            if (ic) ic.className = dark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
        function toggleTheme() {
            const dark = !document.documentElement.classList.contains('dark');
            applyTheme(dark);
            try { localStorage.setItem('painelTema', dark ? 'dark' : 'light'); } catch (e) { /* sem armazenamento */ }
        }
        (function () {
            let pref = null;
            try { pref = localStorage.getItem('painelTema'); } catch (e) { /* sem armazenamento */ }
            applyTheme(pref ? pref === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches);
        })();

        // Inicializa
        fetchDemands().then(loadFonte);
        setInterval(silentRefresh, 60000);
        loadWa();
        setInterval(() => { if (!waPoll) loadWa(); }, 15000);

        async function takeSnapshot() {
            const modal = document.getElementById('taskModalContent');
            const scrollArea = modal.querySelector('.overflow-y-auto');
            const btn = event.currentTarget;
            const originalIcon = btn.innerHTML;
            
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Gerando...';
            
            // Salva estilos originais
            const originalHeight = modal.style.height;
            const originalOverflow = modal.style.overflow;
            const origScrollOverflow = scrollArea.style.overflow;
            const origScrollHeight = scrollArea.style.maxHeight;
            
            // Prepara para tirar foto inteira (expande)
            modal.style.height = 'auto';
            modal.style.overflow = 'visible';
            scrollArea.style.overflow = 'visible';
            scrollArea.style.maxHeight = 'none';
            
            try {
                const canvas = await html2canvas(modal, {
                    scale: 2, // Maior resolução
                    backgroundColor: '#ffffff',
                    windowWidth: modal.scrollWidth,
                    windowHeight: modal.scrollHeight
                });
                
                const imgData = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                // Nome do arquivo amigável
                const safeName = document.getElementById('modalTitle').innerText.replace(/[^a-z0-9]/gi, '_').toLowerCase();
                link.download = `demanda_${safeName}.png`;
                link.href = imgData;
                link.click();
            } catch(e) {
                console.error(e);
                alert('Erro ao gerar imagem da demanda.');
            } finally {
                // Restaura interface
                modal.style.height = originalHeight;
                modal.style.overflow = originalOverflow;
                scrollArea.style.overflow = origScrollOverflow;
                scrollArea.style.maxHeight = origScrollHeight;
                btn.innerHTML = originalIcon;
            }
        }
    </script>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def _send(self, code, payload, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header('Content-type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload if isinstance(payload, bytes) else json.dumps(payload).encode('utf-8'))

    def do_GET(self):
        from urllib.parse import urlparse
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/wa/'):
            sub = parsed.path[len('/api/wa'):]
            if sub not in ('/status', '/qr.png', '/groups', '/feedback', '/participants'):
                return self._send(404, {"error": "rota inválida"})
            code, body, ctype = wa_call('GET', sub + ('?' + parsed.query if parsed.query else ''))
            if sub == '/status' and code == 200:
                st = json.loads(body); st['running'] = True; body = json.dumps(st).encode('utf-8')
            return self._send(code, body, ctype)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(html_template.encode('utf-8'))
        elif self.path == '/api/fonte':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            info = {"fonte": FONTE, "intervalo": SYNC_INTERVAL, "ultima": _sync["ultima"], "erro": _sync["erro"]}
            self.wfile.write(json.dumps(info).encode('utf-8'))
        elif self.path == '/api/demandas':
            # Ler status reais baseados nos arquivos criados na pasta exec
            exec_status = {}
            if os.path.exists(EXEC_DIR):
                for file in glob.glob(f"{EXEC_DIR}/DEM-*.md"):
                    basename = os.path.basename(file).replace('DEM-', '').replace('.md', '')
                    with open(file, 'r', encoding='utf-8') as mf:
                        content = mf.read()
                    fm = ler_frontmatter(content)
                    exec_status[basename] = {
                        'status': fm.get('status') or 'pendente',
                        'versao_producao': fm.get('versao_producao', ''),
                        'data_producao': fm.get('data_producao', ''),
                        'versao_worker': fm.get('versao_worker', ''),
                        'aguardando': fm.get('aguardando', ''),
                        'pendencia': fm.get('pendencia', ''),
                        'data_standby': fm.get('data_standby', '') or fm.get('data_ativacao', ''),
                        'md_content': content
                    }

            STANDBY_DIR = "csv/standby.solution"
            if os.path.exists(STANDBY_DIR):
                for file in glob.glob(f"{STANDBY_DIR}/DEM-*.md"):
                    basename = os.path.basename(file).replace('DEM-', '').replace('.md', '')
                    with open(file, 'r', encoding='utf-8') as mf:
                        content = mf.read()
                    fm = ler_frontmatter(content)
                    exec_status[basename] = {
                        'status': fm.get('status') or 'standby',
                        'versao_producao': fm.get('versao_producao', ''),
                        'data_producao': fm.get('data_producao', ''),
                        'versao_worker': fm.get('versao_worker', ''),
                        'aguardando': fm.get('aguardando', ''),
                        'pendencia': fm.get('pendencia', ''),
                        'data_standby': fm.get('data_standby', '') or fm.get('data_ativacao', ''),
                        'md_content': content
                    }

            demandas = []
            if os.path.exists(CSV_PATH):
                with open(CSV_PATH, 'r', encoding='utf-8') as f:
                    for row in csv.DictReader(f):
                        # Linhas pré-numeradas da planilha (só ID, sem título) não são tasks.
                        if not (row.get('ID') or '').strip() or not (row.get('Título') or '').strip():
                            continue
                        status_csv = row.get('Status', '').lower()
                        
                        # Definir a coluna correta (ia_status)
                        ia_status = 'backlog'
                        if row.get('ID') in exec_status:
                            info = exec_status[row.get('ID')]
                            ia_status = info['status'].lower()
                            row['md_content'] = info['md_content']
                            row['versao_producao'] = info['versao_producao']
                            row['data_producao'] = info['data_producao']
                            row['versao_worker'] = info['versao_worker']
                            row['aguardando'] = info['aguardando']
                            row['pendencia'] = info['pendencia']
                            row['data_standby'] = info['data_standby']
                        else:
                            # Ignorar as reprovadas no CSV original que não foram pra IA
                            if status_csv == 'reprovado':
                                continue
                            # "Concluído" na planilha sem arquivo = entregue no dev, em teste pelo QA.
                            # Só vai para Concluídas (produção) quando o arquivo recebe status: concluido.
                            if status_csv in ['concluído', 'concluido']:
                                ia_status = 'em_teste'
                            # Aprovadas antes do Kanban, sem arquivo: histórico, tratadas como em produção.
                            elif status_csv == 'aprovado':
                                ia_status = 'concluido'
                                row['historico'] = '1'
                                
                        row['ia_status'] = ia_status
                        demandas.append(row)
            
            # Sort inicial: Pendentes primeiro, depois altas, medias, baixas
            prio_map = {'alta': 3, 'média': 2, 'media': 2}
            demandas.sort(key=lambda x: (
                1 if x['ia_status'] == 'pendente' else 0,
                prio_map.get(x.get('Prioridade', '').strip().lower(), 1)
            ), reverse=True)

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(demandas).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/wa/'):
            sub = self.path[len('/api/wa'):]
            if sub not in ('/pair', '/logout', '/group', '/send'):
                return self._send(404, {"error": "rota inválida"})
            length = int(self.headers.get('Content-Length', 0) or 0)
            body = json.loads(self.rfile.read(length) or b'{}')
            if sub == '/send':
                task_id = str(body.get('id', '')).strip()
                texto = body.get('text', '')
                payload = {"text": texto}
                mentions = [str(m) for m in (body.get('mentions') or []) if str(m).strip()]
                if mentions:
                    payload["mentions"] = mentions
                code, resp, ctype = wa_call('POST', '/send', payload)
                if code == 200 and task_id:
                    registrar_notificacao(task_id, texto, body.get('tipo', 'teste'))
                return self._send(code, resp, ctype)
            code, resp, ctype = wa_call('POST', sub, body)
            return self._send(code, resp, ctype)
        if self.path == '/api/ativar':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            
            md_content = f"""---
id: DEM-{body['id']}
status: pendente
data_ativacao: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
modulo: {body['modulo']}
---

# 🚀 Histórico de Execução: {body['titulo']}

## 📌 Resumo do Problema
{body.get('descricao', 'Sem descrição fornecida.')}

## 🛠️ Solução Adotada
(IA preencherá este campo após autorização)

## 📂 Arquivos Modificados
- (A preencher)
"""
            os.makedirs(EXEC_DIR, exist_ok=True)
            with open(f"{EXEC_DIR}/DEM-{body['id']}.md", 'w', encoding='utf-8') as f:
                f.write(md_content)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            
        elif self.path == '/api/nova-demanda':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            if FONTE == "planilha":
                self.send_response(409)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                msg = "Modo planilha: cadastre a task na planilha Google; ela aparece aqui na próxima sincronização."
                self.wfile.write(json.dumps({"success": False, "error": msg}).encode('utf-8'))
                return

            next_id = 1
            rows = []
            headers = ["ID","Tipo","Título","Descrição","Módulo","Prioridade","Status","Responsável","Data de Criação","Versão","Observações","Testado Em"]
            
            if os.path.exists(CSV_PATH):
                with open(CSV_PATH, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        # Mantém as colunas do arquivo (antes "Testado Em" era descartada ao regravar).
                        headers = list(reader.fieldnames)
                    for r in reader:
                        rows.append(r)
                        try:
                            cid = int(r.get('ID', 0))
                            if cid >= next_id:
                                next_id = cid + 1
                        except:
                            pass
                            
            new_row = {
                "ID": str(next_id),
                "Tipo": body.get("Tipo", ""),
                "Título": body.get("Título", ""),
                "Descrição": body.get("Descrição", ""),
                "Módulo": body.get("Módulo", ""),
                "Prioridade": body.get("Prioridade", ""),
                "Status": "A Fazer",
                "Responsável": body.get("Responsável", ""),
                "Data de Criação": datetime.now().strftime('%d/%m/%Y'),
                "Versão": body.get("Versão", ""),
                "Observações": body.get("Observações", "")
            }
            rows.append(new_row)
            
            with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for r in rows:
                    clean_row = {h: r.get(h, '') for h in headers}
                    writer.writerow(clean_row)
                    
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "id": next_id}).encode('utf-8'))

_args = argparse.ArgumentParser(description="Painel local de demandas")
_args.add_argument("--fonte", choices=["csv", "planilha"], default="csv",
                   help="csv (padrão) ou planilha (sincroniza da planilha Google a cada 60 s)")
FONTE = _args.parse_args().fonte

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Servidor web KANBAN iniciado! Fonte do backlog: {FONTE}")
print(f"Acesse: http://localhost:{PORT} no seu navegador.")
if FONTE == "planilha":
    threading.Thread(target=sync_loop, daemon=True).start()
    print(f"Sincronizando com a planilha a cada {SYNC_INTERVAL} s (em segundo plano).")
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer.daemon_threads = True
socketserver.ThreadingTCPServer(("", PORT), Handler).serve_forever()
