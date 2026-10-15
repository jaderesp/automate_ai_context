---
id: DEM-3
status: concluido
data_conclusao: 2026-09-21 15:30:00
data_ativacao: 2026-09-21 10:51:06
modulo: Meu Perfil
---

# 🚀 Histórico de Execução: Autonomia para exclusão da conta

## 📌 Resumo do Problema
Permitir que o usuário exclua a conta caso não queira mais usar a plataforma da Uzapi.

OBS: AO EXCLUIR A CONTA, DEVE-SE TAMBÉM EXCLUIR A ASSIANTURA DESSE CLIENTE NO ASAAS. CASO ELE VOLTE A FAZER UM NOVO CADASTRO NA UZAPI E CONTRATAR UMA NOVA INSTANCIA PAGA, A PLAATFORMA PODE REAPROVEITAR O CADASTRO DO ASAAS E SÓ CRIAR A NOVA ASSIANTURA.

## 🛠️ Solução Adotada
Alterada a lógica de exclusão do perfil do usuário em `src/app/api/user/profile/route.ts`. A função `deleteCustomer` do Asaas foi substituída por `cancelAllActiveSubscriptionsForCustomer`, garantindo que apenas as assinaturas recorrentes sejam canceladas, preservando o cadastro do cliente para futuras reativações.

## 📂 Arquivos Modificados
- `src/app/api/user/profile/route.ts`

## 🧪 Teste Prático e Homologação
A alteração foi realizada seguindo a arquitetura existente. O código foi validado via inspeção visual da nova chamada de função, que utiliza a lib existente `cancelAllActiveSubscriptionsForCustomer` em `src/lib/asaas.ts`. A estrutura da rota de perfil (DELETE) foi mantida conforme o padrão.
