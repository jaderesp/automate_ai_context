---
id: DEM-62
status: concluido
data_ativacao: 2026-09-14 11:36:44
data_conclusao: 2026-10-09 12:00:00
modulo: Instâncias
---

# 🚀 Histórico de Execução: Não exibe QRCode para instancias com status Pausada

## 📌 Resumo do Problema
O QA relatou que ao clicar em "Autenticar" ou "Escanear QRCode" em instâncias que estão com o status "Pausada", o QRCode não é exibido (o modal abre mas entra em loop de loading eterno). A causa raiz arquitetural é que uma instância "Pausada" não possui o pod/worker do WhatsApp rodando, portanto é impossível gerar um QRCode. O erro real é de UX/UI: o painel `manager-service` não deveria oferecer o botão de QRCode para instâncias pausadas.

## 🛠️ Solução Proposta
A proposta (já arquitetada e testada localmente na branch `fix/dem-62-paused-qrcode` do `manager-service`) consiste em refatorar as condições de exibição nos componentes de interface:
1. Em `instance-card.tsx` e `actions-menu.tsx`, a checagem `{status !== "connected"}` (que abrangia instâncias desconectadas e pausadas) será alterada para verificar estritamente `status === "disconnected"`.
2. Para instâncias Pausadas (`status === "paused"`), o botão roxo de QRCode será totalmente substituído pelo botão **"▶️ Retomar Instância"**, que dispara diretamente a função `handleAction("restart")`.
3. No Menu de Ações (três pontinhos), a opção "Autenticar" ficará oculta para instâncias pausadas.

Desta forma, forçamos o usuário a obrigatoriamente retomar (ligar) a instância antes de tentar qualquer autenticação, eliminando o falso positivo de "QRCode que não carrega".

## 📂 Arquivos Modificados (Preview)
- `manager-service/src/app/instances/components/instance-card.tsx`
- `manager-service/src/app/instances/components/actions-menu.tsx`

---

## 🔎 Atualização 06/10/2026

Sem avanço desde 02/10: as alterações em `instance-card.tsx` e `actions-menu.tsx` seguem **não commitadas** na branch `fix/dem-62-paused-qrcode` do `manager-service` (baseada na `v0.3.57`), aguardando aprovação do desenvolvedor.

Pontos levantados na revisão de 02/10 e ainda não tratados:
- O botão "Retomar Instância" chama a ação `restart`, não o endpoint `resume`. Pelo código do `api-service` (`k8s.service.ts`, `restartInstance` → `recoverInstance`) o `restart` sem pod recria o deployment e grava `pending_auth`, igual ao `resumeInstance`; **não testado na prática**.
- `instance-sheet.tsx` e `page.tsx` também tratam o estado pausado e não foram alterados; falta verificar se ainda oferecem autenticação para instância pausada.
- A afirmação "testada localmente" acima não tem evidência registrada.

---

## 🛠️ Correção commitada (08/10/2026)

> **Estado:** commit `96ea5f8` na branch `fix/dem-62-paused-qrcode` do `manager-service`, **sem push**. A branch está sobre a `main` atual (`468b45b`, `v0.3.58`). `status` segue `pendente` até o merge.

### Causa
`getStatus` (`src/app/instances/types.ts`) devolve três estados: `connected`, `disconnected` e `paused`. Os três pontos da tela que oferecem autenticação usavam a condição `status !== "connected"`, que inclui `paused`. Instância pausada não tem pod em execução, então o modal de QR Code abria e nunca recebia o código.

### Alterações
| Arquivo | Antes | Depois |
|---|---|---|
| `src/app/instances/components/actions-menu.tsx` | "Autenticar" se `status !== "connected"` | só se `status === "disconnected"` |
| `src/app/instances/components/instance-card.tsx` | "Escanear QRCode" se `status !== "connected"` | QR Code só para `disconnected`; `paused` mostra **Retomar Instância** (`handleAction("restart")`) |
| `src/app/instances/components/instance-sheet.tsx` | "Autenticar" se `status !== "connected"` | só se `status === "disconnected"` (o botão "Reiniciar Instância" já existia na tela) |

`src/app/instances/page.tsx` não precisou de alteração.

### 🧪 Teste Prático e Homologação
- `npx tsc --noEmit` e `eslint` nos três arquivos: sem erros.
- **Não testado:** comportamento real do reiniciar em instância pausada (depende do cluster). Pelo código do `api-service` (`restartInstance` → `recoverInstance`), sem pod o deployment é recriado e o status vai para `pending_auth`, exibido como "Desconectado"; é o mesmo contorno relatado pelo QA no backlog.
- **Roteiro para o QA:** com uma instância pausada, conferir que (1) o cartão mostra "Retomar Instância" e não "Escanear QRCode"; (2) o menu de ações e a tela de detalhes não mostram "Autenticar"; (3) após retomar/reiniciar, o status passa a "Desconectado" e o QR Code aparece.

### Liberação
A partir de `468b45b` o `manager-service` usa semantic-release: o merge na `main` gera a tag e publica sozinho (merge na `dev` gera `-dev.N` no cluster de desenvolvimento). `pnpm release` foi removido. Destino do MR (`dev` ou `main`) a confirmar com o programador chefe.

---

## ✅ Encerramento (09/10/2026)

- `status` alterado para `concluido`: o desenvolvedor informou em 09/10 que a demanda foi concluída (MR da branch `fix/dem-62-paused-qrcode`, commit `96ea5f8`, push em 08/10).
- **Não verificado daqui:** o merge e a versão gerada pela pipeline (sem `git fetch` nesta sessão desde 08/10; a `origin/main` local ainda está em `468b45b`).
- **Backlog (CSV exportado em 09/10 11:59):** a demanda consta "Em Andamento"; reteste do QA ainda não registrado.
