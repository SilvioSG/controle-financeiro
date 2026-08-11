import os
from datetime import datetime
from fpdf import FPDF
from core.utils import fmt, MESES_PT

class RelatorioPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Relatório Financeiro Mensal", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def gerar_relatorio_pdf(conn, mes_sel, ano_sel, prefixo_mes, rec_mes, desp_mes, simples_mes, balanco_mes, score):
    """
    Gera um arquivo PDF com o relatório do mês selecionado.
    Retorna o caminho absoluto para o arquivo gerado (salvo num diretório temporário/app).
    """
    pdf = RelatorioPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    nome_mes = MESES_PT[mes_sel]
    pdf.cell(0, 10, f"Período: {nome_mes} de {ano_sel}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Resumo Geral
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Resumo Geral", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    
    pdf.cell(50, 10, "Receitas:")
    pdf.set_text_color(0, 150, 0)
    pdf.cell(0, 10, fmt(rec_mes), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    pdf.cell(50, 10, "Despesas:")
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 10, fmt(desp_mes), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    pdf.cell(50, 10, "Simples Nacional:")
    pdf.cell(0, 10, fmt(simples_mes), new_x="LMARGIN", new_y="NEXT")

    pdf.cell(50, 10, "Balanço Líquido:")
    if balanco_mes >= 0:
        pdf.set_text_color(0, 150, 0)
    else:
        pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 10, fmt(balanco_mes), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(50, 10, "Saúde Financeira:")
    pdf.cell(0, 10, f"{score}/100", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Top 5 Gastos
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Top 5 Maiores Despesas", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)

    top5 = conn.execute(
        "SELECT descricao, valor, data FROM transacoes "
        "WHERE tipo='despesa' AND data LIKE ? "
        "ORDER BY valor DESC LIMIT 5",
        (f"{prefixo_mes}%",)
    ).fetchall()

    if not top5:
        pdf.cell(0, 10, "Nenhuma despesa registrada.", new_x="LMARGIN", new_y="NEXT")
    else:
        for i, row in enumerate(top5):
            pdf.cell(0, 10, f"{i+1}. {row[0]} - {fmt(row[1])} (em {row[2]})", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    
    # Categorias
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Despesas por Categoria", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)

    cats = conn.execute(
        "SELECT c.nome, SUM(t.valor) as total FROM transacoes t "
        "LEFT JOIN categorias c ON t.categoria_id = c.id "
        "WHERE t.tipo='despesa' AND t.data LIKE ? "
        "GROUP BY c.nome ORDER BY total DESC",
        (f"{prefixo_mes}%",)
    ).fetchall()

    if not cats:
        pdf.cell(0, 10, "Nenhuma despesa registrada.", new_x="LMARGIN", new_y="NEXT")
    else:
        for row in cats:
            cat_nome = row[0] if row[0] else "Sem Categoria"
            pdf.cell(80, 10, cat_nome)
            pdf.cell(0, 10, fmt(row[1]), new_x="LMARGIN", new_y="NEXT")

    os.makedirs("exports", exist_ok=True)
    file_path = os.path.abspath(f"exports/Relatorio_{prefixo_mes}.pdf")
    pdf.output(file_path)
    return file_path
