import http.server
import socketserver
import csv
import json
import os
import glob
from datetime import datetime

PORT = 8090
CSV_PATH = "csv/10092026.csv"
EXEC_DIR = "csv/exec"

# Configurar para reaproveitar a porta se o servidor for reiniciado rapidamente
socketserver.TCPServer.allow_reuse_address = True

html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UzAPI - Kanban de Demandas IA</title>
    <script src="https://cdn.tailwindcss.com"></script>
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
        
        /* Loading Overlay */
        #loader { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); z-index: 50; justify-content: center; align-items: center; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3b82f6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="text-slate-800 h-screen flex flex-col">

    <div id="loader"><div class="spinner"></div></div>

    <!-- Header & Filters -->
    <header class="bg-white shadow-sm border-b border-slate-200 z-10 sticky top-0">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <div class="bg-blue-600 text-white p-2 rounded-lg"><i class="fa-solid fa-robot"></i></div>
                    <div>
                        <h1 class="text-xl font-bold text-slate-900 leading-tight">UzAPI Demandas</h1>
                        <p class="text-xs text-slate-500">Gestão Integrada Homem + Inteligência Artificial</p>
                    </div>
                </div>

                <!-- Dynamic Filters -->
                <div class="flex flex-wrap items-center gap-3">
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
                    <h2 class="font-semibold text-slate-700 flex items-center gap-2"><i class="fa-solid fa-inbox text-slate-400"></i> Backlog (CSV)</h2>
                    <span id="count-backlog" class="bg-slate-200 text-slate-600 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-backlog" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

            <!-- Col 2: Fila da IA -->
            <div class="bg-blue-50 rounded-xl w-96 flex flex-col max-h-[85vh] border border-blue-100 shadow-sm">
                <div class="p-4 border-b border-blue-100 bg-blue-100/30 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-blue-800 flex items-center gap-2"><i class="fa-solid fa-microchip text-blue-500"></i> Fila da IA (Pendente)</h2>
                    <span id="count-ia" class="bg-blue-200 text-blue-800 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-ia" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

            <!-- Col 3: Concluídas -->
            <div class="bg-emerald-50 rounded-xl w-96 flex flex-col max-h-[85vh] border border-emerald-100 shadow-sm">
                <div class="p-4 border-b border-emerald-100 bg-emerald-100/30 rounded-t-xl flex justify-between items-center">
                    <h2 class="font-semibold text-emerald-800 flex items-center gap-2"><i class="fa-solid fa-check-circle text-emerald-500"></i> Solucionadas</h2>
                    <span id="count-done" class="bg-emerald-200 text-emerald-800 text-xs font-bold px-2 py-1 rounded-full">0</span>
                </div>
                <div id="col-done" class="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 kanban-col"></div>
            </div>

        </div>
    </main>

    <script>
        let allDemands = [];

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

        function createCard(d) {
            const style = getPriorityStyle(d.Prioridade);
            let actionBtn = '';
            
            if (d.ia_status === 'backlog') {
                actionBtn = `<button onclick="ativar('${d.ID}')" class="mt-3 w-full bg-white hover:bg-blue-50 text-blue-600 border border-blue-200 font-medium py-1.5 px-3 rounded text-sm transition-colors flex items-center justify-center gap-2"><i class="fa-solid fa-play text-xs"></i> Enviar p/ IA</button>`;
            } else if (d.ia_status === 'pendente') {
                actionBtn = `<div class="mt-3 w-full bg-blue-100 text-blue-700 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-hourglass-half"></i> Aguardando Código</div>`;
            } else {
                actionBtn = `<div class="mt-3 w-full bg-emerald-100 text-emerald-700 font-medium py-1.5 px-3 rounded text-sm flex items-center justify-center gap-2"><i class="fa-solid fa-check"></i> Executado</div>`;
            }

            // Tratamento de quebras de linha para UX
            const descPreview = d.Descrição.length > 100 ? d.Descrição.substring(0, 100) + '...' : d.Descrição;

            return `
                <div class="task-card bg-white p-4 rounded-lg shadow-sm border border-slate-200 ${style.border}">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs font-bold text-slate-500">#${d.ID}</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${style.color}">${style.icon} ${d.Prioridade.toUpperCase()}</span>
                    </div>
                    <h3 class="font-semibold text-slate-800 text-sm mb-1 leading-snug">${d.Título}</h3>
                    <div class="text-xs text-slate-500 mb-2 font-medium bg-slate-50 inline-block px-1.5 py-0.5 rounded"><i class="fa-solid fa-cube mr-1"></i>${d.Módulo}</div>
                    <p class="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2 rounded border border-slate-100" title="${d.Descrição.replace(/"/g, '&quot;')}">${descPreview}</p>
                    ${actionBtn}
                </div>
            `;
        }

        function renderBoard() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const prioFilter = document.getElementById('prioFilter').value.toLowerCase();

            const filtered = allDemands.filter(d => {
                const matchSearch = d.Título.toLowerCase().includes(search) || d.ID.toString().includes(search);
                const matchPrio = prioFilter === '' || (d.Prioridade || '').toLowerCase() === prioFilter;
                return matchSearch && matchPrio;
            });

            const backlog = filtered.filter(d => d.ia_status === 'backlog');
            const pending = filtered.filter(d => d.ia_status === 'pendente');
            const done = filtered.filter(d => d.ia_status === 'concluido');

            document.getElementById('col-backlog').innerHTML = backlog.map(createCard).join('');
            document.getElementById('col-ia').innerHTML = pending.map(createCard).join('');
            document.getElementById('col-done').innerHTML = done.map(createCard).join('');

            document.getElementById('count-backlog').innerText = backlog.length;
            document.getElementById('count-ia').innerText = pending.length;
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
                    body: JSON.stringify({id: d.ID, titulo: d.Título, modulo: d.Módulo})
                });
                await fetchDemands(); // Recarrega
            } catch(e) {
                alert('Erro ao ativar demanda.');
            }
        }

        // Listeners para filtros
        document.getElementById('searchInput').addEventListener('input', renderBoard);
        document.getElementById('prioFilter').addEventListener('change', renderBoard);

        // Inicializa
        fetchDemands();
    </script>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_template.encode('utf-8'))
        elif self.path == '/api/demandas':
            # Ler status reais baseados nos arquivos criados na pasta exec
            exec_status = {}
            if os.path.exists(EXEC_DIR):
                for file in glob.glob(f"{EXEC_DIR}/DEM-*.md"):
                    basename = os.path.basename(file).replace('DEM-', '').replace('.md', '')
                    # Ler o arquivo para descobrir o status real (pendente ou concluido)
                    status_local = 'pendente'
                    with open(file, 'r', encoding='utf-8') as mf:
                        for line in mf.readlines():
                            if line.startswith('status:'):
                                status_local = line.split('status:')[1].strip()
                                break
                    exec_status[basename] = status_local

            demandas = []
            if os.path.exists(CSV_PATH):
                with open(CSV_PATH, 'r', encoding='utf-8') as f:
                    for row in csv.DictReader(f):
                        status_csv = row.get('Status', '').lower()
                        
                        # Definir a coluna correta (ia_status)
                        ia_status = 'backlog'
                        if row.get('ID') in exec_status:
                            ia_status = exec_status[row.get('ID')].lower()
                        else:
                            # Ignorar as reprovadas no CSV original que não foram pra IA
                            if status_csv in ['reprovado', 'concluído', 'concluido']:
                                continue
                                
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
(Aguardando IA ler a demanda)

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

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Servidor web KANBAN iniciado!")
print(f"Acesse: http://localhost:{PORT} no seu navegador.")
socketserver.TCPServer.allow_reuse_address = True
socketserver.TCPServer(("", PORT), Handler).serve_forever()
