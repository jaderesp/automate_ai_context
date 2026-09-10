# UzAPI - Visão Geral do Projeto

Este documento destina-se a fornecer o contexto geral do projeto UzAPI, ajudando desenvolvedores e gestores a compreenderem como a plataforma é estruturada, orquestrada e como seus componentes interagem.

## 🗂️ Menu de Navegação da Documentação

Para acessar os detalhes específicos de cada camada do projeto, utilize os links abaixo:

### Estrutura e Regras
- [Arquitetura e Fluxo do Sistema](../architecture/ARQUITETURA.md)
- [Regras de Negócio e Lifecycle](../business_rules/REGRAS_NEGOCIO.md)

### Contexto Técnico por Serviço
- [Manager Service (Next.js)](../technical_context/MANAGER_SERVICE.md)
- [API Service (NestJS)](../technical_context/API_SERVICE.md)
- [Worker Go (Golang)](../technical_context/WORKER_GO.md)
- [Infra GitOps (K8s & ArgoCD)](../technical_context/INFRA_GITOPS.md)

### Ferramentas de Apoio
- [Ferramentas de Monitoramento e Gerenciamento](../technical_context/FERRAMENTAS_MONITORAMENTO.md)

---
## O Que É O Projeto?

UzAPI é uma plataforma SaaS/Enterprise para gerenciamento e orquestração de instâncias do WhatsApp. O projeto oferece tanto um painel administrativo (Manager) quanto uma API robusta e instâncias isoladas de workers para garantir a conexão e o processamento de mensagens em tempo real através do WhatsApp (utilizando a biblioteca `whatsmeow` customizada).

## Os 4 Pilares do Projeto

O projeto é dividido em 4 repositórios/partes principais:

1. **Manager Service (`manager-service`)**:
   - **Papel**: Atua como o Frontend (Painel/Dashboard), API de Gerenciamento e orquestrador.
   - **Stack**: Next.js 16 (App Router), React 19, Drizzle ORM, PostgreSQL, Better Auth, Tailwind CSS, Shadcn UI.
   - **Responsabilidades**: Gerenciar cadastros, logins, sessões, cobranças (Asaas), instâncias de clientes. É este serviço que interage dinamicamente com a API do Kubernetes para criar os Pods individuais de cada instância do WhatsApp.

2. **API Service (`api-service`)**:
   - **Papel**: API Core e Gateway de comunicação.
   - **Stack**: NestJS, PostgreSQL, MongoDB, Redis, RabbitMQ.
   - **Responsabilidades**: Receber chamadas de clientes (integrações), processar lógicas de API gerais e orquestrar mensageria enviando eventos e comandos via RabbitMQ para os workers. 

3. **Worker Go (`worker-go`)**:
   - **Papel**: O motor de conexão com o WhatsApp.
   - **Stack**: Golang (1.25+), SQLite, PostgreSQL, RabbitMQ, whatsmeow (fork customizado).
   - **Responsabilidades**: Cada pod deste serviço roda **uma única instância/sessão do WhatsApp**. Ele se conecta ao RabbitMQ (escutando uma fila específica da instância), processa os comandos, envia as mensagens via WhatsApp, salva histórico local (SQLite) e sincroniza estados essenciais/realtime no PostgreSQL compartilhado. Também dispara Webhooks HTTP para notificar clientes sobre eventos (recebimento de mensagem, status, etc).

4. **Infra GitOps (`infra-gitops`)**:
   - **Papel**: Automação e configuração de Infraestrutura Kubernetes.
   - **Stack**: MicroK8s, ArgoCD (App of Apps pattern), Kustomize, Helm, Cert-Manager.
   - **Responsabilidades**: Repositório focado em manter o estado da infraestrutura, gerenciando a ordem de deploy (sync-waves) da base de dados, serviços de cache/mensageria e as aplicações (manager, api, etc).
