# 📊 Financeiro — Controle Pessoal

Aplicativo completo de controle financeiro pessoal e empresarial (Simples Nacional), desenvolvido em Python com [Streamlit](https://streamlit.io/) e PostgreSQL ([Supabase](https://supabase.com/)).

## 🚀 Funcionalidades

- **Dashboard:** Visão executiva com balanço mensal, evolução diária, projeção de fluxo de caixa, Saúde Financeira (Score 0–100) e Regra 50-30-20.
- **Transações:** Cadastro rápido (modal global em qualquer aba), recorrências, parcelamentos, tabela editável em lote e importador de extratos CSV/OFX com anti-duplicidade.
- **Cartões de Crédito:** Controle automático de ciclo de fechamento, vencimento, detalhamento de itens e pagamento de fatura.
- **Orçamento & Metas:** Tetos mensais por categoria e cofres de objetivos (com separação inteligente de resgates da Reserva de Emergência).
- **Simulador & Investimentos:** Simulador de juros compostos com taxas oficiais do Banco Central (Selic, CDI e IPCA 12m em tempo real) e desconto de inflação (poder de compra real).
- **Insights & IA:** Análise automática de padrões de consumo, consultor financeiro via Google Gemini e exportação de Relatório Executivo em PDF.

## 🛠️ Tecnologias

- Python 3.11+
- Streamlit
- Pandas & Plotly
- PostgreSQL (Supabase + Row Level Security) / SQLite (fallback local)
- FPDF2 (Relatórios PDF)
- Google GenAI SDK (Gemini 2.5 Flash)

## 📦 Como rodar localmente

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Crie o arquivo `.streamlit/secrets.toml` (já ignorado pelo Git) com suas credenciais:
   ```toml
   [supabase]
   url = "postgresql://postgres.<ref>:<senha>@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
   api_url = "https://<ref>.supabase.co"
   api_key = "<sua-anon-key>"

   [auth]
   allowed_email = "seu-email@exemplo.com"

   [gemini]
   api_key = "<sua-chave-gemini-opcional>"

   [fiscal]
   aliquota_simples = 0.06
   ```

4. Inicie o aplicativo:
   ```bash
   streamlit run app.py
   ```
