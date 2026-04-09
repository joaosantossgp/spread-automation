# core/conta_map.py — Camada 1: mapeamento rótulo do Spread → CD_CONTA CVM
#
# Fontes usadas para construir este mapa:
#   1. Plano de Contas Fixas DFP – ENET 10.0
#      (docs/plano-contas-fixas-DFP/Plano de Contas - DFP - Empresas Comerciais...)
#   2. Dicionário de Dados DFP (docs/meta_dfp_cia_aberta_txt/)
#   3. Leiaute do Formulário DFP – ENET (Manual XML ITR v2)
#   4. Ofício-Circular CVM/SEP nº 6/2021
#   5. Referência teórica: /financial-statements (ASC 220/210/230 + CPC equivalentes)
#
# CONVENÇÕES
# ----------
# • Cada chave é o rótulo EXATO da coluna B do Spread (case-sensitive, strip aplicado).
# • Cada valor é a lista de CD_CONTA CVM cujos valores devem ser SOMADOS para preencher
#   essa linha do Spread.
# • Entradas incluídas apenas se:
#   (a) validadas contra dados reais da Minerva 4T24 / 3T25, OU
#   (b) semanticamente óbvias no plano de contas fixas CVM.
# • Linhas de seção (totais com fórmulas, ex: "AC", "ATIVO TOTAL") NÃO entram aqui —
#   essas células continuam sendo tratadas por shift_formula em spread.py.
# • Linhas com forte ambiguidade semântica (dívida bancária, PL com nomenclatura
#   diferente do CVM) são omitidas deliberadamente — caem para Camada 2 (valor numérico).
#
# ESTRUTURA DO PLANO DE CONTAS FIXAS CVM (para referência)
# ---------------------------------------------------------
# 1       Ativo Total
# 1.01    Ativo Circulante
# 1.02    Ativo Não Circulante
# 2       Passivo Total
# 2.01    Passivo Circulante
# 2.02    Passivo Não Circulante
# 2.03    Patrimônio Líquido Consolidado
# 3.01    Receita de Venda de Bens e/ou Serviços
# 3.02    Custo dos Bens e/ou Serviços Vendidos
# 3.03    Resultado Bruto
# 3.04    Despesas/Receitas Operacionais (pai — não usar, usar sub-contas)
# 3.06    Resultado Financeiro (pai — não usar, usar sub-contas)
# 3.08    Imposto de Renda e CS sobre o Lucro
# 5.04    Transações de Capital com os Sócios (DMPL)
# 6.01    Caixa Líquido Atividades Operacionais (apenas 10 contas fixas na DFC)
#
# NOTA DFC: A DFC tem apenas 10 contas fixas de alto nível (6.01–6.05.02).
# Sub-itens como Depreciação e Amortização NÃO são contas fixas — variam por empresa.
# Por isso a DFC é tratada por busca textual em dfc.py, não por Camada 1.

CONTA_SPREAD_MAP: dict[str, list[str]] = {

    # =========================================================================
    # BALANÇO PATRIMONIAL — ATIVO CIRCULANTE
    # /financial-statements: Current Assets — more liquid first
    # =========================================================================

    # Caixa e Equivalentes + Aplicações Financeiras CP
    # Validado: 1.01.01(Caixa)+1.01.02(Aplic.Fin.) = Disponibilidades no Spread
    "Disponibilidades":                 ["1.01.01", "1.01.02"],

    # Clientes CP (MN = Moeda Nacional — Minerva separa MN/ME)
    # Validado: 1.01.03.01 = Clientes
    "Dupls Receber CP MN":              ["1.01.03.01"],

    # Estoques operacionais CP — Minerva só tem estoques em MN no CVM consolidado
    # Validado: 1.01.04 = Estoques
    "Estoques Operacionais CP MN":      ["1.01.04"],

    # Ativos Biológicos CP (empresas agroindustriais, ex: Minerva com gado)
    # 1.01.05 = Ativos Biológicos (fixo no plano CVM)
    "Ativos Biológicos CP":             ["1.01.05"],

    # Tributos a Recuperar CP
    # Validado: 1.01.06
    "Impostos a Recuperar CP":          ["1.01.06"],

    # Despesas Antecipadas CP
    "Desp. Antecipadas":                ["1.01.07"],

    # =========================================================================
    # BALANÇO PATRIMONIAL — ATIVO REALIZÁVEL A LONGO PRAZO (RLP)
    # /financial-statements: Non-Current Assets
    # =========================================================================

    # Aplicações Financeiras LP (1.02.01.01 + 1.02.01.02 = valor justo + custo amortizado)
    "Disponibilidades LP":              ["1.02.01.01", "1.02.01.02"],

    # Clientes LP
    "Dupls Receber LP MN":              ["1.02.01.03.01"],
    "Dupls Receber LP ME":              ["1.02.01.03.02"],

    # Tributos Diferidos (IR diferido ativo)
    # Nota: zero para Minerva 4T24 — conta existe mas está vazia
    "Crédito Tributário I.R. LP":       ["1.02.01.06"],

    # Créditos com Partes Relacionadas LP
    "C/C Coligadas RLP MN":             ["1.02.01.08.01"],  # Créditos com Coligadas

    # =========================================================================
    # BALANÇO PATRIMONIAL — ATIVO PERMANENTE
    # /financial-statements: Non-Current Assets (PPE, Intangibles, Goodwill)
    # =========================================================================
    # NOTA: "Investimentos" omitido — CVM 1.02.02 = apenas investimentos financeiros
    # (propriedades para investimento), mas o Spread inclui mais itens. Cai p/ Camada 2.
    #
    # NOTA: "Imobilizado" omitido — é cabeçalho de seção no Spread (sem valor direto),
    # e o CVM 1.02.03 já é líquido de depreciação. Sub-linhas do Spread (terrenos,
    # edificios) são específicas do cliente. Cai p/ Camada 2.
    #
    # NOTA: "Diferido Normal" / "(-) Amortização Acumulada Dif. Normal" omitidos —
    # o CVM mostra 1.02.04 já líquido. As linhas brutas do Spread são decomposições
    # bancárias sem equivalente CVM direto.

    # =========================================================================
    # BALANÇO PATRIMONIAL — PASSIVO CIRCULANTE
    # /financial-statements: Current Liabilities
    # =========================================================================
    # NOTA IMPORTANTE sobre dívida bancária:
    # O Spread separa "Bancos CP MN" / "Bancos CP ME" por MOEDA.
    # O CVM separa por INSTRUMENTO (2.01.04.01=Empréstimos, 2.01.04.02=Debêntures).
    # Não há como somar apenas os instrumentos BRL sem conhecer a moeda de cada um.
    # → Linhas de dívida omitidas desta Camada 1; caem para Camada 2.
    #
    # Fornecedores Nacionais CP
    "Fornecedores Operac. CP MN":       ["2.01.02.01"],

    # Obrigações Sociais e Trabalhistas
    "Despesas Provisionadas":           ["2.01.01"],

    # IR a pagar CP (Corrente)
    "Provisão IR/CS":                   ["2.01.03.01.01"],  # IR e CS a pagar

    # Dividendos e JCP a pagar CP
    "Dividendos a Pagar":               ["2.01.05.02.01", "2.01.05.02.02"],

    # =========================================================================
    # BALANÇO PATRIMONIAL — PASSIVO NÃO CIRCULANTE (ExLP)
    # /financial-statements: Non-Current Liabilities
    # =========================================================================
    # (mesma limitação de dívida — omitido)

    # Tributos Diferidos Passivo
    "Provisão IR/CS LP":                ["2.02.03.01"],

    # =========================================================================
    # BALANÇO PATRIMONIAL — PATRIMÔNIO LÍQUIDO
    # /financial-statements: Stockholders' Equity
    # =========================================================================
    # NOTA: A nomenclatura do Spread para PL diverge do CVM em alguns casos.
    # Incluído apenas o que foi validado ou é semanticamente inequívoco.
    #
    # Participação dos acionistas não controladores
    "Participação dos Minoritários":    ["2.03.09"],

    # =========================================================================
    # DRE — DEMONSTRAÇÃO DO RESULTADO
    # Todas as 28 contas fixas CVM para DRE são bem definidas.
    # /financial-statements: Income Statement by function (COGS, G&A, S&M, etc.)
    # Fonte: Plano de Contas Fixas — DF Cons. - Resultado Período (28 contas)
    # =========================================================================

    # Receita Total (3.01) — conforme convenção do Spread:
    # CVM 3.01 vai sempre para "Vendas Mercado Externo" (sub-linha de receita externa).
    # Validado na Sessão 2 e confirmado: João usa essa linha como destino da receita total.
    "Vendas Mercado Externo":           ["3.01"],

    # CMV Total = CVM 3.02 (Custo dos Bens e/ou Serviços Vendidos)
    # Inclui todas as sub-contas (CMV variável, fixo, depreciação inclusa no custo).
    # Validado como correto: CVM 3.02 = -27.065.603 para Minerva 2024.
    "CMV Total":                        ["3.02"],

    # Lucro Bruto = CVM 3.03 (Resultado Bruto = 3.01 + 3.02)
    # É um total calculado no CVM também; incluído pois o Spread tem uma linha para ele.
    "Lucro Bruto":                      ["3.03"],

    # Despesas/Receitas Operacionais (sub-contas de 3.04)
    "Despesas de Vendas":               ["3.04.01"],
    "Despesas Administrativas":         ["3.04.02"],

    # "Perdas NRA" (3.04.03) é somada em "Outras Despesas Operacionais" (3.04.05)
    # conforme decisão da Sessão 2 (equivalente ao DRE_SPREAD_MAP trimestral).
    "Outras Despesas Operacionais":     ["3.04.05", "3.04.03"],

    "Outras Receitas Operacionais":     ["3.04.04"],
    "Equivalência Patrimonial":         ["3.04.06"],

    # Resultado Financeiro (sub-contas de 3.06)
    # /financial-statements: Other Income (Expense) — Interest income/expense
    "Receitas Financeiras Caixa":       ["3.06.01"],
    "Despesas Financeiras Caixa":       ["3.06.02"],

    # Imposto de Renda + Contribuição Social (total 3.08)
    # Inclui 3.08.01 (corrente) + 3.08.02 (diferido) via conta pai.
    "Imposto de Renda":                 ["3.08"],

    # =========================================================================
    # DMPL — contas de referência para dmpl.py
    # Estas linhas estão no SKIP set de spread.py e NÃO passam por atualizar_ws.
    # São tratadas por processing/dmpl.py via lookup por CD_CONTA (ver abaixo).
    # Incluídas aqui apenas como documentação da correspondência.
    # =========================================================================
    # L209 "Dividendos Pagos (Res. + P.L.) (-)" → 5.04.06 (positivos da DMPL)
    # L210 "I.R. no P.L. (-)"                   → 5.04.07 (JCP negativos) + 5.04.06 (negativos)
    # L213 "Reavaliação / (Reversão) no Imob."  → 5.04.01 (Aumentos de Capital)
}

# ---------------------------------------------------------------------------
# Códigos DMPL usados por processing/dmpl.py (Camada 1 para DMPL)
# ---------------------------------------------------------------------------
# Contas fixas do plano CVM para DMPL (DF Cons. - DMPL):
DMPL_DIVIDENDOS_CODES: list[str] = ["5.04.06"]          # Dividendos
DMPL_JCP_CODES:        list[str] = ["5.04.07"]          # Juros sobre Capital Próprio
DMPL_CAPITAL_CODES:    list[str] = ["5.04.01"]          # Aumentos de Capital
