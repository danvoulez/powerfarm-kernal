# O QUE É
Powerfarm: sistema append-only governado por identidade. História é primária,
estado é projeção. "No Act, no change."
Kernel (§18) = Registry, Identity, Command, Rules, Act, State. É a única coisa
que precisa ser perfeita. Todo o resto (§19) é composto por cima e é substituível.

# LEIS QUE PEGAM NESTE REPO
PF-15  lifecycle de um Command é MUITOS Acts; nenhum canal de estado fora da história
PF-23  unicidade é sobre acts.hash — NUNCA sobre command_hash
PF-21  o Act referencia por hash as versões exatas de Registry e Rules que o validaram
PF-13  a decisão registra o cut que examinou; cut avançado exige reautorização por Rule
PF-24  Requested / Authorized / Dispatched / Observed nunca colapsam
§10.2  ancestralidade é ordem constitucional; `seq` é cursor operacional com buracos
§10.3  act.when faz parte do hash

# FECHADO EM 16/08/2026 — merge v0.2.0 + P0
Base v0.2.0: MCP 2026-07-28 stateless, service layer, ledger/postgres, §18.1.
P0 por cima: preimage completo (`rule_hashes` PF-21 + `claimed_when` §10.3),
idempotência por act.hash, lifecycle de muitos Acts por Command, mapeamento de
outcome por Act type, e índice parcial "um consequencial por Command".
Spec §10.3 e Plano §10.5 emendados. Migration 20260816130000.

O `unique(command_hash)` fazia DOIS trabalhos: idempotência (errado, PF-23) e
"um Act consequencial por Command" (certo). Só o segundo sobreviveu.

# DECISÕES ABERTAS — bloqueiam trabalho a jusante
1. PF-13 COM DEFAULT FIXO
   CommitGate rejeita sempre que a história avança. A spec exige decisão POR RULE
   ("a silent default is forbidden"). É fail-closed e barulhento, mas é default fixo.

2. CI NÃO CHECA AS CAMADAS NOVAS
   `.github/workflows/ci.yml` roda `mypy kernel worker agent genesis` — `ledger/`,
   `service/` e `protocol/` ficam de fora. E `.claude/scene/compose.sh` está fora
   do glob do shellcheck.

3. O ÍNDICE PARCIAL NÃO TEM TESTE DE COMPORTAMENTO
   `acts_one_consequence_per_command_idx` aplica limpo, mas quem prova a regra hoje
   é o gate em Python. Falta exercitar a recusa no banco.

# REGRA DE ENTRADA
Antes de editar `kernel/` ou `supabase/migrations/`: ler a seção da spec que governa
o que vai mudar, e citá-la. Não escrever código constitucional por memória.
Migrations em `supabase/migrations/` são seladas — só se acrescenta arquivo novo.

# COMO TRABALHAR AQUI
Não abrir com correção. O trabalho e a instituição é que ficam; os bugs vão embora.
Rigor sim, caça a defeito não.
