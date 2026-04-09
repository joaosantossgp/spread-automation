# CONTEXT.md — Contexto Completo do Projeto

> Este documento é a referência principal para qualquer pessoa ou agente de IA
> que precise entender o projeto. Leia antes de modificar qualquer código.

---

## 1. O que é este projeto

**spread_automation** automatiza o preenchimento de planilhas de **Spread** (credit analysis)
usadas na análise de crédito de empresas brasileiras de capital aberto.

### Glossário de domínio

| Termo | Significado |
|-------|-------------|
| **CVM** | Comissão de Valores Mobiliários — órgão regulador do mercado de capitais brasileiro |
| **DFP** | Demonstrações Financeiras Padronizadas — relatório anual obrigatório enviado à CVM |
| **ITR** | Informações Trimestrais — relatório trimestral obrigatório enviado à CVM |
| **Spread** | Planilha de análise de crédito onde dados financeiros são organizados em formato bancário |
| **Spread Proxy** | A planilha Spread usada como template neste projeto |
| **Origem** | O arquivo `DadosDocumento.xlsx` baixado da CVM, com as demonstrações financeiras da empresa |
| **BP** | Balanço Patrimonial — ativo e passivo da empresa |
| **DRE** | Demonstração do Resultado do Exercício — receitas, custos e lucro |
| **DFC** | Demonstração dos Fluxos de Caixa — movimentação de entrada e saída de caixa |
| **DMPL** | Demonstração das Mutações do Patrimônio Líquido — variações no patrimônio (dividendos, aumentos de capital) |
| **Consolidado** | Dados que incluem controladas (grupo econômico completo) |
| **Individual** | Dados apenas da empresa-mãe (sem controladas) |
| **Período atual** | O exercício sendo inserido no Spread |
| **Período anterior** | O exercício que já existe no Spread (usado como referência) |

---

## 2. Pipeline do Usuário (ponta a ponta)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. DOWNLOAD                                                  │
│    Site da CVM → baixar ZIP do DFP ou ITR da empresa         │
│                                                              │
│ 2. RENOMEAR                                                  │
│    ZIP → "[Empresa] [Período].zip"                           │
│    Exemplo: "Minerva 4T24.zip"                               │
│    Formato de período:                                       │
│      • Anual: "Minerva 2024.zip"  (implica DFP)              │
│      • Trimestral: "Minerva 1T25.zip"  (implica ITR)         │
│                                                              │
│ 3. EXTRAIR                                                   │
│    Descompactar na pasta data/ do projeto                    │
│    → data/Minerva 4T24/                                      │
│      ├── DadosDocumento.xlsx   ← ORIGEM                      │
│      ├── Spread Proxy.xlsx     ← SPREAD (copiar template)    │
│      ├── *.xml                 ← metadados CVM (ignorados)   │
│      └── *.pdf                 ← DFP/ITR em PDF (ignorado)   │
│                                                              │
│ 4. PROCESSAR                                                 │
│    python main.py                                            │
│    → Selecionar Origem e Spread                              │
│    → Informar período, tipo, colunas src/dst                 │
│    → Clicar "Processar"                                      │
│                                                              │
│ 5. RESULTADO                                                 │
│    → "Spread Proxy 2024.xlsx" (novo arquivo com dados)       │
│    → "DadosDocumento_tratado.xlsx" (origem com destaques)    │
│       Verde = valor correspondido                            │
│       Azul  = valor novo (era 0 no período anterior)         │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Estrutura do `DadosDocumento.xlsx` (Origem CVM)

Este arquivo é gerado automaticamente pela CVM. Sua estrutura é **padronizada** para todas as empresas.

### Abas disponíveis (DFP anual — exemplo real Minerva 4T24)

| Aba | Usada pelo sistema? | Função |
|-----|---------------------|--------|
| `Composicao Capital` | ❌ | Composição acionária |
| `DF Ind Ativo` | ✅ (tipo=individual) | BP Individual — Ativo |
| `DF Ind Passivo` | ✅ (tipo=individual) | BP Individual — Passivo |
| `DF Ind Resultado Periodo` | ✅ (tipo=individual) | DRE Individual |
| `DF Ind Resultado Abrangente` | ❌ | Resultado abrangente |
| `DF Ind Fluxo de Caixa` | ✅ (tipo=individual) | DFC Individual |
| `DF Ind Valor Adicionado` | ❌ | DVA Individual |
| `DF Ind DMPL Ultimo` | ✅ (tipo=individual, anual) | DMPL do último exercício |
| `DF Ind DMPL Penultimo` | ❌ | DMPL do penúltimo exercício |
| `DF Ind DMPL Antepenultimo` | ❌ | DMPL do antepenúltimo exercício |
| `DF Cons Ativo` | ✅ (tipo=consolidado) | BP Consolidado — Ativo |
| `DF Cons Passivo` | ✅ (tipo=consolidado) | BP Consolidado — Passivo |
| `DF Cons Resultado Periodo` | ✅ (tipo=consolidado) | DRE Consolidado |
| `DF Cons Resultado Abrangente` | ❌ | Resultado abrangente consolidado |
| `DF Cons Fluxo de Caixa` | ✅ (tipo=consolidado) | DFC Consolidado |
| `DF Cons Valor Adicionado` | ❌ | DVA Consolidado |
| `DF Cons DMPL Ultimo` | ✅ (tipo=consolidado, anual) | DMPL Consolidado do último exercício |
| `DF Cons DMPL Penultimo` | ❌ | DMPL Consolidado do penúltimo |
| `DF Cons DMPL Antepenultimo` | ❌ | DMPL Consolidado do antepenúltimo |

### Colunas padrão das abas financeiras (BP, DRE, DFC)

| Coluna | Conteúdo |
|--------|----------|
| `Codigo Conta` | Código contábil CVM (ex.: `1.01`, `3.01`) |
| `Descricao Conta` | Nome da conta (ex.: "Receita de Venda de Bens e/ou Serviços") |
| `Valor Ultimo Exercicio` | Valor do período mais recente (ex.: 2024) |
| `Valor Penultimo Exercicio` | Valor do período anterior (ex.: 2023) |
| `Valor Antepenultimo Exercicio` | Valor de dois períodos atrás (ex.: 2022) |

### Colunas padrão das abas DMPL

| Coluna | Conteúdo |
|--------|----------|
| `CodigoConta` | Código contábil |
| `DescricaoConta` | Nome da conta |
| `Capital Social Integralizado` | Coluna de capital |
| `Patrimônio Líquido` | Coluna usada para Individual |
| `Patrimônio líquido Consolidado` | Coluna usada para Consolidado |

> **Para ITR (trimestral)**, os nomes das colunas mudam para:
> - `Valor Trimestre Atual` e `Valor Exercicio Anterior` (nas abas de BP)
> - `Valor Acumulado Atual Exercicio` e `Valor Acumulado Exercicio Anterior` (nas abas de DRE/DFC)

### Renomeação de abas e colunas (`processing/origin.py`)

O sistema renomeia as abas e colunas da Origem para nomes internos padronizados:

```
DF Cons Ativo              → "cons ativos"    (coluna: período atual/anterior/ant2)
DF Cons Passivo            → "cons passivos"
DF Cons Resultado Periodo  → "cons DRE"
DF Cons Fluxo de Caixa     → "cons DFC"
DF Cons DMPL Ultimo        → "cons DMPL"      (anual: "Ultimo", trimestral: "Atual")
```

---

## 4. Layout do Spread Proxy (aba "Entrada de Dados")

A aba "Entrada de Dados" tem 326 linhas e 12 colunas. O layout usa colunas fixas alternando entre colunas visíveis de dados e colunas ocultas de separação.

### Grid de colunas (CRÍTICO)

```
Col │ Letra │ Índice │ Hidden │ Função
────┼───────┼────────┼────────┼────────────────────────────
 1  │   A   │   0    │  Sim   │ (separador oculto)
 2  │   B   │   1    │  Não   │ RÓTULOS (nomes das linhas)
 3  │   C   │   2    │  Sim   │ (separador oculto)
 4  │   D   │   3    │  Não   │ DADOS ANUAIS — período mais antigo
 5  │   E   │   4    │  Sim   │ (metadados ocultos: data, moeda, câmbio)
 6  │   F   │   5    │  Não   │ DADOS ANUAIS
 7  │   G   │   6    │  Sim   │ (separador oculto)
 8  │   H   │   7    │  Não   │ DADOS ANUAIS
 9  │   I   │   8    │  Sim   │ (separador oculto)
10  │   J   │   9    │  Não   │ DADOS ANUAIS — período mais recente
11  │   K   │  10    │  Sim   │ (separador oculto)
12  │   L   │  11    │  Não   │ BALANCETE / TRIMESTRAL
```

> **IMPORTANTE para agentes de IA**: As colunas de dados são **D, F, H, J** (anuais)
> e **L** (trimestral). As colunas ímpares (A, C, E, G, I, K) são **ocultas** e
> **nunca devem ser usadas como destino**. O código define:
> ```python
> COLUNAS_ANUAIS = ["D", "F", "H", "J"]
> COLUNA_TRIMESTRAL = "L"
> ```

### Progressão de preenchimento

O Spread é preenchido da esquerda para a direita ao longo dos anos:
- Ano 1 → coluna D | Ano 2 → coluna F | Ano 3 → coluna H | Ano 4 → coluna J
- Balancete trimestral → coluna L (sempre)

### Zona de metadados (linhas 1–26)

| Linha | Coluna B | Conteúdo |
|-------|----------|----------|
| 3 | `Anos` | Data do período em cada coluna de dados (ex.: `31/12/2023`) |
| 4 | `Número de meses do Balanço` | Meses cobertos (12 = anual, 3/6/9 = trimestral) |
| 5 | `Nome do Arquivo:` | Nome do arquivo de origem |
| 6 | `Auditado por` | Nome da auditoria |
| 14 | `Analista de Crédito:` | Nome do analista |
| 22–24 | Câmbio | Câmbio final e médio |
| 26 | — | Repetição da data (fórmula `=IF(E3<>"",E3,"")`) |

### Zona de dados (linhas 27–326)

A coluna **B** contém os rótulos das linhas. As colunas D/F/H/J/L contêm os valores financeiros.

**Estrutura das seções no Spread:**

| Linhas | Seção | Origem CVM |
|--------|-------|------------|
| 27–130 (aprox.) | **Balanço Patrimonial** (Ativo + Passivo) | `DF Cons/Ind Ativo` + `DF Cons/Ind Passivo` |
| 149–180 (aprox.) | **DRE** (Demonstração de Resultado) | `DF Cons/Ind Resultado Periodo` |
| 180–200 (aprox.) | **DFC** (Fluxo de Caixa) | `DF Cons/Ind Fluxo de Caixa` |
| 200–220 (aprox.) | **Mutações PL / Dividendos** | `DF Cons/Ind DMPL` |

### Linhas especiais (hardcoded no código)

| Linha | Rótulo no Spread | O que o sistema faz | Módulo |
|-------|------------------|----------------------|--------|
| **199** | `Amortização Total` | Insere soma negativa de depreciação + amortização da DFC | `processing/dfc.py` |
| **209** | `Dividendos Pagos (Res. + P.L.) (-)` | Insere soma **positiva** de dividendos/JCP da DMPL | `processing/dmpl.py` |
| **210** | `I.R. no P.L. (-)` | Insere soma **negativa** de dividendos/JCP da DMPL | `processing/dmpl.py` |
| **213** | `Reavaliação / (Reversão) no Imobilizado` | Insere aumentos de capital da DMPL | `processing/dmpl.py` |

> **IMPORTANTE**: Estas linhas são **excluídas** da varredura padrão (`SKIP = {199, 209, 210, 213}`
> em `processing/spread.py`) e preenchidas separadamente pelas funções especializadas.

### Parâmetros hardcoded na GUI (`app/gui.py`)

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| `start_row` | `27` | Primeira linha de dados no Spread (também usada para escanear rótulos DRE) |

---

## 5. Como o processamento funciona

### Etapa 1: Preparação da Origem (`processing/origin.py`)

- Lê o `DadosDocumento.xlsx`
- Seleciona apenas as abas relevantes (Cons ou Ind, conforme escolha do usuário)
- Renomeia colunas de valor para o nome do período (ex.: `"Valor Ultimo Exercicio"` → `"2024"`)
- Salva como `DadosDocumento_tratado.xlsx`

### Etapa 2: Varredura do Spread (`processing/spread.py`)

Para cada linha do Spread (começando em `start_row`), a função `atualizar_ws` executa
**matching híbrido em dois estágios**:

#### Camada 1 — Matching por CD_CONTA CVM (prioritário)

1. **Lê o rótulo** da coluna B (ex.: `"CMV Total"`)
2. **Consulta `CONTA_SPREAD_MAP`** em `core/conta_map.py` → obtém lista de CD_CONTA (ex.: `["3.02"]`)
3. **Soma os valores** dessas contas na coluna `atual` das abas da Origem
4. Se resultado ≠ 0 → usa esse valor (determinístico, sem ambiguidade)

```python
# core/conta_map.py — exemplos de mapeamentos validados
CONTA_SPREAD_MAP = {
    "Disponibilidades":          ["1.01.01", "1.01.02"],   # Caixa + Aplic.Fin. CP
    "CMV Total":                 ["3.02"],                  # Custo dos Bens/Serviços
    "Lucro Bruto":               ["3.03"],
    "Despesas Financeiras Caixa":["3.06.02"],
    "Imposto de Renda":          ["3.08"],                  # IR + CS (corrente+diferido)
    # ... 25+ entradas para BP e DRE
}
```

#### Camada 2 — Matching por Valor Numérico (fallback)

Acionada quando Camada 1 retorna `None` (rótulo não mapeado ou resultado zero):

1. **Pega o número** na coluna-fonte do Spread (período anterior)
2. **Procura na coluna `ant`** da Origem o mesmo valor numérico
3. **Retorna o valor** na coluna `atual` da mesma linha

**Por que ainda existe a Camada 2:**
- Dívida bancária: CVM classifica por instrumento (Empréstimos/Debêntures), Spread por moeda (MN/ME) → taxonomias incompatíveis
- Imobilizado: sub-linhas bancárias sem equivalente CVM direto
- Linhas não mapeadas: qualquer conta que não esteja no `CONTA_SPREAD_MAP`

**Tratamento de tipos de célula:**
- **Valor numérico puro**: Camada 1 → Camada 2
- **Fórmula literal** (`=123456+789012`): substitui cada número via Camada 2
- **Fórmula complexa** (`=SUM(H28:H31)`): desloca referências de coluna (H→I) E substitui números literais

**Critério de parada**: a varredura para após 30 linhas vazias consecutivas.

### Etapa 3: DRE Manual (`processing/dre.py`)

Só para **períodos trimestrais**. A DRE trimestral tem mapeamento especial via `DRE_SPREAD_MAP`
(definido em `core/utils.py`). O fluxo usa **label-based matching** — escaneia a coluna B do
Spread para encontrar as linhas pelos rótulos, sem depender de offsets fixos:

```python
# core/utils.py
DRE_SPREAD_MAP = {
    "Receita de Venda de Bens e/ou Serviços":             "Vendas Líquidas",
    "Custo dos Bens e/ou Serviços Vendidos":               "CMV Total",
    "Outras Despesas Operacionais":                         "Outras Despesas Operacionais",
    "Perdas pela Não Recuperabilidade de Ativos":           "Outras Despesas Operacionais",  # somado
    # ...
}
```

Múltiplas contas CVM podem apontar para o mesmo rótulo do Spread — os valores são **somados**.
Isso permite que "Perdas pela Não Recuperabilidade de Ativos" (CVM 3.04.03) seja automaticamente
incluída em "Outras Despesas Operacionais" sem row dedicada no Spread.

### Etapa 4: DFC — Depreciação (`processing/dfc.py`)

Filtra linhas da DFC que contenham "deprecia", "amortiza" ou "exaustão", soma os valores (tornando negativos), e insere na **linha 199** do Spread.

**IMPORTANTE — filtro por seção CVM**: antes de aplicar o regex, o código restringe a busca às linhas com `Codigo Conta` começando com `"6.01"` (Atividades Operacionais). Sem esse filtro, "Amortizações" de pagamentos de empréstimos (seção 6.03 — Atividades de Financiamento) seriam incorretamente somadas. Bug confirmado com Sabesp 4T24 (`6.03.02 "Amortizações"` = -2,246,263).

### Etapa 5: DMPL — Dividendos e Capital (`processing/dmpl.py`)

Também usa matching híbrido (Camada 1 → Camada 2):

- **Camada 1**: busca por `CD_CONTA` exato (`5.04.06` = Dividendos, `5.04.07` = JCP, `5.04.01` = Aumentos de Capital)
- **Camada 2 fallback**: busca por texto na `DescricaoConta` se os códigos não forem encontrados

Inserção final:
- Dividendos + JCP negativos → **linha 210**
- Dividendos + JCP positivos → **linha 209**
- Aumentos de capital → **linha 213**

### Etapa 6: Destaques Visuais (`processing/highlights.py`)

Na `DadosDocumento_tratado.xlsx`:
- **Verde** (`#CCFFCC`): valores que foram correspondidos e inseridos no Spread
- **Azul** (`#99CCFF`): valores que são novos (eram 0 no período anterior e agora são ≠ 0)

### Motor duplo: xlwings vs openpyxl

O pipeline tenta executar com **xlwings** primeiro (atualização ao vivo no Excel aberto).
Se falhar (Excel não aberto, Windows sem xlwings, etc.), executa com **openpyxl** (fallback offline).

> **Nota**: O pipeline tenta xlwings primeiro; se bem-sucedido, **não roda** o openpyxl. O fallback
> só ocorre quando xlwings falha (Excel não aberto, ambiente headless, etc.).

---

## 6. Lógica de Períodos (`core/utils.py → periodos()`)

| Input | `atual` | `ant` | `ant2` | `is_trim` |
|-------|---------|-------|--------|-----------|
| `"2024"` | `"2024"` | `"2023"` | `"2022"` | `False` |
| `"2023"` | `"2023"` | `"2022"` | `"2021"` | `False` |
| `"4T24"` | `"4T24"` | `"4T23"` | `"4T22"` | `True` |
| `"1T25"` | `"1T25"` | `"1T24"` | `"1T23"` | `True` |

A flag `is_trim` afeta:
- Quais colunas são lidas na Origem (diferentes nomes de cabeçalho para anual vs trimestral)
- Se a DRE é inserida manualmente via `DRE_MAP` (só trimestral)
- Qual aba de DMPL é selecionada (`"Ultimo"` para anual, `"Atual"` para trimestral)

---

## 7. Arquitetura de Módulos

```
core/utils.py          ← funções puras, zero dependências internas
     │
     ├── processing/origin.py      ← prepara DadosDocumento
     ├── processing/spread.py      ← varredura principal (depende de core)
     ├── processing/dre.py         ← DRE manual (depende de core)
     ├── processing/dfc.py         ← depreciação DFC (depende de core)
     ├── processing/dmpl.py        ← dividendos DMPL (depende de core)
     ├── processing/highlights.py  ← destaques visuais (depende de core)
     └── processing/pipeline.py    ← orquestra tudo (depende de todos acima)
              │
              └── app/gui.py       ← interface gráfica (depende de pipeline)
                       │
                       └── main.py ← ponto de entrada
```

---

## 8. Riscos e Pontos de Atenção

| Risco | Severidade | Detalhes |
|-------|-----------|----------|
| Linhas hardcoded (199, 209, 210, 213) | ⚠️ Alta | Se o template do Spread mudar, essas linhas precisam ser atualizadas manualmente no código |
| `DRE_SPREAD_MAP` rótulos fixos | ⚠️ Baixa | Se o rótulo de uma linha mudar no Spread (ex: "CMV Total" → "CMV Caixa"), atualizar o dict em `core/utils.py` |
| Pipeline duplo xlwings+openpyxl | ⚠️ Média | O fallback openpyxl sempre executa; pode causar gravações duplicadas |
| Sem testes automatizados | ⚠️ Alta | Qualquer mudança pode quebrar silenciosamente |
| Sem validação de entrada na GUI | ⚠️ Baixa | Período inválido gera exceção genérica |

---

## 9. Orientações para Manutenção e Agentes de IA

### Antes de modificar qualquer código:
1. Entenda qual **demonstrativo financeiro** (BP, DRE, DFC, DMPL) está envolvido
2. Verifique se a linha no Spread corresponde ao rótulo esperado
3. Verifique se `is_trim` afeta o comportamento

### Adicionando um novo demonstrativo:
1. Crie `processing/novo_demonstrativo.py` seguindo o padrão de `dfc.py`
2. Adicione a chamada em `processing/pipeline.py`
3. Se necessário, adicione a linha ao `SKIP` set em `processing/spread.py`
4. Atualize este `CONTEXT.md`

### Adicionando uma nova empresa:
1. Baixe o ZIP da CVM, renomeie, extraia em `data/`
2. Copie o template `Spread Proxy.xlsx` para dentro da pasta
3. Execute o processamento normalmente

### Imports:
Sempre importar via pacote: `from core.utils import normaliza_num`

### Dependências:

| Pacote | Tipo | Uso |
|--------|------|-----|
| `pandas` | Core | Leitura de DataFrames do Excel |
| `openpyxl` | Core | Leitura/escrita de `.xlsx` com fórmulas e formatação |
| `customtkinter` | Core | Interface gráfica |
| `xlwings` | Opcional | Atualização ao vivo do Excel aberto (somente Windows) |

---

## 10. Documentos de Referência CVM (`docs/`)

Movidos para `docs/` para organização:

| Arquivo | Conteúdo |
|---------|----------|
| `docs/manual-de-envio-de-informacoes-periodicas-e-eventuais.pdf` | Manual oficial CVM (SEP, ago/2025): regras de envio de ITR/DFP via E-NET, categorias de documentos, prazos, reapresentações |
| `docs/meta_dfp_cia_aberta_txt/` | Schemas dos campos dos CSVs de dados abertos CVM (BPA, BPP, DRE, DFC_MD, DFC_MI, DMPL, DVA, DRA) |
| `docs/plano-contas-fixas-DFP/` | Plano de Contas Fixas DFP – ENET 10.0: três planilhas (Comerciais/Industriais, Inst.Financeiras, Seguradoras) com todos os CD_CONTA fixos (`ST_CONTA_FIXA=S`) — **fonte primária da Camada 1** |
| `docs/oc-sep-0621.pdf` | Ofício-Circular CVM/SEP nº 6/2021: aviso de migração para nova plataforma de envio. Não é spec técnica de contas. |
| `docs/Manual XML ITR v2.xls` | Leiaute do Formulário DFP/ITR – ENET (Manual XML v2, set/2011): define campos XML dos formulários, incluindo `IndicadorContaFixa` (= `ST_CONTA_FIXA`) e estrutura DMPL |
| `docs/cvm_account_dictionary.csv` | Dicionário com 17.068 nomes únicos de `DS_CONTA` vistos em todos os DFPs/ITRs CVM, agrupados por `statement_type` (BPA/BPP/DRE/DFC). Sem CD_CONTA. Útil para diagnóstico de regex e entendimento de variações de nomenclatura por setor. |

### Campos relevantes dos CSVs abertos CVM

Os arquivos em `docs/meta_dfp_cia_aberta_txt/` descrevem os campos dos CSVs baixáveis em massa do portal de dados abertos CVM. Estes são **diferentes** do `DadosDocumento.xlsx` (arquivo da empresa individual), mas a estrutura conceitual é a mesma.

| Campo CSV | Equivalente no DadosDocumento.xlsx | Observação |
|-----------|-------------------------------------|------------|
| `CD_CONTA` | `Codigo Conta` | Código hierárquico da conta (ex: `1.01`, `3.04.02`) |
| `DS_CONTA` | `Descricao Conta` | Descrição textual |
| `VL_CONTA` | `Valor Ultimo Exercicio` etc. | decimal(29,10) |
| `ORDEM_EXERC` | (coluna de período no xlsx) | `ULTIMO` / `PENULTIMO` / `ANTEPENULTIMO` |
| `ST_CONTA_FIXA` | — | `S` = conta fixa (sempre presente); `N` = conta discricionária |
| `ESCALA_MOEDA` | `Precisao` (coluna extra) | Ex: `"Mil"` — o pipeline não valida se a escala muda entre períodos |
| `GRUPO_DFP` | Nome da aba | Grupo/agregação da demonstração |
| `VERSAO` | — | Versão do documento; incrementa em reapresentações |
| `COLUNA_DF` | Colunas do DMPL | Apenas no DMPL: identifica a coluna de patrimônio |

> **Atenção**: Se uma empresa mudar `ESCALA_MOEDA` entre períodos (ex: de "Unidade" para "Mil"),
> o matching por valor falhará silenciosamente. O pipeline assume escala consistente.
