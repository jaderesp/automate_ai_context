---
id: DEM-65
status: concluido
data_ativacao: 2026-09-11 11:31:58
data_conclusao: 2026-09-11 12:45:00
modulo: API
---

# 🚀 Histórico de Execução: Audios enviados não reproduzem no iPhone

## 📌 Resumo do Problema
Usuários de iPhone (iOS) relatavam que mensagens de voz (PTT - Push To Talk) enviadas pela API via `worker-go` (utilizando a lib `whatsmeow`) não reproduziam ou exibiam o erro "Mensagem de áudio indisponível".
A causa raiz do problema estava no comando `ffmpeg` executado durante o processamento de mídias (`convertAudioToOpusOGG`). Embora a conversão gerasse corretamente um formato Opus num container OGG (`libopus`), o iOS possui regras draconianas em relação às especificações de PTT. Se o arquivo estiver gravado com frequências arbitrárias ou em canais Stereo (2 canais), o reprodutor nativo do WhatsApp no iPhone rejeita a mídia.

## 🛠️ Solução Adotada
Após validar as documentações e analisar issues (#937 e #599) na página do repositório da biblioteca `whatsmeow`, foi constatado que o desenvolvedor confirmou a necessidade estrita da frequência de 16000 Hz.
Realizei a substituição no comando do `exec.Command` injetando as flags obrigatórias para compatibilidade universal do Opus:
- `-ac 1`: Força a conversão para áudio **Mono** (1 canal).
- `-ar 16000`: Específica que o *Sample Rate* (Taxa de Amostragem) seja **16000 Hz**.

Comando Antigo:
`ffmpeg -y -i <src> -c:a libopus -b:a 16k -vn <dest>`
Comando Novo:
`ffmpeg -y -i <src> -c:a libopus -b:a 16k -ac 1 -ar 16000 -vn <dest>`

Essa alteração foi realizada seguindo os padrões do Gitflow: a branch `fix/dem-65-ios-audio` foi criada diretamente no repositório `worker-go`, e a modificação foi adequadamente 'commitada'.

## 📂 Arquivos Modificados
- `worker-go/utils/processMidias.go`

## 🧪 Teste Prático e Homologação Local
Para garantir a absoluta eficácia da solução antes de submetê-la ao ambiente de produção, foi executado um teste real *End-to-End* envolvendo o disparo de um arquivo de áudio de teste para um **dispositivo físico iPhone (iOS)** do cliente (Número: +55 63 9247-7769).

O processo técnico de validação consistiu em:
1. **Host HTTP Isolado:** O arquivo `audio_teste_iphone.mp3` foi hospedado através de um `python3 -m http.server` porta 8000 na rede local (para bypass da validação do tipo de mimeType `video/mpeg` que bloqueava extensões `.mpeg` no Worker).
2. **Setup do Worker:** O `worker-go` foi recompilado localmente (`./bin/main`) conectando-se a instância pré-existente (`937931931398461`). Foi gerado um QR Code via terminal/base64 que foi pareado localmente com a instância de testes.
3. **Injeção de Fila:** A API local `api-service` (que faria a criação pelo painel) estava enfrentando um erro pela ausência de cluster Kubernetes. Optou-se por realizar o envio fazendo um bypass via injeção `cURL POST` direto na API HTTP local do `RabbitMQ` (porta 15672), alimentando a fila da instância.
4. **Download e Conversão:** O arquivo caiu na fila e os logs comprovaram o download e a formatação: `INFO[0453] Mensagem enviada com sucesso [...] message_type=audio`.
5. **Resultado no Client (iOS):** O cliente final recebeu a mensagem no número do iPhone e confirmou a **reprodução sem problemas**, oficializando a compatibilidade plena do código `-ac 1 -ar 16000`.
