"""
core/auth.py — Sistema de autenticação simples para o app Financeiro.
"""
import streamlit as st
import hashlib
import hmac


def _hash_password(password: str) -> str:
    """Gera hash SHA-256 de uma senha."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password() -> bool:
    """Exibe formulário de login e retorna True se autenticado.

    Credenciais são lidas de st.secrets["passwords"].
    Exemplo em .streamlit/secrets.toml:
        [passwords]
        admin = "hash_sha256_da_senha"
    """
    # Se já autenticado nesta sessão, pula o formulário
    if st.session_state.get("authenticated"):
        return True

    # Se não há secrets configurados, permite acesso (dev local)
    if "passwords" not in st.secrets:
        return True

    # ─── Tela de Login ────────────────────────────────────────────────────
    st.markdown("""
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
    """, unsafe_allow_html=True)

    # Container centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">📊 Financeiro</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Controle Pessoal</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Preencha usuário e senha.")
                return False

            # Verifica credenciais
            stored_passwords = st.secrets["passwords"]
            if username in stored_passwords:
                stored_hash = stored_passwords[username]
                input_hash = _hash_password(password)
                if hmac.compare_digest(input_hash, stored_hash):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.rerun()

            st.error("❌ Usuário ou senha incorretos.")
            return False

    return False
