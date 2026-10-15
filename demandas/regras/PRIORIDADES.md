# 📋 Especificação Técnica: Regras de Priorização e Seleção de Tasks

Este documento define a especificação técnica oficial para a seleção, ordenação e priorização de tarefas do backlog (bugs e melhorias) no ecossistema UzAPI. Todas as diretrizes aqui descritas devem ser rigorosamente seguidas pelos agentes de IA e desenvolvedores.

---

## 1. Campos de Decisão (Backlog / CSV)

Para o cálculo de elegibilidade e ordenação, o sistema avalia os seguintes campos do backlog:

| Campo | Descrição e Valores Aceitos |
| :--- | :--- |
| **`Status`** | Situação do ciclo de vida da demanda. **Apenas tarefas elegíveis** entram no cálculo de execução: `A Fazer`, `Devolvido`, `Aprovado`, `Pendente`. Tarefas com `Concluído`, `Em Homologação`, `Cancelado` ou `Standby` são desconsideradas da fila ativa. |
| **`Responsável` (Origem)** | Identifica a origem do chamado: <br>• **Externo / Cliente:** apontadas diretamente por clientes/usuários finais. <br>• **Interno:** criadas por membros da equipe (ex: `Hugo Peres`, `Lucas Moreira`, desenvolvedores). |
| **`Prioridade`** | Nível de severidade informado na demanda: `Urgente`, `Alta`, `Média` / `Normal`, `Baixa` / `Leve`. |
| **`Módulo` (Tela / Contexto)** | Contexto funcional e arquitetural afetado (ex: `Instâncias`, `Assinaturas`, `Módulo API`, `Chat`, `Financeiro`, etc.). Utilizado na heurística de agrupamento. |

---

## 2. Hierarquia Estrita de Prioridades (Fila Principal)

A fila de execução é dividida em 5 faixas hierárquicas estritas (P1 a P5). Uma faixa inferior **nunca** pode ser iniciada enquanto houver tarefas elegíveis em uma faixa superior (ressalvada a regra de *Batching* quando permitida):

```
┌──────────────────────────────────────────────────────────┐
│  P1 (Crítica Externa)   - Cliente + Urgente              │
├──────────────────────────────────────────────────────────┤
│  P2 (Alta Externa)      - Cliente + Alta                 │
├──────────────────────────────────────────────────────────┤
│  P3 (Crítica Interna)   - Hugo / Lucas + Urgente         │
├──────────────────────────────────────────────────────────┤
│  P4 (Demais Clientes)   - Cliente + Normal / Baixa       │
├──────────────────────────────────────────────────────────┤
│  P5 (Demais Internas)   - Internas (Alta → Normal → Baixa)│
└──────────────────────────────────────────────────────────┘
```

1. **P1 (Crítica Externa):** Tarefas apontadas por **Cliente** com prioridade **Urgente**. (Bloqueio crítico de operação de cliente).
2. **P2 (Alta Externa):** Tarefas apontadas por **Cliente** com prioridade **Alta**. (Impacto relevante em cliente).
3. **P3 (Crítica Interna):** Tarefas com prioridade **Urgente** criadas pela liderança interna (**Hugo Peres** ou **Lucas Moreira**).
4. **P4 (Demais Clientes):** Tarefas apontadas por **Cliente** com prioridade **Normal** ou **Baixa**.
5. **P5 (Demais Internas):** Tarefas internas ordenadas por severidade decrescente (**Alta** $\rightarrow$ **Normal** $\rightarrow$ **Baixa**).

---

## 3. Heurística de Agrupamento por Contexto (Batching de Tela / Módulo)

### Flag de Configuração
- **`allow_context_batching: boolean`** (Padrão sugerido: `true`)

### Comportamento
Ao concluir uma tarefa de um determinado **Módulo** (ex: tela de *Instâncias*), caso existam outras tarefas pendentes no mesmo módulo (mesmo que com prioridade P4 ou P5):
- O agente pode optar por executá-las em lote para aproveitar o contexto de arquivos abertos, container/worker já instrumentados e testes afins.
- **TRAVA DE SEGURANÇA CRÍTICA:** O batching só é autorizado se **NÃO HOUVER** tarefas de clientes de gravidade crítica pendentes (**P1** ou **P2**) em outras áreas. Se houver qualquer tarefa P1 ou P2 aguardando em outro módulo, o batching é cancelado e o agente deve mudar de contexto imediatamente para atender a emergência externa.

---

## 4. Pseudocódigo do Algoritmo de Seleção da Fila

```typescript
/**
 * Algoritmo Oficial de Priorização e Seleção de Tasks (UzAPI)
 */

interface Task {
  id: string;
  modulo: string;
  prioridade: "Urgente" | "Alta" | "Normal" | "Média" | "Baixa" | "Leve";
  status: string;
  responsavel: string; // Origem: "Cliente", "Hugo Peres", "Lucas Moreira", etc.
}

const STATUS_ELEGIVEIS = ["A Fazer", "Devolvido", "Aprovado", "Pendente"];

enum NivelFila {
  P1 = 1, // Crítica Externa (Cliente + Urgente)
  P2 = 2, // Alta Externa (Cliente + Alta)
  P3 = 3, // Crítica Interna (Hugo / Lucas + Urgente)
  P4 = 4, // Demais Clientes (Cliente + Normal / Baixa)
  P5_ALTA = 5,   // Interna Alta
  P5_NORMAL = 6, // Interna Normal / Média
  P5_BAIXA = 7,  // Interna Baixa
  INELIGIVEL = 99
}

function calcularNivel(task: Task): NivelFila {
  if (!STATUS_ELEGIVEIS.includes(task.status)) {
    return NivelFila.INELIGIVEL;
  }

  const isCliente = task.responsavel.toLowerCase().includes("cliente");
  const isLiderancaInterna = ["hugo peres", "lucas moreira"].some((lider) =>
    task.responsavel.toLowerCase().includes(lider)
  );

  const prio = task.prioridade.toLowerCase();

  // P1: Cliente + Urgente
  if (isCliente && prio === "urgente") return NivelFila.P1;

  // P2: Cliente + Alta
  if (isCliente && prio === "alta") return NivelFila.P2;

  // P3: Crítica Interna (Hugo ou Lucas + Urgente)
  if (isLiderancaInterna && prio === "urgente") return NivelFila.P3;

  // P4: Demais Clientes (Normal, Média, Baixa)
  if (isCliente) return NivelFila.P4;

  // P5: Demais Internas ordenadas por gravidade
  if (prio === "urgente" || prio === "alta") return NivelFila.P5_ALTA;
  if (prio === "normal" || prio === "média") return NivelFila.P5_NORMAL;
  return NivelFila.P5_BAIXA;
}

function selecionarProximaTask(
  backlog: Task[],
  ultimoModuloExecutado: string | null = null,
  allow_context_batching: boolean = true
): Task | null {
  // 1. Filtra tarefas elegíveis e classifica o nível de fila
  const candidatas = backlog
    .map((task) => ({ task, nivel: calcularNivel(task) }))
    .filter((item) => item.nivel !== NivelFila.INELIGIVEL);

  if (candidatas.length === 0) return null;

  // 2. Verifica se existem bloqueios críticos externos (P1 ou P2)
  const temCriticoExterno = candidatas.some(
    (item) => item.nivel === NivelFila.P1 || item.nivel === NivelFila.P2
  );

  // 3. Heurística de Batching por Módulo/Tela
  if (allow_context_batching && ultimoModuloExecutado && !temCriticoExterno) {
    // Busca se há tarefas no mesmo módulo com prioridade aceitável
    const tarefasMesmoModulo = candidatas.filter(
      (item) => item.task.modulo.toLowerCase() === ultimoModuloExecutado.toLowerCase()
    );

    if (tarefasMesmoModulo.length > 0) {
      // Ordena as tarefas do mesmo módulo por nível de prioridade
      tarefasMesmoModulo.sort((a, b) => a.nivel - b.nivel);
      return tarefasMesmoModulo[0].task;
    }
  }

  // 4. Seleção padrão da Fila Principal (Menor nível = Maior prioridade)
  candidatas.sort((a, b) => a.nivel - b.nivel);
  return candidatas[0].task;
}
```

---

## 5. Prazos e SLA (Service Level Agreement)

Complementarmente à hierarquia, as faixas de execução devem observar as seguintes janelas operacionais:

- **🔴 P1 & P2 (Urgente / Alta Externa):**
  - **SLA:** Atendimento imediato. Correção ou disponibilização da solução no **mesmo dia** ou até **24 horas**.
- **🟠 P3 (Crítica Interna - Hugo / Lucas):**
  - **SLA:** Execução preferencial dentro da **mesma semana** (até 48h a 72h).
- **🟡 P4 (Demais Clientes):**
  - **SLA:** Execução dentro da **mesma quinzena**.
- **🟢 P5 (Demais Internas):**
  - **SLA:** Execução conforme disponibilidade de ciclo dentro do **mês vigente**.
