# 📊 Financeiro — Controle Pessoal

Aplicativo completo de controle financeiro pessoal, desenvolvido em Python usando [Streamlit](https://streamlit.io/).

## 🚀 Funcionalidades

- **Dashboard:** Visão geral rápida com saldos e metas.
- **Transações:** Cadastro de receitas, despesas, incluindo modo recorrente.
- **Orçamento:** Definição de limites mensais de gastos (Regra 50-30-20).
- **Cartões de Crédito:** Controle específico para limite e vencimento de faturas.
- **Insights:** Gráficos inteligentes com análise usando IA (Google Gemini).

## 🛠️ Tecnologias

- Python 3
- Streamlit
- Pandas & Plotly (Análise de Dados e Gráficos)
- PostgreSQL (Supabase) ou SQLite Local
- Autenticação via `secrets`

## 📦 Como rodar localmente

1. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Crie o arquivo `.streamlit/secrets.toml` com suas configurações de senha (e Supabase, se quiser):
   ```toml
   [passwords]
   admin = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
   ```

4. Inicie o app:
   ```bash
   streamlit run app.py
   ```
