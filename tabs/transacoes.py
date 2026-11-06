"""
tabs/transacoes.py — Aba de Transações (criar, listar em Feed ou Tabela Editável, buscar, editar em Modal, importar CSV/OFX).
"""
import calendar
import html
import io
import re
from datetime import date, datetime
import pandas as pd
import streamlit as st

from core.utils import fmt, MESES_PT, processar_tags
from core.models import get_contas, get_categorias, get_transacoes_mes, clear_cache_transacoes
from components.cards import sec
from intelligence.categorizer import sugerir_categoria, aprender_categoria


def _processar_recorrentes(conn, prefixo_mes):
    """Processa transações recorrentes para o mês atual preservando o dia original de vencimento."""
    ano, mes = int(prefixo_mes[:4]), int(prefixo_mes[5:7])
    mes_ant = mes - 1
    ano_ant = ano
    if mes_ant <= 0:
        mes_ant = 12
        ano_ant -= 1
    prefixo_ant = f"{ano_ant}-{mes_ant:02d}"

    recorrentes = conn.execute("""
        SELECT t.id, t.tipo, t.descricao, t.valor, t.categoria_id, t.conta_id, t.observacao, t.data
        FROM transacoes t
        WHERE t.recorrente = 1 AND t.data LIKE ?
        AND t.id NOT IN (
            SELECT transacao_origem_id FROM recorrentes_log WHERE prefixo_mes = ?
        )
    """, (f"{prefixo_ant}%", prefixo_mes)).fetchall()

    if recorrentes:
        max_dia_mes = calendar.monthrange(ano, mes)[1]
        count = 0
        for r in recorrentes:
            try:
                dia_orig = int(str(r[7])[-2:])
            except Exception:
                dia_orig = 1
            dia_lanc = min(max(1, dia_orig), max_dia_mes)
            data_lancamento = f"{prefixo_mes}-{dia_lanc:02d}"

            conn.execute(
                "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                "VALUES (?,?,?,?,?,?,1,?)",
                (r[1], r[2], r[3], data_lancamento, r[4], r[5], r[6] or ""),
            )
            conn.execute(
                "INSERT OR IGNORE INTO recorrentes_log (prefixo_mes, transacao_origem_id, processado_em) "
                "VALUES (?,?,?)"
                if not getattr(conn, 'is_postgres', False) else
                "INSERT INTO recorrentes_log (prefixo_mes, transacao_origem_id, processado_em) "
                "VALUES (?,?,?) ON CONFLICT DO NOTHING",
                (prefixo_mes, r[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            count += 1
        conn.commit()
        clear_cache_transacoes()
        return count
    return 0


def _parse_valor_br(val_raw) -> float:
    """Converte strings como 'R$ 1.234,56', '-45,90' ou floats para float."""
    if pd.isna(val_raw):
        return 0.0
    if isinstance(val_raw, (int, float)):
        return float(val_raw)
    s = str(val_raw).strip().replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def _parse_data_flex(dt_raw) -> str:
    """Converte datas YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY ou YYYYMMDD para YYYY-MM-DD."""
    s = str(dt_raw).strip()[:10]
    for fmt_str in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt_str).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return pd.to_datetime(s, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return date.today().strftime("%Y-%m-%d")


def _parse_ofx(content_bytes: bytes) -> pd.DataFrame:
    """Parser leve para arquivos OFX bancários brasileiros."""
    try:
        text = content_bytes.decode("utf-8", errors="ignore")
    except Exception:
        text = content_bytes.decode("latin-1", errors="ignore")

    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, flags=re.DOTALL | re.IGNORECASE)
    rows = []
    for b in blocks:
        dt_m = re.search(r"<DTPOSTED>\s*(\d{8})", b, re.IGNORECASE)
        amt_m = re.search(r"<TRNAMT>\s*([-\d.,]+)", b, re.IGNORECASE)
        memo_m = re.search(r"<(?:MEMO|NAME)>\s*([^<\r\n]+)", b, re.IGNORECASE)
        if amt_m:
            raw_val = _parse_valor_br(amt_m.group(1))
            dt_str = _parse_data_flex(dt_m.group(1)) if dt_m else date.today().strftime("%Y-%m-%d")
            desc_str = memo_m.group(1).strip() if memo_m else "Transação OFX"
            rows.append({
                "Data": dt_str,
                "Descrição": desc_str,
                "Valor": abs(raw_val),
                "Tipo": "receita" if raw_val > 0 else "despesa",
            })
    return pd.DataFrame(rows)


@st.dialog("✏️ Gerenciar Transação")
def _modal_editar_transacao(conn, tx_sel, categorias_df, contas_df):
    st.caption(f"ID #{tx_sel['id']} · Registrada em {tx_sel['data']}")
    with st.form(f"form_modal_edit_{tx_sel['id']}"):
        e1, e2 = st.columns(2)
        with e1:
            edit_desc = st.text_input("Descrição", value=tx_sel['descricao'])
        with e2:
            edit_valor = st.number_input("Valor (R$)", value=float(tx_sel['valor']), min_value=0.01, step=10.0, format="%.2f")

        e3, e4 = st.columns(2)
        with e3:
            try:
                edit_data = st.date_input("Data", value=pd.to_datetime(tx_sel['data']).date())
            except Exception:
                edit_data = st.date_input("Data", value=date.today())
        with e4:
            if not categorias_df.empty:
                cat_opts = {f"{r['icone']} {r['nome']}": r["id"] for _, r in categorias_df.iterrows()}
                cat_keys = list(cat_opts.keys())
                cat_idx = 0
                for idx_c, (k, v) in enumerate(cat_opts.items()):
                    if v == tx_sel.get("categoria_id") or (tx_sel.get("cat") and tx_sel["cat"] in k):
                        cat_idx = idx_c
                        break
                edit_cat = st.selectbox("Categoria", cat_keys, index=cat_idx)
                edit_cat_id = cat_opts[edit_cat]
            else:
                edit_cat_id = None

        e5, e6 = st.columns(2)
        with e5:
            if not contas_df.empty:
                conta_opts = {f"{r['icone']} {r['nome']}": r["id"] for _, r in contas_df.iterrows()}
                conta_keys = list(conta_opts.keys())
                conta_idx = 0
                for idx_co, (k, v) in enumerate(conta_opts.items()):
                    if v == tx_sel.get("conta_id") or (tx_sel.get("conta") and tx_sel["conta"] in k):
                        conta_idx = idx_co
                        break
                edit_conta = st.selectbox("Conta", conta_keys, index=conta_idx)
                edit_conta_id = conta_opts[edit_conta]
            else:
                edit_conta_id = None
        with e6:
            edit_obs = st.text_input("Observação", value=tx_sel.get('observacao', '') or '')

        edit_rec = st.checkbox("🔄 Transação Recorrente (Fixa)", value=bool(tx_sel.get("recorrente")))

        c_save, c_del = st.columns(2)
        with c_save:
            salvar = st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
        with c_del:
            excluir = st.form_submit_button("🗑️ Excluir Transação", use_container_width=True)

        if salvar and edit_desc.strip() and edit_valor > 0 and edit_cat_id and edit_conta_id:
            conn.execute(
                "UPDATE transacoes SET descricao=?, valor=?, data=?, categoria_id=?, conta_id=?, observacao=?, recorrente=? WHERE id=?",
                (edit_desc.strip(), edit_valor, edit_data.strftime("%Y-%m-%d"), edit_cat_id, edit_conta_id, edit_obs.strip(), 1 if edit_rec else 0, int(tx_sel['id'])),
            )
            conn.commit()
            clear_cache_transacoes()
            st.toast("✅ Transação atualizada!")
            st.rerun()

        if excluir:
            conn.execute("DELETE FROM transacoes WHERE id=?", (int(tx_sel['id']),))
            conn.commit()
            clear_cache_transacoes()
            st.toast("🗑️ Transação removida!")
            st.rerun()


def render(ctx):
    """Renderiza a aba Transações."""
    conn = ctx["conn"]
    prefixo_mes = ctx["prefixo_mes"]
    mes_sel = ctx["mes_sel"]

    # ── Processar recorrentes automaticamente ─────────────────────────
    count_rec = _processar_recorrentes(conn, prefixo_mes)
    if count_rec > 0:
        st.success(f"🔄 {count_rec} transação(ões) recorrente(s) lançada(s) automaticamente respeitando os dias de vencimento!")

    # ── Nova Transação ────────────────────────────────────────────────
    sec("➕", "Nova Transação")
    contas_df = get_contas(conn)
    categorias_df = get_categorias(conn)

    with st.form("form_tx", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tipo_tx = st.selectbox(
                "Tipo", ["despesa", "receita"],
                format_func=lambda x: "🔴 Despesa" if x == "despesa" else "🟢 Receita",
            )
        with f2:
            data_tx = st.date_input("Data", value=date.today())
        f3, f4 = st.columns(2)
        with f3:
            desc_tx = st.text_input("Descrição", placeholder="Ex: Supermercado, Uber, Salário...")
        with f4:
            valor_tx = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        f5, f6 = st.columns(2)
        with f5:
            if not categorias_df.empty:
                opcoes_cat = {"✨ Auto-detectar pela descrição": "AUTO"}
                for _, r in categorias_df.iterrows():
                    opcoes_cat[f"{r['icone']} {r['nome']} ({r['tipo']})"] = r["id"]
                cs = st.selectbox("Categoria", list(opcoes_cat.keys()), index=0)
                cat_choice = opcoes_cat[cs]
            else:
                st.warning("Sem categorias.")
                cat_choice = None
        with f6:
            if not contas_df.empty:
                co2 = {f"{r['icone']} {r['nome']}": r["id"] for _, r in contas_df.iterrows()}
                cs2 = st.selectbox("Conta", list(co2.keys()))
                conta_id = co2[cs2]
            else:
                st.warning("Sem contas.")
                conta_id = None

        f7, f8 = st.columns(2)
        with f7:
            obs_tx = st.text_input("Observação (opcional)", placeholder="Ex: Dividido com João...")
        with f8:
            tags_tx = st.text_input("Tags (separadas por vírgula)", placeholder="Ex: viagem, lazer")

        f9, f10 = st.columns(2)
        with f9:
            recorrente_tx = st.checkbox("🔄 Lançamento Recorrente (Conta Fixa Mensal)")
        with f10:
            parcelado_tx = st.checkbox("💳 Compra Parcelada")
            qtd_parcelas = st.number_input("Número de Parcelas (se parcelada)", min_value=2, max_value=72, value=2, step=1)

        if st.form_submit_button("💾 Salvar Transação", use_container_width=True, type="primary"):
            if desc_tx.strip() and valor_tx > 0 and cat_choice and conta_id:
                from dateutil.relativedelta import relativedelta

                # Resolver categoria caso esteja em modo Auto-detectar
                if cat_choice == "AUTO":
                    sug_id, _ = sugerir_categoria(conn, desc_tx)
                    if sug_id:
                        cat_id = int(sug_id)
                    else:
                        cats_tipo = categorias_df[categorias_df["tipo"].isin([tipo_tx, "ambos"])]
                        cat_id = int(cats_tipo["id"].iloc[0]) if not cats_tipo.empty else int(categorias_df["id"].iloc[0])
                else:
                    cat_id = int(cat_choice)

                parcelas_real = int(qtd_parcelas) if parcelado_tx else 1

                try:
                    for i in range(parcelas_real):
                        desc_atual = f"{desc_tx.strip()} ({i+1}/{parcelas_real})" if parcelas_real > 1 else desc_tx.strip()
                        valor_atual = round(valor_tx / parcelas_real, 2) if parcelas_real > 1 else valor_tx
                        data_atual = (data_tx + relativedelta(months=i)).strftime("%Y-%m-%d")
                        rec_val = 1 if (recorrente_tx and parcelas_real == 1) else 0

                        if getattr(conn, 'is_postgres', False):
                            cursor = conn.execute(
                                "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                                "VALUES (?,?,?,?,?,?,?,?) RETURNING id",
                                (tipo_tx, desc_atual, valor_atual, data_atual, cat_id, conta_id, rec_val, obs_tx.strip()),
                            )
                            tx_id = cursor.fetchone()[0]
                        else:
                            cursor = conn.execute(
                                "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                                "VALUES (?,?,?,?,?,?,?,?)",
                                (tipo_tx, desc_atual, valor_atual, data_atual, cat_id, conta_id, rec_val, obs_tx.strip()),
                            )
                            tx_id = cursor.lastrowid

                        if tags_tx.strip():
                            processar_tags(conn, tx_id, tags_tx)

                    if cat_choice != "AUTO":
                        aprender_categoria(conn, desc_tx, cat_id)
                    conn.commit()
                    clear_cache_transacoes()
                    st.toast("✅ Transação salva!" if parcelas_real == 1 else f"✅ Compra parcelada salva em {parcelas_real}x!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.error("Preencha a descrição e um valor válido.")

    st.html("<br>")

    # ── Importar Extrato Inteligente (CSV e OFX) ──────────────────────
    with st.expander("📥 Importar Extrato Bancário (CSV / OFX com Anti-Duplicidade)"):
        st.caption("Compatível com extratos OFX e CSV (Nubank, Inter, Itaú, BB, Santander, etc.). Categoriza automaticamente e ignora lançamentos duplicados.")
        uploaded_file = st.file_uploader("Escolha um arquivo CSV ou OFX", type=["csv", "ofx"])
        if uploaded_file is not None and not contas_df.empty:
            try:
                raw_bytes = uploaded_file.read()
                fname = uploaded_file.name.lower()
                if fname.endswith(".ofx"):
                    df_imp = _parse_ofx(raw_bytes)
                    col_dt, col_desc, col_val, col_tp = "Data", "Descrição", "Valor", "Tipo"
                else:
                    # Detectar encoding e separador
                    try:
                        txt_csv = raw_bytes.decode("utf-8")
                    except Exception:
                        txt_csv = raw_bytes.decode("latin-1", errors="ignore")
                    sep = ";" if txt_csv.split("\n")[0].count(";") > txt_csv.split("\n")[0].count(",") else ","
                    df_imp = pd.read_csv(io.StringIO(txt_csv), sep=sep)

                    cols_csv = list(df_imp.columns)
                    mc1, mc2, mc3 = st.columns(3)
                    with mc1:
                        col_dt = st.selectbox("Coluna de Data", cols_csv, index=next((i for i, c in enumerate(cols_csv) if "dat" in c.lower()), 0))
                    with mc2:
                        col_desc = st.selectbox("Coluna de Descrição", cols_csv, index=next((i for i, c in enumerate(cols_csv) if any(w in c.lower() for w in ["desc", "hist", "tít", "tit", "estab"])), min(1, len(cols_csv)-1)))
                    with mc3:
                        col_val = st.selectbox("Coluna de Valor", cols_csv, index=next((i for i, c in enumerate(cols_csv) if "val" in c.lower() or "amount" in c.lower()), min(2, len(cols_csv)-1)))
                    col_tp = next((c for c in cols_csv if "tip" in c.lower()), None)

                st.dataframe(df_imp.head(5), use_container_width=True)
                co2_keys = list(co2.keys())
                c_imp = st.selectbox("Importar para a conta:", co2_keys, key="conta_csv")

                if st.button("✅ Confirmar Importação Inteligente", type="primary", use_container_width=True):
                    conta_id_imp = co2[c_imp]
                    inseridos, ignorados = 0, 0
                    for _, row in df_imp.iterrows():
                        dt = _parse_data_flex(row.get(col_dt, date.today().strftime("%Y-%m-%d")))
                        desc = str(row.get(col_desc, "Importado")).strip()
                        raw_v = _parse_valor_br(row.get(col_val, 0))
                        val = abs(raw_v)

                        if col_tp and col_tp in row and pd.notna(row[col_tp]):
                            tp_raw = str(row[col_tp]).strip().lower()
                            tp = "receita" if tp_raw in ("receita", "crédito", "credito", "c", "entrada") else "despesa"
                        else:
                            tp = "receita" if raw_v > 0 and fname.endswith(".ofx") else ("despesa" if raw_v < 0 else "despesa")

                        if val <= 0:
                            continue

                        # Verificar duplicidade (mesma data, descrição, valor e conta)
                        ja_existe = conn.execute(
                            "SELECT 1 FROM transacoes WHERE data=? AND descricao=? AND ABS(valor - ?) < 0.01 AND conta_id=? LIMIT 1",
                            (dt, desc, val, conta_id_imp),
                        ).fetchone()
                        if ja_existe:
                            ignorados += 1
                            continue

                        sug_cat_id, _ = sugerir_categoria(conn, desc)
                        cat_id_imp = sug_cat_id if sug_cat_id else (int(categorias_df["id"].iloc[0]) if not categorias_df.empty else None)

                        if cat_id_imp:
                            conn.execute(
                                "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente) "
                                "VALUES (?,?,?,?,?,?,0)",
                                (tp, desc, val, dt, cat_id_imp, conta_id_imp),
                            )
                            inseridos += 1
                    conn.commit()
                    clear_cache_transacoes()
                    st.toast(f"✅ {inseridos} importadas ({ignorados} duplicadas ignoradas)!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

    # ── Listagem e Gerenciamento ──────────────────────────────────────
    sec("🔍", f"Transações de {MESES_PT[mes_sel]}")

    col_busca, col_modo, col_gerenciar = st.columns([2.2, 1.3, 1.5])
    with col_busca:
        busca = st.text_input("Buscar...", placeholder="🔎 Filtrar por descrição, tag ou observação...", key="busca_tx", label_visibility="collapsed")
    with col_modo:
        modo_visao = st.segmented_control(
            "Modo de Visão",
            options=["📱 Feed", "📋 Tabela"],
            default="📱 Feed",
            label_visibility="collapsed",
        ) or "📱 Feed"

    txs = get_transacoes_mes(conn, prefixo_mes, busca)

    # ── Filtros avançados e Exportar ─────────────────────────────────
    with st.expander("🔎 Filtros Avançados / 📤 Exportar CSV"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            filtro_tipo = st.selectbox("Tipo", ["Todos", "🔴 Despesa", "🟢 Receita", "🔄 Transferências"], key="filtro_tipo")
        with fc2:
            cats_filtro = ["Todas"] + sorted(txs["cat"].dropna().unique().tolist()) if not txs.empty else ["Todas"]
            filtro_cat = st.selectbox("Categoria", cats_filtro, key="filtro_cat")
        with fc3:
            contas_filtro = ["Todas"] + sorted(txs["conta"].dropna().unique().tolist()) if not txs.empty else ["Todas"]
            filtro_conta = st.selectbox("Conta", contas_filtro, key="filtro_conta")

        if not txs.empty:
            if filtro_tipo == "🔴 Despesa":
                txs = txs[(txs["tipo"] == "despesa") & (txs["is_transferencia"] == 0)]
            elif filtro_tipo == "🟢 Receita":
                txs = txs[(txs["tipo"] == "receita") & (txs["is_transferencia"] == 0)]
            elif filtro_tipo == "🔄 Transferências":
                txs = txs[txs["is_transferencia"] == 1]
            if filtro_cat != "Todas":
                txs = txs[txs["cat"] == filtro_cat]
            if filtro_conta != "Todas":
                txs = txs[txs["conta"] == filtro_conta]

        if not txs.empty:
            csv_data = txs[["data", "tipo", "descricao", "valor", "cat", "conta", "observacao", "tags_str"]].copy()
            csv_data.columns = ["Data", "Tipo", "Descrição", "Valor", "Categoria", "Conta", "Observação", "Tags"]
            csv_string = csv_data.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📤 Exportar Transações Filtradas (CSV)",
                data=csv_string,
                file_name=f"transacoes_{prefixo_mes}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

    with col_gerenciar:
        tx_opcoes = txs.to_dict('records') if not txs.empty else []
        tx_map = {t["id"]: t for t in tx_opcoes}
        tx_sel_id = st.selectbox(
            "Gerenciar",
            options=[None] + list(tx_map.keys()),
            format_func=lambda x: "✏️ Editar / Excluir..." if x is None else f"{tx_map[x]['descricao']} ({fmt(tx_map[x]['valor'])})",
            label_visibility="collapsed",
        )
        if tx_sel_id is not None and st.button("Abrir Editor", type="primary", use_container_width=True):
            _modal_editar_transacao(conn, tx_map[tx_sel_id], categorias_df, contas_df)

    if txs.empty:
        st.info("Nenhuma transação encontrada neste período.")
        return

    # Totalizador visual (excluindo transferências entre contas para não distorcer)
    txs_reais = txs[txs["is_transferencia"] == 0]
    tot_rec = txs_reais[txs_reais['tipo'] == 'receita']['valor'].sum()
    tot_desp = txs_reais[txs_reais['tipo'] == 'despesa']['valor'].sum()
    tot_saldo = tot_rec - tot_desp

    st.html(f"""
    <div style="display:flex; justify-content:space-around; padding: 0.8rem; background: linear-gradient(135deg, rgba(22,27,38,0.7), rgba(11,14,20,0.8)); border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="text-align:center;">
            <div style="font-size:0.65rem; color:#8b95a5; text-transform:uppercase;">Receitas Filtradas</div>
            <div style="font-weight:700; color:#00d4aa;">{fmt(tot_rec)}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:0.65rem; color:#8b95a5; text-transform:uppercase;">Despesas Filtradas</div>
            <div style="font-weight:700; color:#ff4b6e;">{fmt(tot_desp)}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:0.65rem; color:#8b95a5; text-transform:uppercase;">Resultado</div>
            <div style="font-weight:700; color:{'#00d4aa' if tot_saldo >= 0 else '#ff4b6e'};">{fmt(tot_saldo)}</div>
        </div>
    </div>
    """)

    # ── Visão em Tabela Interativa (Edição em Lote) ───────────────────
    if modo_visao == "📋 Tabela":
        st.caption("💡 Edite descrições, valores, datas ou marque a coluna **Excluir** e clique em **Aplicar Alterações da Tabela**.")
        df_edit = txs[["id", "data", "tipo", "descricao", "valor", "cat", "conta", "observacao"]].copy()
        df_edit["Excluir"] = False

        edited_df = st.data_editor(
            df_edit,
            key="editor_txs_table",
            use_container_width=True,
            hide_index=True,
            disabled=["id", "tipo", "cat", "conta"],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "data": st.column_config.TextColumn("Data (YYYY-MM-DD)", width="small"),
                "tipo": st.column_config.TextColumn("Tipo", width="small"),
                "descricao": st.column_config.TextColumn("Descrição", width="large"),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.01),
                "cat": st.column_config.TextColumn("Categoria"),
                "conta": st.column_config.TextColumn("Conta"),
                "observacao": st.column_config.TextColumn("Observação"),
                "Excluir": st.column_config.CheckboxColumn("🗑️ Excluir?", default=False),
            },
        )

        if st.button("💾 Aplicar Alterações da Tabela", type="primary"):
            removidos, atualizados = 0, 0
            orig_map = {int(r["id"]): r for _, r in df_edit.iterrows()}
            for _, row_ed in edited_df.iterrows():
                tid = int(row_ed["id"])
                if row_ed["Excluir"]:
                    conn.execute("DELETE FROM transacoes WHERE id=?", (tid,))
                    removidos += 1
                else:
                    orig = orig_map[tid]
                    if (
                        str(row_ed["descricao"]) != str(orig["descricao"])
                        or float(row_ed["valor"]) != float(orig["valor"])
                        or str(row_ed["data"]) != str(orig["data"])
                        or str(row_ed["observacao"] or "") != str(orig["observacao"] or "")
                    ):
                        conn.execute(
                            "UPDATE transacoes SET descricao=?, valor=?, data=?, observacao=? WHERE id=?",
                            (str(row_ed["descricao"]).strip(), float(row_ed["valor"]), str(row_ed["data"]).strip(), str(row_ed["observacao"] or "").strip(), tid),
                        )
                        atualizados += 1
            if removidos > 0 or atualizados > 0:
                conn.commit()
                clear_cache_transacoes()
                st.toast(f"✅ {atualizados} atualizada(s), {removidos} excluída(s)!")
                st.rerun()
        return

    # ── Visão Feed (Cards com Badges de Recorrência, Parcela, Tags e Obs) ──
    txs['data_formatada'] = pd.to_datetime(txs['data'], errors='coerce').dt.strftime('%Y-%m-%d').fillna(txs['data'])
    datas_unicas = sorted(txs['data_formatada'].unique(), reverse=True)

    html_feed = "<div class='tx-feed-container'>"
    for dt in datas_unicas:
        try:
            dt_obj = datetime.strptime(dt, '%Y-%m-%d')
            mes_nome = MESES_PT[dt_obj.month][:3].upper()
            cabecalho_dia = f"{dt_obj.day:02d} DE {mes_nome}"
        except Exception:
            cabecalho_dia = str(dt)

        html_feed += f'<div class="day-header">{cabecalho_dia}</div>'

        txs_dia = txs[txs['data_formatada'] == dt]
        for _, row in txs_dia.iterrows():
            is_inc = row['tipo'] == 'receita'
            bg_class = 'inc-bg' if is_inc else 'exp-bg'
            amount_class = 'inc' if is_inc else 'exp'
            sinal = "+" if is_inc else "-"
            icone = row['ci'] if pd.notna(row['ci']) else '📌'
            cat_nome = row['cat'] if pd.notna(row['cat']) else 'Sem categoria'
            conta_nome = row['conta'] if pd.notna(row['conta']) else 'Sem conta'
            desc_str = str(row["descricao"])

            # Construir badges informativas
            badges_html = ""
            if row.get("is_transferencia") == 1:
                badges_html += '<span class="tx-tag" style="background:rgba(6,182,212,0.15);color:#06b6d4;">🔄 Transferência</span>'
            if row.get("recorrente") == 1:
                badges_html += '<span class="tx-badge-recur">🔄 Fixa</span>'
            if re.search(r"\(\d+/\d+\)$", desc_str):
                badges_html += '<span class="tx-badge-parcel">💳 Parcelado</span>'
            if pd.notna(row.get("tags_str")) and str(row["tags_str"]).strip():
                for tg in str(row["tags_str"]).split(","):
                    if tg.strip():
                        badges_html += f'<span class="tx-tag">#{html.escape(tg.strip())}</span>'

            obs_str = str(row.get("observacao") or "").strip()
            obs_html = f'<div style="font-size:0.66rem;color:var(--text3);margin-top:2px;">💬 {html.escape(obs_str)}</div>' if obs_str else ""

            html_feed += (
                f'<div class="tx-item">'
                f'<div class="tx-left">'
                f'<div class="tx-cat-icon {bg_class}">{icone}</div>'
                f'<div>'
                f'<div class="tx-desc">{html.escape(desc_str)}</div>'
                f'<div class="tx-meta">{html.escape(str(conta_nome))} &bull; {html.escape(str(cat_nome))} {badges_html}</div>'
                f'{obs_html}'
                f'</div>'
                f'</div>'
                f'<div class="tx-amount {amount_class}">{sinal} {fmt(row["valor"])}</div>'
                f'</div>'
            )

    html_feed += "</div>"
    st.html(html_feed)
