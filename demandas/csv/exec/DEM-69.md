---
id: DEM-69
status: concluido
data_ativacao: 2026-09-17 15:10:48
data_conclusao: 2026-09-22 10:00:00
modulo: API
---

# 🚀 Histórico de Execução: Endpoints de Fila (Queue) com erro 400

## 📌 Resumo do Problema
Todos os endpoints de gestão de fila de mensagens (queue) estavam retornando erro 400 - `username is missing`.

## 🛠️ Solução Adotada
1.  **TokenGuard (`api-service/src/common/guards/token.guard.ts`):** Removidas as 4 rotas de `queue` da lista de exclusão. Isso obriga o sistema a validar o JWT, garantindo que o `request['user']` seja populado.
2.  **UsernameInterceptor (`api-service/src/common/interceptors/username.interceptor.ts`):** Adicionadas as 4 rotas de emulação do Facebook (`/v1/me`, `/v1/:business_account_id/message_templates`, `/v1/:business_account_id`, `/v1/:phone_number_id`) na lista de exclusão.

## 🧪 Teste Prático e Homologação
- **Build:** Executado `npm run build` no repositório `api-service`. O processo concluiu com sucesso, sem erros de tipagem nas novas configurações de rotas.
- **Validação de Código:** As exclusões foram verificadas manualmente comparando com as definições de rotas no `controller` e garantindo que o `path-to-regexp` suporte os padrões.

## 📂 Arquivos Modificados
- `api-service/src/common/guards/token.guard.ts`
- `api-service/src/common/interceptors/username.interceptor.ts`
