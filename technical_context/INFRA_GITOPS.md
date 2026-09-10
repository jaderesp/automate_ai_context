# Contexto Técnico - Infraestrutura e GitOps (`infra-gitops`)

## Visão Geral
Este repositório mantém a Infraestrutura como Código (IaC) e o fluxo declarativo do Cluster Kubernetes que suporta o projeto UzAPI. O gerenciamento de CD (Continuous Deployment) é realizado pelo ArgoCD.

## Padrão App of Apps
- A abordagem utiliza 1 aplicação raiz, contida em `bootstrap/root-app.yaml`, que aponta de volta para o próprio repositório na pasta `bootstrap/apps/`. Todas as outras instâncias da infra (postgres, cert-manager) e as aplicações em si (manager-service, api-service) são Applications geridas pela Root App.

## Ordem de Sincronização (Sync Waves)
Para evitar "condition races" (ex: subir app antes do banco), o ArgoCD usa anotações `sync-wave`:
- **Wave -1**: `infra-cert-manager` (certificados TLS básicos).
- **Wave 0**: PVCs, Storage, ConfigMaps, e infra básica de auto scaling.
- **Wave 1**: Bancos (Postgres, Redis, RabbitMQ) via Helm charts (bitnami etc).
- **Wave 2**: Ingress externo ArgoCD.
- **Wave 3**: `manager-service` (Painel).
- **Wave 4**: `api-service` (API).
- **Wave 5**: Possíveis frontends/backends auxiliares (SPA, etc).

*Nota técnica: Além de Applications, os recursos K8s dentro de uma Application também podem possuir sync-waves granulares (Ex: PVC > ConfigMap > Service > Deployment).*

## Configurações Fixas
- **Servidor K8s**: Baseado no MicroK8s instalado na VPS Ubuntu (scriptável via `scripts/setup-vps.sh`).
- **Segredos (Secrets)**: Não são comitados valores sensíveis. O template `CHANGE_ME_*` existe para ser alterado via script/CLI ao realizar o deploy, documentado em `secrets/README.md`.
- **Ingress**: Utiliza o Ingress do MicroK8s publicamente (`ingressClassName: public`). O TLS é orquestrado via cert-manager. 

## Como Interage com o CI
Quando há um `pnpm release` (geração de tag) nos projetos principais (manager ou api), os repositórios correspondentes têm um estágio no CI do GitLab que substitui a tag da imagem no `infra-gitops` (ex: em `apps/manager-service/deployment.yaml`) e emite um commit de Deploy, ativando automaticamente a rotina de pull e update declarativo via ArgoCD.
