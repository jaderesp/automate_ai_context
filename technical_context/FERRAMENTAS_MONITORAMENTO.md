# 🛠️ Ferramentas de Monitoramento e Gerenciamento

Para facilitar o desenvolvimento, testes e resolução de problemas (troubleshooting) do projeto **UzAPI**, utilizamos diversas interfaces visuais e ferramentas de gerenciamento. 

Abaixo está o guia rápido de como acessar e utilizar cada painel ou ferramenta associada às tecnologias do projeto.

---

## 🚢 Kubernetes (Cluster & Pods)

O Kubernetes é o coração da infraestrutura. Para inspecionar Pods, ver logs em tempo real e gerenciar recursos (como os workers de WhatsApp instanciados dinamicamente), recomendamos:

### 🔍 **[Lens Desktop](https://k8slens.dev/)** (Recomendado)
A IDE visual mais poderosa para Kubernetes.
- **Como conectar**:
  1. Instale o Lens no seu computador local.
  2. Adicione o seu arquivo `KUBECONFIG` (o mesmo usado na VPS com MicroK8s ou gerado localmente).
  3. Navegue visualmente pelos `Namespaces`, veja logs dos Pods do `worker-go` ou reinicie `Deployments` com 1 clique.

### 💻 **[K9s](https://k9scli.io/)** (Alternativa via Terminal)
Dashboard leve executado diretamente no terminal.
- **Como usar**: Basta instalar e rodar `k9s` no terminal. Ideal para checagens rápidas via SSH na VPS sem precisar de interface gráfica pesada.

---

## 🐙 ArgoCD (GitOps & Deployments)

O [ArgoCD](https://argo-cd.readthedocs.io/en/stable/) orquestra a aplicação dos arquivos do repositório `infra-gitops` dentro do Kubernetes.

- **Acesso**: Painel acessível pelo Ingress (ex: `https://argocd.uzapi.com.br` ou via port-forward).
- **O que fazer lá**:
  - 🔄 **Sincronizar aplicações** manualmente (Sync), caso necessário.
  - 👀 **Visualizar a árvore** de dependências de cada microserviço e conferir as *Sync Waves*.
  - 🛑 **Verificar alertas** de desincronização e logs de deploy do K8s.

---

## 🐇 RabbitMQ (Mensageria e Filas)

A troca de mensagens entre a `api-service` e o `worker-go` é feita pelo RabbitMQ. O painel é excelente para inspecionar os fluxos de forma visual.

- **Acesso**: Porta `15672` (Ex: `http://localhost:15672` ou via Admin Ingress).
- **O que fazer lá**:
  - 📊 **Monitorar as filas**: Ver se as filas dos workers (geralmente nomeadas pelo ID da instância) estão acumulando muitas mensagens.
  - 🗑️ **Purgar (Limpar) mensagens**: Muito útil durante desenvolvimento quando mensagens de teste ficam presas.
  - ⏱️ **Plugins**: Checar funcionamento do `x-delayed-message` se houver agendamentos.

---

## 🗄️ Bancos de Dados (PostgreSQL, MongoDB, Redis)

Gerenciar banco de dados apenas pelo ORM ou CLI pode ser limitante no dia a dia. Seguem as recomendações de interfaces visuais:

### 🐘 **PostgreSQL (Database Principal)**
- **Ferramentas sugeridas**: [DBeaver](https://dbeaver.io/), [TablePlus](https://tableplus.com/) ou [pgAdmin](https://www.pgadmin.org/).
- **Para que serve no projeto**: Inspecionar os registros do Manager (usuários, sessões, pagamentos) e a tabela unificada de `public.instances` (ver o status das conexões do whatsapp em tempo real).

### 🍃 **MongoDB (Logs e Dados Flexíveis)**
- **Ferramentas sugeridas**: [MongoDB Compass](https://www.mongodb.com/products/compass) ou DBeaver.
- **Para que serve no projeto**: Usado principalmente pelo `api-service` para salvar logs de integrações, métricas e dados de requisições de forma estruturada, porém flexível.

### 🟥 **Redis (Cache e Rate Limiting)**
- **Ferramentas sugeridas**: [RedisInsight](https://redis.com/redis-enterprise/redis-insight/) ou [Another Redis Desktop Manager](https://github.com/qishibo/AnotherRedisDesktopManager).
- **Para que serve no projeto**: Checar chaves e TTL de proteção contra Rate Limit da API e cache de tokens.

---

## 🌐 Gerenciamento de Rede Local e Webhooks

### 🔀 **[Ngrok](https://ngrok.com/) / [Localtunnel](https://theboroer.github.io/localtunnel-www/)**
Durante o desenvolvimento local de Webhooks, os serviços externos (como Asaas ou notificações de instâncias) precisam acessar o seu `localhost`.
- **Uso**: Crie um túnel reverso e aponte os endpoints nas configurações locais da aplicação para escutar retornos de pagamento, por exemplo.

### 📝 **Arquivo Hosts (`/etc/hosts`)**
Útil para testar os domínios do K8s ou do seu ambiente Docker na sua máquina (ex: apontar `api.uzapi.local` para `127.0.0.1`).
