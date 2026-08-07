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

st.set_page_config(page_title="Análise SWOT", page_icon="🎯", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
module_started(
    Module.SWOT
)
sidebar_data_controls()

st.title("🎯 Análise SWOT")
st.caption(
    "Forças e Fraquezas são fatores internos (você controla). Oportunidades e Ameaças são "
    "fatores externos — aqui você pode importar automaticamente o que já foi identificado na "
    "Análise PESTEL e nas 5 Forças de Porter."
)

def itens_pestel_por_tipo(tipo):
    resultado = []
    if "pestel" in data:
        for cat, itens in data["pestel"].items():
            for item in itens:
                if item.get("tipo") == tipo and item.get("descricao"):
                    resultado.append(f"[PESTEL-{cat}] {item['descricao']}")
    return resultado

def itens_porter_alerta():
    alertas = []
    if "porter_analise" in data:
        for forca in data["porter_analise"].values():
            if forca.get("intensidade", 0) >= 4:
                nota = f" — {forca['notas']}" if forca.get("notas") else ""
                alertas.append(f"[Porter] {forca.get('nome', 'Força')} está com intensidade alta{nota}")
    return alertas

col_import1, col_import2 = st.columns(2)
with col_import1:
    if st.button("⬇️ Importar Oportunidades da Análise PESTEL", width="stretch"):
        novas = itens_pestel_por_tipo("Oportunidade")
        existentes = {i["descricao"] for i in data["swot"]["oportunidades"]}
        for texto in novas:
            if texto not in existentes:
                data["swot"]["oportunidades"].append({"descricao": texto})
        st.success(f"{len(novas)} itens verificados/importados.")
        st.rerun()
with col_import2:
    if st.button("⬇️ Importar Ameaças do PESTEL + Porter", width="stretch"):
        novas = itens_pestel_por_tipo("Ameaça") + itens_porter_alerta()
        existentes = {i["descricao"] for i in data["swot"]["ameacas"]}
        for texto in novas:
            if texto not in existentes:
                data["swot"]["ameacas"].append({"descricao": texto})
        st.success(f"{len(novas)} itens verificados/importados.")
        st.rerun()

st.divider()

QUADRANTES = [
    ("forcas", "💪 Forças (interno)", "Vantagens internas: o que a empresa faz bem, recursos únicos, diferenciais."),
    ("fraquezas", "⚠️ Fraquezas (interno)", "Pontos internos a melhorar: limitações de recursos, processos, equipe."),
    ("oportunidades", "🌱 Oportunidades (externo)", "Fatores externos favoráveis que a empresa pode aproveitar."),
    ("ameacas", "🌩️ Ameaças (externo)", "Fatores externos desfavoráveis que podem prejudicar a empresa."),
]

def gerar_analise_swot(quadrante=None):
    """Gera análise SWOT com IA para um quadrante específico ou todos"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
        
        empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
        empresa_setor = data.get("empresa", {}).get("setor", "não informado")
        
        # Coletar dados do PESTEL e Porter para contexto
        pestel_oportunidades = []
        pestel_ameacas = []
        if "pestel" in data:
            for cat, itens in data["pestel"].items():
                for item in itens:
                    if item.get("descricao"):
                        if item.get("tipo") == "Oportunidade":
                            pestel_oportunidades.append(f"[{cat}] {item['descricao']}")
                        elif item.get("tipo") == "Ameaça":
                            pestel_ameacas.append(f"[{cat}] {item['descricao']}")
        
        porter_alertas = []
        if "porter_analise" in data:
            for forca in data["porter_analise"].values():
                if forca.get("intensidade", 0) >= 4:
                    porter_alertas.append(f"{forca.get('nome', 'Força')} - {forca.get('notas', '')}")
        
        contexto_adicional = ""
        if pestel_oportunidades:
            contexto_adicional += f"\nOPORTUNIDADES IDENTIFICADAS NO PESTEL:\n" + "\n".join([f"- {item}" for item in pestel_oportunidades[:5]])
        if pestel_ameacas:
            contexto_adicional += f"\nAMEAÇAS IDENTIFICADAS NO PESTEL:\n" + "\n".join([f"- {item}" for item in pestel_ameacas[:5]])
        if porter_alertas:
            contexto_adicional += f"\nALERTAS DAS 5 FORÇAS DE PORTER:\n" + "\n".join([f"- {item}" for item in porter_alertas[:5]])
        
        if quadrante:
            chave, titulo, ajuda = next(q for q in QUADRANTES if q[0] == quadrante)
            
            if chave in ["oportunidades", "ameacas"]:
                contexto_adicional = f"\nDADOS JÁ IDENTIFICADOS EM ANÁLISES ANTERIORES:{contexto_adicional}\n"
            
            prompt = f"""
            Você é um consultor de estratégia especialista em análise SWOT.
            
            INFORMAÇÕES DA EMPRESA:
            - Nome: {empresa_nome}
            - Setor: {empresa_setor}
            {contexto_adicional}
            
            Quadrante SWOT: {titulo}
            Descrição: {ajuda}
            
            Gere uma lista de 3 a 5 itens em português do Brasil para este quadrante.
            {'Considere os dados de análises anteriores fornecidos acima.' if contexto_adicional else ''}
            Responda APENAS com um JSON: {{"itens": ["item1", "item2", "item3"]}}
            """
        else:
            prompt = f"""
            Você é um consultor de estratégia especialista em análise SWOT.
            
            INFORMAÇÕES DA EMPRESA:
            - Nome: {empresa_nome}
            - Setor: {empresa_setor}
            {contexto_adicional}
            
            Gere uma análise SWOT completa com os 4 quadrantes em português do Brasil.
            {'Considere os dados de análises anteriores fornecidos acima para oportunidades e ameaças.' if contexto_adicional else ''}
            
            FORMATO DE SAÍDA: Retorne APENAS um JSON com:
            {{
                "forcas": ["item1", "item2", "item3"],
                "fraquezas": ["item1", "item2", "item3"],
                "oportunidades": ["item1", "item2", "item3"],
                "ameacas": ["item1", "item2", "item3"]
            }}
            """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "Você é um consultor especialista em análise SWOT. Responda em português do Brasil. Retorne APENAS JSON válido."},
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
    st.caption("A IA vai gerar sugestões para todos os 4 quadrantes da SWOT")
with col_gerar2:
    if st.button("🔄 Gerar SWOT Completa", width="stretch"):
        with st.spinner("Gerando análise SWOT completa..."):
            resultado = gerar_analise_swot()
            if resultado:
                total_adicionados = 0
                for chave, _, _ in QUADRANTES:
                    if chave in resultado and resultado[chave]:
                        itens_existentes = data["swot"].get(chave, [])
                        existentes_desc = {item["descricao"].lower().strip() for item in itens_existentes}
                        for item in resultado[chave]:
                            if item and item.lower().strip() not in existentes_desc:
                                itens_existentes.append({"descricao": item})
                                total_adicionados += 1
                        data["swot"][chave] = itens_existentes
                if total_adicionados > 0:
                    st.success(f"✅ {total_adicionados} itens adicionados à SWOT!")
                    st.rerun()
                else:
                    st.info("ℹ️ Todos os itens sugeridos já existem.")
with col_gerar3:
    if st.button("🗑️ Limpar SWOT", width="stretch"):
        for chave, _, _ in QUADRANTES:
            data["swot"][chave] = []
        st.rerun()

st.divider()

col_a, col_b = st.columns(2)
cols_map = {0: col_a, 1: col_b, 2: col_a, 3: col_b}

for i, (chave, titulo, ajuda) in enumerate(QUADRANTES):
    with cols_map[i]:
        st.markdown(f"#### {titulo}")
        st.caption(ajuda)
        
        if "swot" not in data:
            data["swot"] = {}
        if chave not in data["swot"]:
            data["swot"][chave] = []
        
        itens = data["swot"].get(chave, [])
        
        for item in itens:
            if "descricao" not in item:
                item["descricao"] = ""
        
        if itens:
            df = pd.DataFrame(itens)
        else:
            df = pd.DataFrame(columns=["descricao"])
        
        df_hash = hash(str(sorted([item.get("descricao", "") for item in itens]))) if itens else 0
        editor_key = f"editor_swot_{chave}_{df_hash}"
        
        edited = st.data_editor(
            df, 
            num_rows="dynamic", 
            width="stretch",
            key=editor_key, 
            hide_index=True,
            column_config={"descricao": st.column_config.TextColumn("Item", width="large")},
        )
        
        if edited is not None:
            edited = edited.fillna("")
            novos_itens = []
            for _, row in edited.iterrows():
                descricao = row.get("descricao", "").strip()
                if descricao:
                    novos_itens.append({"descricao": descricao})
            
            if novos_itens != data["swot"][chave]:
                data["swot"][chave] = novos_itens
                st.rerun()
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button(f"🤖 Sugerir", key=f"sugerir_{chave}", width="stretch"):
                with st.spinner(f"Gerando sugestões para {titulo}..."):
                    resultado = gerar_analise_swot(chave)
                    if resultado and "itens" in resultado and isinstance(resultado["itens"], list):
                        itens_existentes = data["swot"].get(chave, [])
                        existentes_desc = {item["descricao"].lower().strip() for item in itens_existentes}
                        adicionados = 0
                        for item in resultado["itens"]:
                            if item and isinstance(item, str) and item.lower().strip() not in existentes_desc:
                                itens_existentes.append({"descricao": item})
                                adicionados += 1
                        if adicionados > 0:
                            data["swot"][chave] = itens_existentes
                            st.success(f"✅ {adicionados} itens adicionados para {titulo}!")
                            st.rerun()
                        else:
                            st.info(f"ℹ️ Todos os itens sugeridos já existem em {titulo}.")
                    else:
                        st.warning("A IA não retornou itens válidos. Tente novamente.")
        
        with col_btn2:
            if st.button(f"🗑️", key=f"limpar_{chave}", width="stretch"):
                data["swot"][chave] = []
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
    swot_atual = ""
    for chave, titulo, _ in QUADRANTES:
        itens = data["swot"].get(chave, [])
        swot_atual += f"\n{titulo}:\n"
        if itens:
            for item in itens:
                swot_atual += f"  • {item.get('descricao', '')}\n"
        else:
            swot_atual += "  (vazio)\n"

    contexto = f"""
    SIPE - SISTEMA INTEGRADO DE PLANEJAMENTO ESTRATÉGICO

    EMPRESA:
    {empresa_nome}

    SETOR:
    {empresa.get('setor', 'Não informado')}

    LOCALIZAÇÃO:
    {empresa.get('cidade_estado', 'Não informado')}

    ANÁLISE SWOT ATUAL:
    {swot_atual}
    """

    system_prompt = """
    Você é um assistente especialista em Análise SWOT e Estratégia.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Identificar forças, fraquezas, oportunidades e ameaças
    - Classificar corretamente cada item nos quadrantes da SWOT
    - Relacionar os fatores internos e externos
    - Entender como a SWOT se conecta com as demais análises
    """

    render_chat(
        messages_key="messages_swot",
        placeholder="Pergunte ao assistente sobre sua análise SWOT...",
        system_prompt=system_prompt,
        context=contexto,
    )

st.divider()
st.info(
    "💡 Depois de concluir a SWOT, vá para **🧭 Planejamento Estratégico** para construir "
    "a **SWOT Cruzada** (cruzamento de Forças/Fraquezas com Oportunidades/Ameaças)."
)

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Planejamento Estratégico", width="stretch"):
        st.switch_page("pages/5_🧭_Planejamento_Estratégico.py")
