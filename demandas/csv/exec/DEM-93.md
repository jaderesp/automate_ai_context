---
id: DEM-93
status: pendente
data_ativacao: 2026-10-15 16:37:35
modulo: Instâncias
---

# 🚀 Histórico de Execução: Erro ao tentar autenticar instancia mobile

## 📌 Resumo do Problema
Ao tentar autenticar uma instancia mobile com um numero virtual, exibe esse erro: Timeout waiting for response from RabbitMQ


## 🔬 Análise (15/10/2026, só leitura; nada alterado)
**Escopo:** a autenticação mobile é funcionalidade nova do Eduardo — só existe na `dev` (`worker-go` `15a1bef` 08/10 → `609e150` 10/10; `api-service` `MobileAuth` 09/10) e na branch `mobile` dele (1 commit à frente em cada repo, 13/10). Não está na `main` do `worker-go` nem do `api-service`; logo o erro foi visto no ambiente **dev**. A coluna Versão da planilha (`0.095`) é o valor padrão e não indica onde foi testado.

**Origem da mensagem:** `api-service` `src/rabbitmq/rabbitmq.service.ts:201` — `send(..., useReplyTo = true)` publica na fila da instância e rejeita com `Timeout waiting for response from RabbitMQ` se o worker não responder em **30 s** (`setTimeout(..., 30000)`, fixo para todas as chamadas). O fluxo mobile usa esse caminho: `src/controllers/MobileAuth/mobile-auth.controller.ts` (`dispatch`, `POST /:version/:phone_number_id/mobile/:action`).

**Worker:** `rabbitmq/listener.go` (executor `"mobile"`) → `services/mobile_auth.go` → `MobileRequestCode` chama `GetMobileRegistrationStatus` + `RequestMobileCode`/`RetryMobileCode` do fork `edupoli/whatsmeow` (`v0.0.0-20261010181705-29043430d4af`). No fork, cada chamada HTTP do registro tem limite de **45 s** (`mobile_http.go:394` `DefaultRegistrationRequestTimeout = 45 * time.Second`; `HTTPClient{Timeout: 45s}`), e o pedido de código pode fazer mais de uma chamada.

**Causa provável (não confirmada em log):** limites desencontrados — o worker pode legitimamente levar mais de 30 s falando com os servidores do WhatsApp (número virtual, rede lenta, proxy), enquanto a API desiste aos 30 s. O painel mostra o timeout, mas o worker continua e pode até concluir a etapa (o estado sai pelo realtime `mobile.auth`), deixando a tela fora de sincronia; um novo clique encontra "já existe uma tentativa em andamento".

**Outras causas possíveis do mesmo erro:** pod da instância ainda subindo ou parado (fila sem consumidor); worker travado/caído (o commit de 13/10 na branch `mobile` corrige `WhatsappLogLevel = DEBUG`, que gerava ~45 GB/h de log e podia derrubar pods por eviction, e um nil pointer em `handleMediaURL`).

**Para confirmar:** log do pod da instância e do `api-service` no horário do teste (duração da chamada de registro; se a resposta chegou depois dos 30 s).

### Propostas (aguardando decisão)
- **A (recomendada):** `api-service` — `send` aceita um timeout opcional; o `dispatch` mobile usa ~120 s. Conferir também o timeout do ingress/proxy entre o painel e a API (comumente 60 s). Mudança pequena, sem afetar as demais chamadas.
- **B:** `worker-go` — reduzir o limite das chamadas de registro (`SetRequestTimeout`, ~20 s) para o worker responder com erro claro antes dos 30 s. Contra: pode falhar chamadas lentas que dariam certo.
- **C:** tornar a etapa assíncrona (responder na hora e entregar o resultado só pelo realtime). Mais robusto, mas muda o desenho do Eduardo.
- Por ser funcionalidade do Eduardo em desenvolvimento ativo (branch `mobile`), alinhar com ele antes de alterar.

## 🛠️ Solução Adotada
(IA preencherá este campo após autorização)

## 📂 Arquivos Modificados
- (A preencher)
