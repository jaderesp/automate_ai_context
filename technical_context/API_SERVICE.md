# Contexto Técnico - API Service (`api-service`)

## Visão Geral
Repositório responsável por expor os endpoints públicos da API de WhatsApp para integração com os sistemas dos clientes. Funciona como um gateway inteligente, orquestrando recebimentos via HTTP e enfileiramento via RabbitMQ.

## Tecnologias e Stack
- **Framework**: NestJS (Node.js/TypeScript).
- **Gerenciador de Pacotes**: pnpm.
- **Integração Filas**: RabbitMQ (via `@golevelup/nestjs-rabbitmq` e `amqplib`).
- **Banco de Dados**: Suporta Mongoose (MongoDB), Drizzle ORM / pg (PostgreSQL).
- **Cache / Redis**: Redis (via `cache-manager-ioredis`).
- **Outros**: `@kubernetes/client-node` (possível acesso a status do K8s), Swagger para documentação (`@nestjs/swagger`).

## Detalhes de Implementação Importantes
1. **Ponto de Entrada**: Inicialização típica NestJS em `dist/main.js` via `nest build && node code.js` ou `nest start`.
2. **Integração RabbitMQ**: Atua como *Producer* majoritário. Quando os clientes invocam a API para enviar mensagens para um determinado número, a API valida a entrada, constrói o payload padrão e delega a mensagem a uma Exchange/Fila com routing-key atrelada ao worker responsável (geralmente ligada ao identificador da instância - `PHONE_NUMBER_ID`).
3. **Padrão de Qualidade**: Possui `eslint`, `prettier` e `commitlint` (com `commit-and-tag-version` para versionamento semver automático). O Pipeline CI (`.gitlab-ci.yml`) dita a build do container Docker (`Dockerfile` e `RabbitDockerfile`).

## Responsabilidade vs Worker
- O `api-service` **NÃO** possui dependência direta com o protocolo do WhatsApp (`whatsmeow`).
- Se um cliente faz um GET na API que dependa de estado online do Whatsapp, o `api-service` possivelmente lê do PostgreSQL Compartilhado ou consulta status de Redis/Mongo ao invés de falar com o WhatsApp diretamente de forma síncrona, evitando travamentos.
