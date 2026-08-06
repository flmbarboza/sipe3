import streamlit as st
from utils.data_manager import init_data, get_data, sidebar_data_controls
from utils.ai_helper import sidebar_api_key_input
from utils.chat import render_chat
from analytics import (
    init_page, module_started, module_completed,
    track, track_navigation, track_chat_message,
    Module
)

st.set_page_config(
    page_title="Gestor Estratégico",
    page_icon="🧭",
    layout="wide",
)

init_page(Module.HOME)
init_data()
data = get_data()

# ---------- Barra lateral (comum a todas as páginas) ----------
st.sidebar.title("🧭 Gestor Estratégico")
sidebar_data_controls()

# ---------- Conteúdo da Home ----------
st.title("🧭 Gestor Estratégico")
st.caption("Ferramenta de apoio ao planejamento estratégico de empresas")

st.markdown("""
Bem-vindo! Este aplicativo guia você pela construção do planejamento estratégico
completo da sua empresa, do modelo de negócio ao plano de ação. Use o menu na
barra lateral para navegar entre as etapas.
""")

module_started(Module.HOME)

with st.form("form_empresa"):
    st.subheader("🏢 Dados da empresa")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome da empresa", value=data["empresa"]["nome"])
        setor = st.text_input("Setor / Segmento", value=data["empresa"]["setor"])
    with col2:
        cidade = st.text_input("Cidade/Estado", value=data["empresa"]["cidade_estado"])
        responsavel = st.text_input("Responsável pelo planejamento", value=data["empresa"]["responsavel"])
    salvar = st.form_submit_button("Salvar dados da empresa", width="stretch")
    if salvar:
        data["empresa"].update(
            {"nome": nome, "setor": setor, "cidade_estado": cidade, "responsavel": responsavel}
        )
        track("empresa_saved", Module.HOME, metadata={
            "nome": nome,
            "setor": setor,
            "has_data": bool(nome or setor)
        })
        st.success("Dados da empresa salvos!")

st.divider()

st.subheader("🗺️ Roteiro do planejamento")

etapas = [
    "📋 Business Model Canvas",
    "🌍 Análise PESTEL",
    "⚔️ 5 Forças de Porter",
    "🎯 Análise SWOT",
    "🧭 Planejamento Estratégico",
    "✅ Plano de Ação (5W2H)",
    "📋 Planos por Função",
    "💰 Orçamento",
    "🛃 Monitoramento",
    "🔄 Revisão Estratégica",
    "📈 Painel de Controle",
    "📄 Relatório Completo",
]

cols = st.columns(2)
for i, etapa in enumerate(etapas):
    with cols[i % 2]:
        st.markdown(f"**{etapa}**")

st.divider()

st.subheader("📊 Resumo do Planejamento")

# Calcular progresso
total_secoes = 11
preenchidas = 0

if data.get("empresa", {}).get("nome"):
    preenchidas += 1
if data.get("bmc") and any(data["bmc"].values()):
    preenchidas += 1
if data.get("pestel") and any([any([i.get("descricao") for i in itens]) for itens in data["pestel"].values()]):
    preenchidas += 1
if data.get("porter_analise") and any([v.get("notas") for v in data["porter_analise"].values()]):
    preenchidas += 1
if data.get("swot") and any([any([i.get("descricao") for i in itens]) for itens in data["swot"].values()]):
    preenchidas += 1
if data.get("mvv") and (data["mvv"].get("missao") or data["mvv"].get("visao")):
    preenchidas += 1
if data.get("objetivos") and any([o.get("objetivo") for o in data["objetivos"]]):
    preenchidas += 1
if data.get("acao_5w2h") and any([a.get("what") for a in data["acao_5w2h"]]):
    preenchidas += 1
if data.get("departamentos") and any([any([v for v in depto.values() if v]) for depto in data["departamentos"].values()]):
    preenchidas += 1
if data.get("orcamento") and (data["orcamento"].get("receitas") or data["orcamento"].get("investimentos")):
    preenchidas += 1
if data.get("monitoramento") and data["monitoramento"].get("alertas"):
    preenchidas += 1

progresso = (preenchidas / total_secoes) * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Progresso Total", f"{progresso:.0f}%")
with col2:
    st.metric("Seções Preenchidas", f"{preenchidas}/{total_secoes}")
with col3:
    total_acoes = len([a for a in data.get("acao_5w2h", []) if a.get("what")])
    st.metric("Ações Totais", total_acoes)
with col4:
    deptos = len(data.get("departamentos", {}))
    st.metric("Departamentos", deptos)

# Barra de progresso
st.progress(progresso / 100, text=f"Progresso do planejamento: {progresso:.0f}%")

st.info(
    "💡 Use o botão **'⬇️ Baixar dados (.json)'** na barra lateral sempre que quiser "
    "salvar seu progresso, e **'⬆️ Carregar dados (.json)'** para retomar depois.",
    icon="💡",
)

# ========== ASSISTENTE IA PARA AJUDA ==========
st.divider()
st.subheader("💬 Tem dúvidas? Consulte nosso Assistente IA")

empresa = data.get("empresa", {})

empresa_nome = empresa.get("nome", "").strip()
empresa_setor = empresa.get("setor", "").strip()
empresa_cidade = empresa.get("cidade_estado", "").strip()
empresa_responsavel = empresa.get("responsavel", "").strip()

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
    {empresa_setor or "Não informado"}

    LOCALIZAÇÃO:
    {empresa_cidade or "Não informado"}

    RESPONSÁVEL:
    {empresa_responsavel or "Não informado"}

    PROGRESSO DO PLANEJAMENTO:
    {progresso:.0f}%

    SEÇÕES PREENCHIDAS:
    {preenchidas}/{total_secoes}

    TOTAL DE AÇÕES:
    {len([a for a in data.get('acao_5w2h', []) if a.get('what')])}

    DEPARTAMENTOS:
    {len(data.get('departamentos', {}))}
    """

    system_prompt = """
    Você é um assistente especialista em Planejamento Estratégico.

    Auxilie o usuário na construção do planejamento estratégico da empresa.

    O SIPE possui as seguintes etapas:

    1. Business Model Canvas
    2. Análise PESTEL
    3. 5 Forças de Porter
    4. Análise SWOT
    5. Planejamento Estratégico
    6. Plano de Ação 5W2H
    7. Planos por Função
    8. Orçamento
    9. Monitoramento
    10. Revisão Estratégica
    11. Painel de Controle
    12. Relatório Completo

    Responda em português do Brasil, de forma prática e objetiva.
    """

    render_chat(
        messages_key="messages_home",
        placeholder="Pergunte ao assistente sobre o que faz o SIPE...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Canvas Business Model", width="stretch"):
        track_navigation(Module.HOME, "1_📋_Business_Model_Canvas.py")
        st.switch_page("pages/1_📋_Business_Model_Canvas.py")
