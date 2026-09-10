# Arquitetura do Sistema UzAPI

A arquitetura do UzAPI foi desenhada visando alta disponibilidade, isolamento de processos (sandbox por instância de WhatsApp) e deployment declarativo.

## Diagrama Geral da Arquitetura

```mermaid
flowchart TD
    %% Atores externos
    Client[Cliente/Usuário]
    APIClient[Sistema do Cliente via API/Webhook]
    WA[Servidores do WhatsApp]

    %% Ingress & Load Balancing
    subgraph K8s Cluster [Cluster Kubernetes MicroK8s]
        Ingress[Ingress Controller NGINX TLS]
        
        %% Manager Service
        subgraph Manager [Manager Service Next.js]
            Web[Frontend Painel]
            MAPI[API Interna & Orquestração]
        end
        
        %% API Service
        subgraph API [API Service NestJS]
            CoreAPI[Gateway de Integração]
        end

        %% Workers
        subgraph Workers [Workers Go - 1 Pod por Instância]
            W1[Worker Instância A]
            W2[Worker Instância B]
            Wn[Worker Instância N]
        end

        %% Bancos & Infra
        subgraph Databases [Data Layer & Mensageria]
            PG[(PostgreSQL Compartilhado)]
            RMQ((RabbitMQ))
            Redis[(Redis)]
            Mongo[(MongoDB)]
        end
    end

    Client -->|HTTPS /painel| Ingress
    Ingress --> Web
    Web --> MAPI

    APIClient -->|HTTPS /api| Ingress
    Ingress --> CoreAPI
    
    %% K8s orchestration
    MAPI -.->|Cria Deployments dinâmicos| Workers
    MAPI --> PG
    
    CoreAPI --> PG
    CoreAPI --> Mongo
    CoreAPI --> Redis
    CoreAPI -->|Publica mensagens| RMQ
    
    RMQ -->|Consome fila dedicada| W1
    RMQ -->|Consome fila dedicada| W2
    RMQ -->|Consome fila dedicada| Wn

    W1 <-->|Protocolo WhatsApp| WA
    W1 -->|Sync status| PG
    W1 -.->|Dispara HTTP| APIClient

    W2 <-->|Protocolo WhatsApp| WA
    Wn <-->|Protocolo WhatsApp| WA
```

## Componentes Chave

### 1. K8s Dinâmico (Manager Service)
O **Manager Service** utiliza as credenciais locais (`KUBECONFIG_PATH` apontando para o MicroK8s) para instanciar dinamicamente novos Pods de `worker-go` sob demanda de cada cliente. Assim, garante-se que, se uma sessão cair ou corromper, não afetará os demais clientes.

### 2. Mensageria Desacoplada (RabbitMQ)
As APIs (`api-service`) não interagem diretamente com o `worker-go` de forma síncrona para envio de mensagens. Elas depositam comandos (via RabbitMQ) em uma fila específica cujo nome é o `PHONE_NUMBER_ID` da instância correspondente.
O `worker-go` consome essa fila de forma isolada, controlando também mensagens com "delay" (via plugin `x-delayed-message` do RabbitMQ).

### 3. Gerenciamento de Estado (Bancos de Dados)
- **PostgreSQL**: Onde repousa o núcleo das informações. O Manager usa o Prisma/Drizzle para as tabelas principais de usuários e billing. O Worker utiliza uma tabela compartilhada (`public.instances` e `public.instance_realtime_state`) atualizando o status em realtime (usando UPSERT + NOTIFY trigger).
- **SQLite (No Worker)**: O pacote `whatsmeow` requer persistência atômica e rápida do device store criptográfico, mensagens e mídias. Para isso, há 1 arquivo `.db` gerado dinamicamente dentro de cada Pod.
- **MongoDB & Redis**: Utilizados pelo NestJS (`api-service`) para controle de cache, taxa limites (rate limit) ou modelagem flexível de logs e analíticos das integrações.

### 4. GitOps e Fluxo de Deploy
Toda a infraestrutura do MicroK8s e seus serviços essenciais é mantida via ArgoCD (padrão App of Apps). A ordem de deploy (Sync Waves) assegura que recursos de Storage (PVC) sejam criados primeiro, depois Bancos (PG, Redis, RabbitMQ), seguidos pelos serviços (Manager e então API).
