"""
core/auth.py — Autenticação do app Financeiro (uso individual).

Login via Supabase Auth, restrito ao e-mail em st.secrets["auth"]["allowed_email"].
"""
import streamlit as st


@st.cache_resource
def _get_supabase(url: str, key: str):
    from supabase import create_client
    return create_client(url, key)


def _allowed_email() -> str:
    return str(st.secrets.get("auth", {}).get("allowed_email", "")).strip().lower()


def logout():
    """Encerra a sessão do usuário."""
    for k in ("authenticated", "user_id", "user_email"):
        st.session_state.pop(k, None)
    st.rerun()


def check_password() -> bool:
    """Exibe formulário de login e retorna True se autenticado.
    Autentica via Supabase Auth (Email/Senha).
    """
    if st.session_state.get("authenticated"):
        return True

    # Sem configuração completa, bloqueia (nunca libera acesso por padrão)
    if "supabase" not in st.secrets or not _allowed_email():
        st.error("Configuração ausente em secrets.toml ([supabase] e [auth] allowed_email).")
        return False

    supabase = _get_supabase(st.secrets["supabase"]["api_url"], st.secrets["supabase"]["api_key"])

    # ─── Tela de Login ────────────────────────────────────────────────────
    st.html("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 8rem auto 0 auto;
        padding: 2.5rem;
        background: linear-gradient(135deg, rgba(22,27,38,0.95) 0%, rgba(11,14,20,0.98) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden;
    }
    .login-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4aa, #4e8cff, #a855f7);
    }
    .login-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.3rem;
    }
    .login-subtitle {
        text-align: center;
        font-size: 0.8rem;
        color: #5a6478;
        margin-bottom: 1.5rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    </style>
    """)

    # Container centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.html('<div class="login-title">📊 Financeiro</div>')
        st.html('<div class="login-subtitle">Controle Pessoal na Nuvem</div>')

        with st.form("login_form"):
            email_login = st.text_input("📧 Email", placeholder="Digite seu email", autocomplete="username")
            pass_login = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha", autocomplete="current-password")
            submitted_login = st.form_submit_button("Entrar", width='stretch', type="primary")

        if submitted_login:
            email_norm = (email_login or "").strip().lower()
            if not email_norm or not pass_login:
                st.error("Preencha email e senha.")
            elif email_norm != _allowed_email():
                # Mesma mensagem do erro de senha, para não revelar qual e-mail é válido
                st.error("❌ Email ou senha incorretos.")
            else:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_norm, "password": pass_login})
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = res.user.id
                    st.session_state["user_email"] = email_norm
                    st.rerun()
                except Exception:
                    st.error("❌ Email ou senha incorretos.")

    return False
