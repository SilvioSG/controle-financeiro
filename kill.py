import psycopg2
import streamlit as st
import traceback

try:
    conn = psycopg2.connect(st.secrets['supabase']['url'])
    cur = conn.cursor()
    cur.execute("SELECT pid, query, state, usename FROM pg_stat_activity WHERE datname = 'postgres';")
    for row in cur.fetchall():
        print(row)
except Exception as e:
    traceback.print_exc()
