import psycopg2
import streamlit as st
from supabase import create_client, Client

def setup_multi_tenant():
    print("Iniciando setup Multiusuário e Segurança...")
    
    user_id = "16faa9c5-8c63-4f99-832c-f7cbb6ce9dc9"
    print(f"UUID do Admin: {user_id}")
    
    # 3. Atualizar tabelas no banco de dados (Adicionar user_id e RLS)
    conn_url = st.secrets["supabase"]["url"]
    conn = psycopg2.connect(conn_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    tabelas = [
        "contas", "categorias", "transacoes", "metas", "orcamentos", 
        "tags", "transacao_tags", "mapeamento_categorias", "atalhos"
    ]
    
    for tabela in tabelas:
        print(f"Aplicando segurança na tabela: {tabela}")
        
        # Adicionar coluna se não existir
        cur.execute(f"""
            ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS user_id UUID;
        """)
        
        # Atualizar registros antigos para pertencerem ao admin
        cur.execute(f"""
            UPDATE {tabela} SET user_id = %s WHERE user_id IS NULL;
        """, (user_id,))
        
        # Tornar obrigatório
        cur.execute(f"""
            ALTER TABLE {tabela} ALTER COLUMN user_id SET NOT NULL;
        """)
        
        # Ativar Row Level Security
        cur.execute(f"""
            ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;
        """)
        
        # Criar política (ignora erro se já existir)
        try:
            cur.execute(f"""
                CREATE POLICY "Isolar dados de usuario" ON {tabela}
                FOR ALL
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
            """)
        except psycopg2.errors.DuplicateObject:
            conn.rollback() # Rollback do erro da policy
            cur = conn.cursor()
            
    conn.commit()
    conn.close()
    
    print("\n✅ Banco de dados protegido e convertido para Multiusuário com RLS!")
    print(f"Novo Login: {email}")
    print(f"Nova Senha: {password}")

if __name__ == "__main__":
    setup_multi_tenant()
