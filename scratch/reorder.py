import re

with open('tabs/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split("    # ── ")

sections = {}
sections['header'] = parts[0]

for p in parts[1:]:
    title_line = p.split("\n")[0]
    title = title_line.replace("─", "").strip()
    sections[title] = "    # ── " + p

new_content = sections['header']
new_content += sections['Alertas Inteligentes (Fase 4.2)']
new_content += sections['Widget: Quanto posso gastar hoje (Fase 3.5)']
new_content += sections['Cards de métricas']

new_content += sections['Evolução diária']
new_content += sections['Gráficos']
new_content += sections['Gráfico de Projeção de Fluxo de Caixa (Fase 4.1)']

new_content += """
    # ── Seções Colapsáveis (Expanders) ────────────────────────────────
    with st.expander("🏅 Conquistas e ⚡ Atalhos Rápidos", expanded=False):
"""

def indent(text):
    return "\n".join("        " + line if line.strip() else line for line in text.split("\n"))

def extra_indent(text):
    return "\n".join("    " + line if line.strip() else line for line in text.split("\n"))

new_content += extra_indent(sections['Gamificação (Badges)'])
new_content += extra_indent(sections['Atalhos de Lançamento (Fase 5.3)'])

new_content += """
    with st.expander("💚 Saúde Financeira e Regra 50-30-20", expanded=False):
"""
new_content += extra_indent(sections['Score + Regra 50-30-20'])

new_content += """
    with st.expander("📅 Previsão de Contas a Pagar", expanded=False):
"""
new_content += extra_indent(sections['Previsão de Contas a Pagar (Fase 4)'])

new_content += """
    with st.expander("🏆 Top 5 Gastos e Visão Anual", expanded=False):
"""
new_content += extra_indent(sections['Top 5 Gastos do Mês (Fase 3.2)'])
new_content += extra_indent(sections['Resumo Anual (Fase 3.1)'])

with open('tabs/dashboard_new.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Refactor complete")
