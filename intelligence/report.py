"""
intelligence/report.py — Geração de Relatório Executivo em PDF (FPDF2).
"""
import os
import re
from datetime import datetime
from fpdf import FPDF
from core.utils import fmt, MESES_PT
from intelligence.rules import calcular_50_30_20


def _clean_text(txt: str) -> str:
    """Remove emojis e caracteres fora do Latin-1 para evitar erros na fonte padrão do FPDF."""
    if not txt:
        return ""
    # Remove caracteres fora do range Latin-1 (ex: emojis)
    cleaned = "".join(ch for ch in str(txt) if ord(ch) <= 255)
    return re.sub(r"\s+", " ", cleaned).strip()


class RelatorioPDF(FPDF):
    def header(self):
        # Banner superior escuro elegante
        self.set_fill_color(18, 22, 32)
        self.rect(0, 0, 210, 28, "F")
        # Linha de destaque verde/azul
        self.set_fill_color(0, 212, 170)
        self.rect(0, 28, 210, 1.5, "F")

        self.set_y(8)
        self.set_font("helvetica", "B", 16)
        self.set_text_color(240, 242, 245)
        self.cell(0, 8, "RELATORIO EXECUTIVO FINANCEIRO", border=False, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "", 9)
        self.set_text_color(139, 149, 165)
        self.cell(0, 5, f"Controle Pessoal  |  Emitido em {datetime.now().strftime('%d/%m/%Y as %H:%M')}", align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 125, 135)
        self.cell(0, 10, f"Financeiro - Controle Pessoal  |  Pagina {self.page_no()}", align="C")


def _section_title(pdf: FPDF, title: str):
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(18, 22, 32)
    pdf.set_fill_color(240, 244, 248)
    pdf.cell(0, 8, f"  {_clean_text(title)}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


def gerar_relatorio_pdf(conn, mes_sel, ano_sel, prefixo_mes, rec_mes, desp_mes, simples_mes, balanco_mes, score):
    """
    Gera um arquivo PDF executivo com o relatório completo do mês selecionado.
    Retorna o caminho absoluto para o arquivo gerado.
    """
    pdf = RelatorioPDF()
    pdf.add_page()

    nome_mes = MESES_PT[mes_sel]
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(30, 35, 45)
    pdf.cell(0, 8, _clean_text(f"Competencia: {nome_mes} / {ano_sel}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── 1. Cards de Resumo Geral (KPIs) ──────────────────────────────────────
    _section_title(pdf, "1. Resumo Executivo do Mes")

    kpis = [
        ("Receitas Totais", fmt(rec_mes), (0, 150, 110)),
        ("Despesas Totais", fmt(desp_mes), (210, 45, 75)),
        ("Imposto / Simples", fmt(simples_mes), (215, 135, 0)),
        ("Balanco Liquido", fmt(balanco_mes), (0, 150, 110) if balanco_mes >= 0 else (210, 45, 75)),
        ("Score de Saude", f"{score}/100", (45, 110, 220)),
    ]

    col_w = 38
    y_start = pdf.get_y()
    x_start = pdf.get_x()
    for i, (label, val, color) in enumerate(kpis):
        x = x_start + i * col_w
        pdf.set_xy(x, y_start)
        pdf.set_draw_color(220, 225, 230)
        pdf.set_fill_color(250, 251, 253)
        pdf.rect(x, y_start, col_w - 2, 18, "DF")
        pdf.set_xy(x + 2, y_start + 2.5)
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(100, 110, 125)
        pdf.cell(col_w - 6, 4, _clean_text(label), new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(x + 2, y_start + 9)
        pdf.set_font("helvetica", "B", 9.5)
        pdf.set_text_color(*color)
        pdf.cell(col_w - 6, 6, _clean_text(val))

    pdf.set_y(y_start + 23)

    # ── 2. Regra 50-30-20 ────────────────────────────────────────────────────
    _section_title(pdf, "2. Distribuicao Pela Regra 50-30-20")
    regra = calcular_50_30_20(conn, prefixo_mes, rec_mes)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(230, 235, 242)
    pdf.set_text_color(40, 45, 55)
    pdf.cell(65, 7, "  Pilar", fill=True)
    pdf.cell(45, 7, "Valor Gasto", fill=True)
    pdf.cell(40, 7, "% Real", fill=True)
    pdf.cell(40, 7, "% Ideal", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 9)
    for pilar_nome, chave in [("Necessidades Essenciais", "necessidades"), ("Desejos & Estilo de Vida", "desejos"), ("Prioridades & Investimentos", "prioridades")]:
        d = regra[chave]
        pdf.cell(65, 6.5, f"  {pilar_nome}", border="B")
        pdf.cell(45, 6.5, _clean_text(fmt(d["valor"])), border="B")
        pdf.cell(40, 6.5, f"{d['pct']:.1f}%", border="B")
        pdf.cell(40, 6.5, f"{d['ideal']}%", border="B", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # ── 3. Despesas por Categoria ────────────────────────────────────────────
    _section_title(pdf, "3. Despesas por Categoria")

    cats = conn.execute(
        "SELECT c.nome, SUM(t.valor) as total, COUNT(t.id) as qtd FROM transacoes t "
        "LEFT JOIN categorias c ON t.categoria_id = c.id "
        "WHERE t.tipo='despesa' AND COALESCE(t.is_transferencia,0)=0 AND t.data LIKE ? "
        "GROUP BY c.nome ORDER BY total DESC",
        (f"{prefixo_mes}%",)
    ).fetchall()

    if not cats:
        pdf.set_font("helvetica", "I", 9.5)
        pdf.set_text_color(100, 105, 115)
        pdf.cell(0, 8, "Nenhuma despesa registrada neste mes.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(230, 235, 242)
        pdf.set_text_color(40, 45, 55)
        pdf.cell(75, 7, "  Categoria", fill=True)
        pdf.cell(30, 7, "Lancamentos", fill=True)
        pdf.cell(45, 7, "Total", fill=True)
        pdf.cell(40, 7, "% das Despesas", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", "", 9)
        for idx, row in enumerate(cats):
            cat_nome = _clean_text(row[0] if row[0] else "Sem Categoria")
            total_cat = row[1] or 0
            qtd_cat = row[2] or 0
            pct_desp = (total_cat / desp_mes * 100) if desp_mes > 0 else 0
            if idx % 2 == 1:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.cell(75, 6.5, f"  {cat_nome}", fill=True, border="B")
            pdf.cell(30, 6.5, str(qtd_cat), fill=True, border="B")
            pdf.cell(45, 6.5, _clean_text(fmt(total_cat)), fill=True, border="B")
            pdf.cell(40, 6.5, f"{pct_desp:.1f}%", fill=True, border="B", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # ── 4. Top 5 Maiores Despesas ────────────────────────────────────────────
    _section_title(pdf, "4. Top 5 Maiores Despesas do Mes")

    top5 = conn.execute(
        "SELECT t.descricao, t.valor, t.data, c.nome FROM transacoes t "
        "LEFT JOIN categorias c ON t.categoria_id = c.id "
        "WHERE t.tipo='despesa' AND COALESCE(t.is_transferencia,0)=0 AND t.data LIKE ? "
        "ORDER BY t.valor DESC LIMIT 5",
        (f"{prefixo_mes}%",)
    ).fetchall()

    if not top5:
        pdf.set_font("helvetica", "I", 9.5)
        pdf.set_text_color(100, 105, 115)
        pdf.cell(0, 8, "Nenhuma despesa registrada.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(230, 235, 242)
        pdf.set_text_color(40, 45, 55)
        pdf.cell(80, 7, "  Descricao", fill=True)
        pdf.cell(45, 7, "Categoria", fill=True)
        pdf.cell(30, 7, "Data", fill=True)
        pdf.cell(35, 7, "Valor", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", "", 9)
        for i, row in enumerate(top5):
            desc_clean = _clean_text(row[0])[:40]
            cat_clean = _clean_text(row[3] or "Geral")[:22]
            pdf.cell(80, 6.5, f"  {i+1}. {desc_clean}", border="B")
            pdf.cell(45, 6.5, cat_clean, border="B")
            pdf.cell(30, 6.5, _clean_text(row[2]), border="B")
            pdf.cell(35, 6.5, _clean_text(fmt(row[1])), border="B", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # ── 5. Saldos das Contas ─────────────────────────────────────────────────
    _section_title(pdf, "5. Posicao Atual das Contas")
    contas_rows = conn.execute("""
        SELECT c.nome, c.tipo,
               COALESCE(c.saldo_inicial, 0) +
               COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='receita'), 0) -
               COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='despesa'), 0) as saldo
        FROM contas c ORDER BY c.id
    """).fetchall()

    if contas_rows:
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(230, 235, 242)
        pdf.set_text_color(40, 45, 55)
        pdf.cell(85, 7, "  Conta", fill=True)
        pdf.cell(60, 7, "Tipo", fill=True)
        pdf.cell(45, 7, "Saldo Atual", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", "", 9)
        for c_nome, c_tipo, c_saldo in contas_rows:
            pdf.cell(85, 6.5, f"  {_clean_text(c_nome)}", border="B")
            pdf.cell(60, 6.5, _clean_text(c_tipo), border="B")
            pdf.cell(45, 6.5, _clean_text(fmt(c_saldo)), border="B", new_x="LMARGIN", new_y="NEXT")

    os.makedirs("exports", exist_ok=True)
    file_path = os.path.abspath(f"exports/Relatorio_{prefixo_mes}.pdf")
    pdf.output(file_path)
    return file_path
