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
    Autentica via Supabase Auth (Email/Senha).
    """
    if st.session_state.get("authenticated"):
        return True

    # Se não há secrets de supabase configurados, bloqueia
    if "supabase" not in st.secrets:
        st.error("Configuração do Supabase ausente em secrets.toml")
        return False
        
    from supabase import create_client, Client
    url = st.secrets["supabase"]["api_url"]
    key = st.secrets["supabase"]["api_key"]
    
    @st.cache_resource
    def get_supabase() -> Client:
        return create_client(url, key)
        
    supabase = get_supabase()
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
        st.markdown('<div class="login-subtitle">Controle Pessoal na Nuvem</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 Login", "📝 Criar Conta"])
        
        with tab1:
            with st.form("login_form"):
                email_login = st.text_input("📧 Email", placeholder="Digite seu email")
                pass_login = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
                submitted_login = st.form_submit_button("Entrar", width='stretch', type="primary")

            if submitted_login:
                if not email_login or not pass_login:
                    st.error("Preencha email e senha.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = res.user.id
                        st.rerun()
                    except Exception as e:
                        st.error("❌ Email ou senha incorretos.")

        with tab2:
            with st.form("signup_form"):
                email_signup = st.text_input("📧 Email", placeholder="Seu melhor email")
                pass_signup = st.text_input("🔒 Criar Senha", type="password", placeholder="Mínimo 6 caracteres")
                pass_confirm = st.text_input("🔒 Confirmar Senha", type="password")
                submitted_signup = st.form_submit_button("Criar Conta", width='stretch')
                
            if submitted_signup:
                if not email_signup or not pass_signup:
                    st.error("Preencha todos os campos.")
                elif pass_signup != pass_confirm:
                    st.error("As senhas não coincidem.")
                else:
                    try:
                        res = supabase.auth.sign_up({"email": email_signup, "password": pass_signup})
                        st.success("✅ Conta criada com sucesso! Você já pode fazer login.")
                        st.info("⚠️ Se você não conseguir logar, peça ao administrador para desativar a confirmação de email no Supabase.")
                    except Exception as e:
                        st.error(f"❌ Erro ao criar conta: {str(e)}")

    return False
