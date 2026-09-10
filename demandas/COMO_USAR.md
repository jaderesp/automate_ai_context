# 📖 Manual de Gestão de Demandas (Homem + IA)

Bem-vindo ao centro de operações onde você e a Inteligência Artificial coordenam o que deve ser programado no projeto **UzAPI**. 

Esta pasta (`ai.context/demandas/`) foi desenhada com um objetivo claro: **terceirizar a leitura do Backlog para a IA, mantendo o Desenvolvedor no controle total da aprovação técnica.**

---

## ⚙️ Como funciona a engrenagem?

Toda a dinâmica gira em torno de três peças principais:
1. 🗃️ **O Arquivo CSV:** A origem dos dados (Backlog).
2. 🎛️ **O Painel Local (HTML):** Onde você escolhe visualmente qual tarefa iniciar.
3. 📂 **A Pasta `exec/`:** A memória histórica do projeto (usada pela IA para ler e registrar o que já foi codificado e o que está pendente).

---

## 🚀 Passo a Passo (O Fluxo de Trabalho)

### Passo 1: Atualizar o Backlog 📥
Quando houver novas tarefas ou a lista mudar, basta exportar do seu sistema de gestão (Jira, Trello, Planilha) e largar o arquivo **`.csv`** (ex: `10092026.csv`) dentro da pasta:
👉 `ai.context/demandas/csv/`

### Passo 2: Iniciar a Interface Visual (Painel Local) 💻
Para não precisar ler linha por linha do CSV manualmente, utilize o servidor embutido. No terminal do projeto, rode o comando:
```bash
python3 ai.context/demandas/painel_local.py
```
Acesse o endereço exibido (geralmente **http://localhost:8090**) no seu navegador. Lá você verá o seu Backlog lindamente organizado com base nas regras da empresa (`Prioridade Alta` -> `Média` -> `Baixa`).

### Passo 3: Ativar uma Demanda ⚡
No navegador, clique no botão **"Ativar Demanda para a IA"** na tarefa que você quer resolver no dia. 
- *O que acontece por trás dos panos?* O sistema irá criar automaticamente um arquivo Markdown (Ex: `DEM-1.md`) dentro da pasta `csv/exec/` com o metadado `status: pendente`.

### Passo 4: Acionar o Agente de Inteligência Artificial 🤖
Volte para o seu chat de IA (VSCode/IDE) e dê o comando de início. Exemplo:
> *"Pode atuar nas demandas pendentes"*

- **O Agente vai:** Varrer a pasta `csv/exec/` buscando o status `pendente`.
- **O Agente vai:** Levantar o impacto nos módulos do sistema (ex: Banco de Dados, Backend, Filas).
- **O Agente vai:** Propor opções (A ou B) e pedir a sua **Autorização**.

### Passo 5: Execução e Conclusão ✅
Após você autorizar, o agente mergulha no código, edita os arquivos e commita (ou entrega pronto para você testar). 
Por fim, o próprio agente altera o arquivo `DEM-1.md` de `status: pendente` para `status: concluido`, salvando a lista de arquivos afetados.

---

## 🎯 Por que isso é incrível? (A Magia da Economia de Tokens)
No futuro, se a IA precisar alterar o "Login" novamente, ela não precisará reler todo o código para saber o que já foi feito. Ela dará uma lida rápida na pasta `exec/` (que é extremamente leve) para puxar todo o histórico de manutenções! 🧠⚡
