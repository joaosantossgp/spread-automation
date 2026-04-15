# MEMORIADASIA.md — Memória Compartilhada entre Agentes de IA

> **PARA AGENTES DE IA**: Leia as seções **Estado Atual** e **Restrições Ativas** antes
> de começar qualquer tarefa. Leia o histórico de sessões apenas se estiver depurando
> uma regressão específica. Consulte também [CLAUDE.md](CLAUDE.md) para fatos críticos
> do código e [CONTEXT.md](CONTEXT.md) para referência completa do domínio e pipeline.
>
> Ao final de cada sessão, atualize "Estado Atual" e adicione uma entrada resumida em
> "Arquivo de Sessões". **Regra de compressão**: máximo 150 linhas. Após 3 sessões novas,
> comprima as mais antigas para 2-3 frases e mova para o arquivo.

---

## Estado Atual (2026-03-25)

Pipeline funcional com matching híbrido de duas camadas validado contra Minerva 4T24 e Sabesp 4T24:
- **Camada 1** (`core/conta_map.py`): matching determinístico por CD_CONTA CVM — 25+ entradas cobrindo BP e DRE completa
- **Camada 2** (`processing/spread.py`): fallback por valor numérico — ativo para contas sem mapeamento direto
- DFC usa busca textual por regex (seção 6.01 apenas) — correto por design, DFC não tem contas fixas
- DMPL usa Camada 1 por CD_CONTA (5.04.06, 5.04.07, 5.04.01) com fallback textual
- `docs/cvm_account_dictionary.csv` adicionado: 17.068 DS_CONTA únicas para diagnóstico de regex

---

## Restrições Ativas (gotchas que causam bugs)

1. **Filtro DFC obrigatório**: sempre filtrar `Codigo Conta` começando com `"6.01"` antes do regex de depreciação. Sem esse filtro, `6.03.02 "Amortizações"` (pagamento de empréstimo) é capturado — bug confirmado com Sabesp (-85% erro)
2. **Branch fórmula literal**: no branch `=-123456`, testar Camada 1 ANTES do loop de substituição literal. Sem isso, empresa nova (sem valor de referência) fica com valor da empresa anterior.
3. **SKIP = {199, 209, 210, 213}**: essas linhas são preenchidas por funções especializadas — nunca incluir na varredura padrão
4. **Colunas do Spread**: D/F/H/J são dados; A/C/E/G/I/K são ocultos. `col_txt_to_idx` retorna 0-based; `get_column_letter` é 1-based; offset correto para pular coluna oculta = +3
5. **Reapresentações silenciosas**: campo `VERSAO` incrementa quando empresa republica demonstrações. Pipeline não detecta — valores históricos podem mudar sem aviso
6. **L201 risco de falso-positivo**: "Amortização Acumulada Dif. Normal" pode ter mesmo valor que depreciação DFC → false-positive no value-matching. João corrige manualmente. Candidata ao SKIP se recorrer.

---

## Decisões Permanentes do João

| Data | Decisão |
|------|---------|
| 2026-03-12 | Extração de PDFs descartada — pipeline sempre via `DadosDocumento.xlsx` |
| 2026-03-12 | Nomes de pasta sem prefixo numérico (compatibilidade Python) |
| 2026-03-25 | Camada 1 aprovada: CD_CONTA tem prioridade, valor numérico é fallback |
| 2026-03-25 | Contas sem mapeamento (deliberadas): dívida MN/ME, imobilizado, Reserva de Capital — taxonomias CVM × Spread incompatíveis |
| 2026-03-25 | Receita (CVM 3.01) SEMPRE → "Vendas Mercado Externo" (convenção do João) |
| 2026-03-25 | L195 (Lucro Líquido) NÃO é escrito pelo pipeline — calculado por fórmula do Spread |

---

## Convenções do Negócio (não-inferíveis)

- João verifica manualmente: (i) Ativo = Passivo + PL, (ii) LL bate com DadosDocumento_tratado.xlsx, (iii) depreciação DFC bate, (iv) Dividendos e Aum./Red. Capital na DMPL
- Células **azuis** no DadosDocumento_tratado.xlsx = valores novos (eram 0 antes) → precisam verificação manual
- O `Spread Proxy.xlsx` é um template — João copia para cada empresa/período
- Convenção de pasta: `[Empresa] [Período]` (ex.: `Minerva 4T24`)

---

## Arquivo de Sessões

**Sessões 1-2 (2026-03-12, Gemini + Claude Sonnet 4.6):** Reorganização estrutural completa — `app_spread.py` (812 linhas) decomposto em pacotes `core/`, `processing/`, `app/`. Criados `CONTEXT.md` e `README.md`. DRE trimestral redesenhada: `DRE_MAP` offset-based → `DRE_SPREAD_MAP` label-based. Correção do grid de colunas (offset +2 → +3). Bug `wb.active` → seleção explícita de aba. Motor duplo xlwings+openpyxl corrigido.

**Sessão 3 (2026-03-25, Claude Sonnet 4.6):** Leitura do manual CVM e metadados de campos. Pipeline testado com Minerva 4T24 (38 matches) e 3T25 (32 matches). Descoberta: `ESCALA_MOEDA` não é validada; `VERSAO` incrementa em reapresentações; DMPL tem nomes de coluna sem espaço. Arquivos de referência movidos para `docs/`.

**Sessão 4 (2026-03-25, Claude Sonnet 4.6):** Camada 1 implementada — `core/conta_map.py` com 25+ entradas BP e DRE. `processing/spread.py` atualizado com `valor_corresp_por_conta()`. `processing/dmpl.py` reescrito com Camada 1 + fallback. Validação: 14 linhas Camada 1 + 24 Camada 2 = 38 total (sem regressão). Bug de sintaxe `dmpl.py:79` corrigido.

**Sessão 5 (2026-03-25, Claude Sonnet 4.6):** Validação Sabesp 4T24 — 19 HITS na Camada 1 (DRE completa + 8 BP), 14/14 pipeline completo ✓. Bug DFC corrigido: filtro `6.01` adicionado. Bug spread.py corrigido: Camada 1 antes de fórmula literal. `docs/cvm_account_dictionary.csv` adicionado (17.068 DS_CONTA únicas).

---

## Sugestões Pendentes de Avaliação

| Sugestão | Status |
|----------|--------|
| Reconhecer reapresentações (`VERSAO`) | Pendente — João quer consultar agente com expertise em contabilidade |
| Expandir para 4 anos simultâneos | Fase 1 já processa 3 períodos do DadosDocumento |
