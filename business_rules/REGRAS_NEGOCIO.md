# Regras de Negócio e Lógica de Domínio - UzAPI

## Contexto de Negócio
O UzAPI oferece a capacidade de interagir de forma programática com o WhatsApp. A plataforma gerencia clientes (saas/tenant), onde cada cliente pode assinar/pagar (integração Asaas no manager) e provisionar **Instâncias do WhatsApp**.

### 1. Vida Útil da Instância (WhatsApp Worker)
- **Criação**: Quando o cliente solicita uma nova conexão no painel, o **Manager Service** se comunica via Kubernetes API para fazer o spawn de um novo Pod (`worker-go`).
- **Autenticação**: O pod suporta autenticação via `QRCode` ou `PairingCode`. O cliente abre seu WhatsApp no celular e lê o QRCode gerado pelo sistema (exibido no frontend através de leitura via banco/socket) para parear.
- **Isolamento**: Existe 1 container (`worker-go`) por sessão do WhatsApp. O histórico é persistido num SQLite próprio do container para segurança e integridade do sinal criptográfico da biblioteca `whatsmeow`.
- **Desconexão**: Em certos erros fatais (ex: `LoggedOut`, `PermanentDisconnect`), o Pod intencionalmente faz `os.Exit(1)`. A infraestrutura de K8s cuidará de matar ou reiniciar a sessão dependendo do estado esperado.

### 2. Mensageria Assíncrona e Webhooks
- **Envio**: O cliente utiliza o `api-service` (chamadas REST) para enviar mensagens. A API enfileira este comando no RabbitMQ para não bloquear a requisição HTTP e segurar estabilidade durante alta carga.
- **Processamento**: O `worker-go` retira a mensagem da fila dedicada (`PHONE_NUMBER_ID`) e utiliza o protocolo do WhatsApp para efetuar o disparo.
- **Webhooks**: Todos os eventos oriundos do próprio celular (mensagens recebidas, status de lido, eventos de grupo) são capturados pelo worker. Se o cliente configurar o webhook (via `WEBHOOK_URL` e `WEBHOOK_EVENTS`), o Worker dispara requisições HTTP (POST) para os endpoints informados (arquitetura push).

### 3. Falhas e Resiliência
- Se uma mensagem tenta ser enviada para um número não existente (verificado por `IsOnWhatsApp` via `whatsmeow`), o worker cancela e notifica imediatamente pelo Webhook de erro, não poluindo o fluxo de envio real.
- Em caso de desconexões passageiras, o Worker guarda estado até poder religar o socket do WhatsApp sem afetar APIs externas.

### 4. Notificações e Financeiro
- Notificações de sistema e cronjobs ficam sob responsabilidade do `manager-service` (ex: `node-cron` que roda a cada minuto para automações e campanhas programadas).
- Fluxo financeiro (Asaas) valida quais clientes estão adimplentes para liberar ou pausar dinamicamente os `Deployments` (workers) de WhatsApp no cluster.
