# Contexto Técnico - Manager Service (`manager-service`)

## Visão Geral
Este repositório é o "cérebro" de gestão do SaaS. É o frontend (painel de administração e cliente) e também a API de administração do serviço.

## Tecnologias e Stack
- **Framework**: Next.js 16 (App Router) + React 19.
- **Frontend UI**: TailwindCSS, Shadcn UI, Radix UI.
- **ORM / BD**: Drizzle ORM com PostgreSQL (driver `pg`).
- **Autenticação**: Better Auth (solução focada no Next.js).
- **Outros**: Integração Asaas (pagamentos), Kubectl API (`@kubernetes/client-node`), `node-cron` (tarefas agendadas).

## Detalhes de Implementação Importantes
1. **Migrations Drizzle**:
   - Os schemas habitam `src/database/schemas/*.ts`.
   - **ATENÇÃO**: Migrations customizadas (ex: triggers ou functions SQL) devem ser escritas na pasta `src/database/custom-migrations/`. O comando `pnpm db:generate` roda um script automático (`scripts/sync-drizzle-custom-migrations.mjs`) que copia isso para a pasta `drizzle/`. Nunca altere arquivos diretamente dentro da pasta `drizzle/` que contenham lógica SQL manual, faça na origem `custom-migrations`.
2. **Proxy e Autenticação Optimista**:
   - O `src/proxy.ts` (substituto do `middleware.ts` do Next.js) atua apenas para redirecionamentos otimistas lendo o Cookie de forma rápida para proteger `/dashboard`, `/instances`, `/admin`. A validação criptográfica do Better Auth é feita em cada página server-side na rota para real proteção.
3. **Orquestração de Kubernetes (K8s)**:
   - Utiliza `src/services/kubernetes/` juntamente com as variáveis do arquivo `.env` para disparar chamadas para a API do Kubernetes do servidor. É este projeto que gerencia as manifestações do `worker-go` (criando novos "whatsapp" sob demanda).
4. **Cronjobs In-Memory**:
   - O `src/instrumentation.ts` do Next.js registra funções do `node-cron` a cada boot (campanhas e automações diárias/minuto). É essencial que qualquer side-effect inicializado aqui seja idempotente devido ao modelo de multi-processos de serveless/servers do Next.js.
5. **Git e CI/CD**:
   - Assim como na API, usa o standard `commit-and-tag-version` (via pnpm release). O tag/push de release dispara no Gitlab a imagem Docker e altera o manifest da infra no repo `infra-gitops`.
