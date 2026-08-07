import pandas as pd
import streamlit as st
import json
import re
from utils.data_manager import init_data, get_data, sidebar_data_controls
from utils.chat import render_chat
from openai import OpenAI
from analytics import Module
from analytics import module_started
from analytics import module_completed
from analytics import track
from analytics import EventType

st.set_page_config(page_title="Planejamento Estratégico", page_icon="🧭", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
module_started(
    Module.PLANEJAMENTO
)
sidebar_data_controls()

st.title("🧭 Planejamento Estratégico")

tab1, tab2, tab3 = st.tabs(["🌟 Missão, Visão e Valores", "🔀 SWOT Cruzada", "🎯 Objetivos, KPIs e Metas"])

# ---------------- Missão, Visão, Valores ----------------
with tab1:
    st.subheader("Missão, Visão e Valores")

    def gerar_missao_ia():
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            prompt = f"""
            Empresa: {empresa_nome}
            Setor: {empresa_setor}
            
            Gere uma missão objetiva em 1-2 frases em português do Brasil.
            Responda APENAS com um JSON: {{"missao": "texto da missão"}}
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor de estratégia. Responda APENAS com JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            conteudo = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(conteudo)
        except Exception as e:
            st.error(f"Erro na IA: {str(e)}")
            return None

    def gerar_visao_ia():
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            prompt = f"""
            Empresa: {empresa_nome}
            Setor: {empresa_setor}
            
            Gere uma visão inspiradora e mensurável no tempo em 1-2 frases em português do Brasil.
            Responda APENAS com um JSON: {{"visao": "texto da visão"}}
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor de estratégia. Responda APENAS com JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            conteudo = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(conteudo)
        except Exception as e:
            st.error(f"Erro na IA: {str(e)}")
            return None

    def gerar_valores_ia():
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            
            prompt = f"""
            Empresa: {empresa_nome}
            
            Gere 4 a 6 valores organizacionais em português do Brasil, cada um com uma frase curta explicando.
            Responda APENAS com um JSON: {{"valores": ["valor1", "valor2", "valor3", "valor4"]}}
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor de estratégia. Responda APENAS com JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            conteudo = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(conteudo)
        except Exception as e:
            st.error(f"Erro na IA: {str(e)}")
            return None

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🤖 Sugerir Missão", width="stretch"):
            with st.spinner("Gerando missão..."):
                resultado = gerar_missao_ia()
                if resultado and "missao" in resultado:
                    data["mvv"]["missao"] = resultado["missao"]
                    st.rerun()
    with col_btn2:
        if st.button("🤖 Sugerir Visão", width="stretch"):
            with st.spinner("Gerando visão..."):
                resultado = gerar_visao_ia()
                if resultado and "visao" in resultado:
                    data["mvv"]["visao"] = resultado["visao"]
                    st.rerun()
    with col_btn3:
        if st.button("🤖 Sugerir Valores", width="stretch"):
            with st.spinner("Gerando valores..."):
                resultado = gerar_valores_ia()
                if resultado and "valores" in resultado:
                    data["mvv"]["valores"] = resultado["valores"]
                    st.rerun()

    st.divider()

    missao = st.text_area("Missão — por que a empresa existe hoje?", value=data["mvv"]["missao"], height=100)
    data["mvv"]["missao"] = missao

    visao = st.text_area("Visão — onde a empresa quer chegar (médio/longo prazo)?", value=data["mvv"]["visao"], height=100)
    data["mvv"]["visao"] = visao

    st.markdown("**Valores**")
    
    valores_atuais = data["mvv"]["valores"]
    df_valores = pd.DataFrame(valores_atuais, columns=["valor"]) if valores_atuais else pd.DataFrame(columns=["valor"])
    
    valores_hash = hash(str(sorted(valores_atuais))) if valores_atuais else 0
    editor_key = f"editor_valores_{valores_hash}"
    
    edited_valores = st.data_editor(
        df_valores, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True,
        column_config={"valor": st.column_config.TextColumn("Valor organizacional", width="large")},
        key=editor_key,
    )
    
    if edited_valores is not None:
        novos_valores = [v for v in edited_valores["valor"].fillna("").tolist() if str(v).strip()]
        if novos_valores != data["mvv"]["valores"]:
            data["mvv"]["valores"] = novos_valores
            st.rerun()

# ---------------- SWOT Cruzada ----------------
with tab2:
    st.subheader("Matriz SWOT Cruzada")
    st.caption(
        "Cruze os quadrantes da Análise SWOT para gerar estratégias de ação: "
        "**SO** (usar forças para aproveitar oportunidades), **ST** (usar forças para neutralizar ameaças), "
        "**WO** (superar fraquezas aproveitando oportunidades), **WT** (reduzir fraquezas e evitar ameaças)."
    )

    forcas = [i.get("descricao", "") for i in data["swot"]["forcas"] if i.get("descricao")]
    fraquezas = [i.get("descricao", "") for i in data["swot"]["fraquezas"] if i.get("descricao")]
    oportunidades = [i.get("descricao", "") for i in data["swot"]["oportunidades"] if i.get("descricao")]
    ameacas = [i.get("descricao", "") for i in data["swot"]["ameacas"] if i.get("descricao")]

    if not any([forcas, fraquezas, oportunidades, ameacas]):
        st.warning("Preencha a página **🎯 Análise SWOT** primeiro para poder cruzar os quadrantes aqui.")

    with st.expander("Ver itens da SWOT usados no cruzamento"):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown("**Forças**\n\n" + "\n".join(f"- {f}" for f in forcas) if forcas else "**Forças**\n\n_(vazio)_")
        c2.markdown("**Fraquezas**\n\n" + "\n".join(f"- {f}" for f in fraquezas) if fraquezas else "**Fraquezas**\n\n_(vazio)_")
        c3.markdown("**Oportunidades**\n\n" + "\n".join(f"- {f}" for f in oportunidades) if oportunidades else "**Oportunidades**\n\n_(vazio)_")
        c4.markdown("**Ameaças**\n\n" + "\n".join(f"- {f}" for f in ameacas) if ameacas else "**Ameaças**\n\n_(vazio)_")

    QUADRANTES_CRUZ = [
        ("SO", "🚀 SO — Forças + Oportunidades", "Estratégias ofensivas: potencializar."),
        ("ST", "🛡️ ST — Forças + Ameaças", "Estratégias defensivas: proteger."),
        ("WO", "🔧 WO — Fraquezas + Oportunidades", "Estratégias de reforço: melhorar para aproveitar."),
        ("WT", "🚧 WT — Fraquezas + Ameaças", "Estratégias de sobrevivência: minimizar riscos."),
    ]

    def gerar_swot_cruzada(quadrante=None):
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            forcas_texto = "; ".join(forcas) or "nenhuma força definida"
            fraquezas_texto = "; ".join(fraquezas) or "nenhuma fraqueza definida"
            oportunidades_texto = "; ".join(oportunidades) or "nenhuma oportunidade definida"
            ameacas_texto = "; ".join(ameacas) or "nenhuma ameaça definida"
            
            if quadrante:
                chave, titulo, ajuda = next(q for q in QUADRANTES_CRUZ if q[0] == quadrante)
                prompt = f"""
                Você é um consultor de estratégia especialista em SWOT Cruzada.
                
                INFORMAÇÕES DA EMPRESA:
                - Nome: {empresa_nome}
                - Setor: {empresa_setor}
                
                FORÇAS: {forcas_texto}
                FRAQUEZAS: {fraquezas_texto}
                OPORTUNIDADES: {oportunidades_texto}
                AMEAÇAS: {ameacas_texto}
                
                Quadrante: {titulo}
                Descrição: {ajuda}
                
                Gere de 3 a 5 estratégias específicas em português do Brasil para este quadrante.
                Responda APENAS com um JSON: {{"itens": ["estratégia1", "estratégia2", "estratégia3"]}}
                """
            else:
                prompt = f"""
                Você é um consultor de estratégia especialista em SWOT Cruzada.
                
                INFORMAÇÕES DA EMPRESA:
                - Nome: {empresa_nome}
                - Setor: {empresa_setor}
                
                FORÇAS: {forcas_texto}
                FRAQUEZAS: {fraquezas_texto}
                OPORTUNIDADES: {oportunidades_texto}
                AMEAÇAS: {ameacas_texto}
                
                Gere estratégias para os 4 quadrantes da SWOT Cruzada em português do Brasil.
                
                FORMATO DE SAÍDA: Retorne APENAS um JSON com:
                {{
                    "SO": ["estratégia1", "estratégia2"],
                    "ST": ["estratégia1", "estratégia2"],
                    "WO": ["estratégia1", "estratégia2"],
                    "WT": ["estratégia1", "estratégia2"]
                }}
                """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor de estratégia. Responda em português do Brasil. Retorne APENAS JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            conteudo = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(conteudo)
            
        except Exception as e:
            st.error(f"Erro na IA: {str(e)}")
            return None

    st.subheader("🚀 Ações com IA")
    col_gerar1, col_gerar2, col_gerar3 = st.columns([3, 1, 1])
    with col_gerar1:
        st.caption("A IA vai gerar estratégias para todos os quadrantes da SWOT Cruzada")
    with col_gerar2:
        if st.button("🔄 Gerar SWOT Cruzada", width="stretch"):
            if not any([forcas, fraquezas, oportunidades, ameacas]):
                st.warning("⚠️ Preencha a Análise SWOT primeiro!")
            else:
                with st.spinner("Gerando SWOT Cruzada..."):
                    resultado = gerar_swot_cruzada()
                    if resultado:
                        for chave, _, _ in QUADRANTES_CRUZ:
                            if chave in resultado and resultado[chave]:
                                itens_existentes = data["swot_cruzada"].get(chave, [])
                                existentes_desc = {item["estrategia"].lower().strip() for item in itens_existentes}
                                for item in resultado[chave]:
                                    if item and item.lower().strip() not in existentes_desc:
                                        itens_existentes.append({"estrategia": item})
                                data["swot_cruzada"][chave] = itens_existentes
                        st.success("✅ SWOT Cruzada gerada!")
                        st.rerun()
    with col_gerar3:
        if st.button("🗑️ Limpar SWOT Cruzada", width="stretch"):
            for chave, _, _ in QUADRANTES_CRUZ:
                data["swot_cruzada"][chave] = []
            st.rerun()

    st.divider()

    col_a, col_b = st.columns(2)
    cols_map = {0: col_a, 1: col_b, 2: col_a, 3: col_b}

    for i, (chave, titulo, ajuda) in enumerate(QUADRANTES_CRUZ):
        with cols_map[i]:
            st.markdown(f"#### {titulo}")
            st.caption(ajuda)
            
            if "swot_cruzada" not in data:
                data["swot_cruzada"] = {}
            if chave not in data["swot_cruzada"]:
                data["swot_cruzada"][chave] = []
            
            itens = data["swot_cruzada"].get(chave, [])
            
            for item in itens:
                if "estrategia" not in item:
                    item["estrategia"] = ""
            
            if itens:
                df = pd.DataFrame(itens)
            else:
                df = pd.DataFrame(columns=["estrategia"])
            
            if "estrategia" not in df.columns:
                df["estrategia"] = ""
            
            df_hash = hash(str(sorted([item.get("estrategia", "") for item in itens]))) if itens else 0
            editor_key = f"editor_cruz_{chave}_{df_hash}"
            
            edited = st.data_editor(
                df, 
                num_rows="dynamic", 
                use_container_width=True, 
                hide_index=True,
                key=editor_key,
                column_config={"estrategia": st.column_config.TextColumn("Estratégia", width="large")},
            )
            
            if edited is not None:
                edited = edited.fillna("")
                novos_itens = []
                for _, row in edited.iterrows():
                    estrategia = row.get("estrategia", "").strip()
                    if estrategia:
                        novos_itens.append({"estrategia": estrategia})
                
                if novos_itens != data["swot_cruzada"][chave]:
                    data["swot_cruzada"][chave] = novos_itens
                    st.rerun()
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                if st.button(f"🤖 Sugerir", key=f"sugerir_cruz_{chave}", width="stretch"):
                    if not any([forcas, fraquezas, oportunidades, ameacas]):
                        st.warning("⚠️ Preencha a Análise SWOT primeiro!")
                    else:
                        with st.spinner(f"Gerando estratégias para {titulo}..."):
                            resultado = gerar_swot_cruzada(chave)
                            if resultado and "itens" in resultado:
                                itens_existentes = data["swot_cruzada"].get(chave, [])
                                existentes_desc = {item["estrategia"].lower().strip() for item in itens_existentes}
                                adicionados = 0
                                for item in resultado["itens"]:
                                    if item and item.lower().strip() not in existentes_desc:
                                        itens_existentes.append({"estrategia": item})
                                        adicionados += 1
                                if adicionados > 0:
                                    data["swot_cruzada"][chave] = itens_existentes
                                    st.success(f"✅ {adicionados} estratégias adicionadas para {titulo}!")
                                    st.rerun()
                                else:
                                    st.info(f"ℹ️ Todas as estratégias sugeridas já existem em {titulo}.")
            
            with col_btn2:
                if st.button(f"🗑️", key=f"limpar_cruz_{chave}", width="stretch"):
                    data["swot_cruzada"][chave] = []
                    st.rerun()

# ---------------- Objetivos, KPIs, Metas ----------------
with tab3:
    st.subheader("Objetivos Estratégicos, KPIs e Metas")
    st.caption("Defina objetivos concretos, o indicador que vai medi-los e a meta com prazo.")

    def gerar_objetivos():
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            estrategias_cruzadas = []
            for q in ["SO", "ST", "WO", "WT"]:
                estrategias_cruzadas += [i.get("estrategia", "") for i in data["swot_cruzada"].get(q, []) if i.get("estrategia")]
            
            estrategias_texto = "; ".join(estrategias_cruzadas) or "nenhuma estratégia definida"
            
            prompt = f"""
            Você é um consultor de planejamento estratégico.
            
            INFORMAÇÕES DA EMPRESA:
            - Nome: {empresa_nome}
            - Setor: {empresa_setor}
            
            ESTRATÉGIAS DA SWOT CRUZADA:
            {estrategias_texto}
            
            Gere de 3 a 5 objetivos estratégicos SMART em português do Brasil.
            Cada objetivo deve ter: objetivo, perspectiva (Financeira/Clientes/Processos internos/Aprendizado e crescimento), KPI, meta e prazo.
            
            Responda APENAS com um JSON no formato:
            {{
                "objetivos": [
                    {{
                        "objetivo": "texto",
                        "perspectiva": "Financeira",
                        "kpi": "texto",
                        "meta": "texto",
                        "prazo": "texto"
                    }}
                ]
            }}
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor de planejamento estratégico. Responda em português do Brasil. Retorne APENAS JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            conteudo = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(conteudo)
            
        except Exception as e:
            st.error(f"Erro na IA: {str(e)}")
            return None

    st.subheader("🚀 Ações com IA")
    col_gerar_obj1, col_gerar_obj2, col_gerar_obj3 = st.columns([3, 1, 1])
    with col_gerar_obj1:
        st.caption("A IA vai gerar objetivos estratégicos baseados na SWOT Cruzada")
    with col_gerar_obj2:
        if st.button("🔄 Gerar Objetivos", width="stretch"):
            with st.spinner("Gerando objetivos estratégicos..."):
                resultado = gerar_objetivos()
                if resultado and "objetivos" in resultado:
                    itens_existentes = data["objetivos"]
                    existentes_desc = {item["objetivo"].lower().strip() for item in itens_existentes}
                    adicionados = 0
                    for obj in resultado["objetivos"]:
                        if obj.get("objetivo") and obj["objetivo"].lower().strip() not in existentes_desc:
                            itens_existentes.append({
                                "objetivo": obj.get("objetivo", ""),
                                "perspectiva": obj.get("perspectiva", "Financeira"),
                                "kpi": obj.get("kpi", ""),
                                "meta": obj.get("meta", ""),
                                "prazo": obj.get("prazo", "")
                            })
                            adicionados += 1
                    if adicionados > 0:
                        data["objetivos"] = itens_existentes
                        st.success(f"✅ {adicionados} objetivos gerados!")
                        st.rerun()
                    else:
                        st.info("ℹ️ Todos os objetivos sugeridos já existem.")
    with col_gerar_obj3:
        if st.button("🗑️ Limpar Objetivos", width="stretch"):
            data["objetivos"] = []
            st.rerun()

    st.divider()

    itens = data["objetivos"]
    
    for item in itens:
        for col in ["objetivo", "perspectiva", "kpi", "meta", "prazo"]:
            if col not in item:
                item[col] = ""
    
    if itens:
        df = pd.DataFrame(itens)
    else:
        df = pd.DataFrame(columns=["objetivo", "perspectiva", "kpi", "meta", "prazo"])
    
    for col in ["objetivo", "perspectiva", "kpi", "meta", "prazo"]:
        if col not in df.columns:
            df[col] = ""
    
    df_hash = hash(str(sorted([str(item) for item in itens]))) if itens else 0
    editor_key = f"editor_objetivos_{df_hash}"
    
    edited = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True,
        key=editor_key,
        column_config={
            "objetivo": st.column_config.TextColumn("Objetivo estratégico", width="large"),
            "perspectiva": st.column_config.SelectboxColumn(
                "Perspectiva", options=["Financeira", "Clientes", "Processos internos", "Aprendizado e crescimento"]
            ),
            "kpi": st.column_config.TextColumn("KPI (indicador)"),
            "meta": st.column_config.TextColumn("Meta"),
            "prazo": st.column_config.TextColumn("Prazo"),
        },
    )
    
    if edited is not None:
        edited = edited.fillna("")
        novos_itens = []
        for _, row in edited.iterrows():
            objetivo = row.get("objetivo", "").strip()
            if objetivo:
                novos_itens.append({
                    "objetivo": objetivo,
                    "perspectiva": row.get("perspectiva", "Financeira"),
                    "kpi": row.get("kpi", ""),
                    "meta": row.get("meta", ""),
                    "prazo": row.get("prazo", ""),
                })
        
        if novos_itens != data["objetivos"]:
            data["objetivos"] = novos_itens
            st.rerun()

# ========== ASSISTENTE IA PARA AJUDA ==========
st.divider()
st.subheader("💬 Tem dúvidas? Consulte nosso Assistente IA")

empresa = data.get("empresa", {})
empresa_nome = empresa.get("nome", "").strip()

if not empresa_nome:
    st.warning(
        "⚠️ Cadastre primeiro os dados da empresa para utilizar o assistente de IA.",
        icon="⚠️"
    )
else:
    contexto = f"""
    SIPE - SISTEMA INTEGRADO DE PLANEJAMENTO ESTRATÉGICO

    EMPRESA:
    {empresa_nome}

    SETOR:
    {empresa.get('setor', 'Não informado')}

    LOCALIZAÇÃO:
    {empresa.get('cidade_estado', 'Não informado')}

    MISSÃO:
    {data['mvv'].get('missao', 'Não definida')}

    VISÃO:
    {data['mvv'].get('visao', 'Não definida')}

    VALORES:
    {', '.join(data['mvv'].get('valores', [])) or 'Não definidos'}

    SWOT CRUZADA:
    """
    for chave, titulo, _ in QUADRANTES_CRUZ:
        itens = data["swot_cruzada"].get(chave, [])
        contexto += f"\n{titulo}:\n"
        if itens:
            for item in itens:
                contexto += f"  • {item.get('estrategia', '')}\n"
        else:
            contexto += "  (vazio)\n"
    
    contexto += "\nOBJETIVOS ESTRATÉGICOS:\n"
    for obj in data.get("objetivos", []):
        contexto += f"  • {obj.get('objetivo', '')} - {obj.get('perspectiva', '')} - {obj.get('kpi', '')} - {obj.get('meta', '')} - {obj.get('prazo', '')}\n"

    system_prompt = """
    Você é um assistente especialista em Planejamento Estratégico.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Definir Missão, Visão e Valores
    - Construir a SWOT Cruzada
    - Definir objetivos estratégicos SMART
    - Conectar as diferentes partes do planejamento
    """

    render_chat(
        messages_key="messages_planejamento",
        placeholder="Pergunte ao assistente sobre o planejamento estratégico...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Plano de Ação", width="stretch"):
        st.switch_page("pages/6_✅_Plano_de_Ação_5W2H.py")
