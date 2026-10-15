---
id: DEM-49
status: concluido
data_ativacao: 2026-09-19 14:03:24
data_conclusao: 2026-09-21 14:00:00
modulo: Contratar Instâncias
---

# 🚀 Histórico de Execução: Falha grave no downgrade de instancias

## 📌 Resumo do Problema
Testei com um usuário que tinha 2 instancias ativas. Fiz o downgrade para 1 instancia. Ainda sim, as 2 instancias do usuário continuaram ativas e funcionando perfeitamnete. O Dashboard estava exibindo: 2/1 instancias ativas Ou seja, permitindo o usuário usar 2 instancias mesmo em um plano de 1 instancia.

TESTAMOS E REALMNETE IMPEDIU O DOWNGRADE AO TER QUANTIDADE DE INSTANCIAS CRIADAS MAIOR QUE  A QUANTIDADE DE INSTANCIA DO DOWNGRADE.

## 🛠️ Solução Adotada
Finalizado por outro programador. A lógica de bloqueio de downgrade ao exceder a quantidade de instâncias foi validada e implementada (ver commits do repositório).

## 📂 Arquivos Modificados
(Ver commits do repositório)

## 🧪 Teste Prático e Homologação
Finalizado por outro programador via commits.
