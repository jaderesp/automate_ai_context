# Padrão de Configuração do Agente (AGENTS.md)

Este documento descreve a regra de ouro para a inicialização deste contexto (`ai.context`) em qualquer novo projeto.

## 🎯 Objetivo
Toda vez que este repositório `automate_ai_context` for clonado ou carregado para dentro de um novo projeto, o Agente IA (Antigravity ou outro) deve identificar este padrão e gerar automaticamente um arquivo chamado `AGENTS.md` na **raiz** do projeto hospedeiro.

## 🛠️ O que o Agente deve fazer:
Ao iniciar os trabalhos em um projeto que contenha esta pasta `ai.context`, o agente deve ler este arquivo e replicar o conteúdo abaixo em um arquivo `/AGENTS.md` na raiz do projeto (ex: `../AGENTS.md`).

Isso é fundamental pelo sistema de "Rules" do Antigravity, que faz com que a IA leia e obedeça automaticamente o arquivo `AGENTS.md` se ele estiver na raiz.

## 📝 Conteúdo Padrão do `AGENTS.md` (Copiar e Colar):

```markdown
# Regras do Agente (Workflow de Demandas)

Este documento é a "Regra de Ouro" (AGENTS.md) do projeto. Todo agente o lerá automaticamente ao iniciar. Você deve seguir este fluxo rigorosamente:

## 1. Triagem no Kanban (`ai.context/demandas/csv/exec/`)
A interface visual gera um arquivo na pasta `ai.context/demandas/csv/exec/` (ex: `DEM-1.md`) com o metadado YAML `status: pendente`.
- Ao iniciar o trabalho, você DEVE buscar e ler arquivos `.md` com `status: pendente` nessa pasta.

## 2. Processo de Decisão
Não altere código sem autorização!
- Apresente um panorama do impacto técnico.
- Ofereça opções de solução (ex: Opção A vs Opção B) com Prós e Contras.
- Aguarde a autorização e escolha do Desenvolvedor.

## 3. Conclusão e Atualização do Kanban (CRÍTICO)
Após finalizar a demanda, você **NÃO DEVE** criar um arquivo novo.
Você **DEVE OBRIGATORIAMENTE** editar o arquivo existente gerado pela etapa 1 (ex: `DEM-1.md`):
- Altere o frontmatter para `status: concluido`.
- Preencha os campos vazios do arquivo com o Resumo, a Solução Adotada, e a lista de arquivos afetados.

Isto encerra o ciclo no Kanban e preserva os tokens.
```
