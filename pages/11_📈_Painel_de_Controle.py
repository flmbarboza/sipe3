import pandas as pd
import streamlit as st
import json
import re
from datetime import datetime
from utils.data_manager import init_data, get_data, sidebar_data_controls
from utils.chat import render_chat
from openai import OpenAI
from analytics import Module
from analytics import module_started
from analytics import module_completed
from analytics import track
from analytics import EventType

st.set_page_config(page_title="Dashboard Executivo", page_icon="📊", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
module_started(
    Module.PAINEL
)
sidebar_data_controls()

st.title("📊 Dashboard Executivo")
st.caption(
    "Visão consolidada de todo o planejamento estratégico. Acompanhe o desempenho da empresa "
    "em um único painel."
)

# ========== FUNÇÕES DE CONSOLIDAÇÃO ==========
def contar_itens():
    """Conta itens em todas as seções do sistema"""
    return {
        "empresa": 1 if data.get("empresa", {}).get("nome") else 0,
        "bmc": len([v for v in data.get("bmc", {}).values() if v]),
        "pestel": sum([len([i for i in itens if i.get("descricao")]) for itens in data.get("pestel", {}).values()]),
        "porter": len(data.get("porter_analise", {})),
        "swot": sum([len([i for i in itens if i.get("descricao")]) for itens in data.get("swot", {}).values()]),
        "objetivos": len([o for o in data.get("objetivos", []) if o.get("objetivo")]),
        "acoes_5w2h": len([a for a in data.get("acao_5w2h", []) if a.get("what")]),
        "departamentos": len(data.get("departamentos", {})),
        "financeiro": 1 if data.get("financeiro", {}).get("receitas") or data.get("financeiro", {}).get("custos") else 0
    }

def calcular_progresso():
    """Calcula o progresso geral do planejamento"""
    total_secoes = 9
    preenchidas = 0
    
    if data.get("bmc"):
        if any(data["bmc"].values()):
            preenchidas += 1
    
    if data.get("pestel"):
        if any([any([i.get("descricao") for i in itens]) for itens in data["pestel"].values()]):
            preenchidas += 1
    
    if data.get("porter_analise"):
        if any([v.get("notas") for v in data["porter_analise"].values()]):
            preenchidas += 1
    
    if data.get("swot"):
        if any([any([i.get("descricao") for i in itens]) for itens in data["swot"].values()]):
            preenchidas += 1
    
    if data.get("mvv"):
        if data["mvv"].get("missao") or data["mvv"].get("visao") or data["mvv"].get("valores"):
            preenchidas += 1
    
    if data.get("objetivos"):
        if any([o.get("objetivo") for o in data["objetivos"]]):
            preenchidas += 1
    
    if data.get("acao_5w2h"):
        if any([a.get("what") for a in data["acao_5w2h"]]):
            preenchidas += 1
    
    if data.get("departamentos"):
        if any([any([v for v in depto.values() if v]) for depto in data["departamentos"].values()]):
            preenchidas += 1
    
    if data.get("financeiro"):
        if data["financeiro"].get("receitas") or data["financeiro"].get("custos"):
            preenchidas += 1
    
    return (preenchidas / total_secoes) * 100

def calcular_status_acoes():
    """Calcula o status das ações do sistema"""
    total = 0
    concluidas = 0
    andamento = 0
    nao_iniciadas = 0
    atrasadas = 0
    
    for acao in data.get("acao_5w2h", []):
        if acao.get("what"):
            total += 1
            status = acao.get("status", "Não iniciado")
            if status == "Concluído":
                concluidas += 1
            elif status == "Em andamento":
                andamento += 1
            elif status == "Atrasado":
                atrasadas += 1
            else:
                nao_iniciadas += 1
    
    for depto in data.get("departamentos", {}).values():
        for acao in depto.get("acoes", []):
            if acao.get("Ação"):
                total += 1
                status = acao.get("Situação", "Não iniciado")
                if status == "Concluído":
                    concluidas += 1
                elif status == "Em andamento":
                    andamento += 1
                elif status == "Atrasado":
                    atrasadas += 1
                else:
                    nao_iniciadas += 1
    
    return {
        "total": total,
        "concluidas": concluidas,
        "andamento": andamento,
        "nao_iniciadas": nao_iniciadas,
        "atrasadas": atrasadas
    }

# ========== DADOS CONSOLIDADOS ==========
contagens = contar_itens()
progresso = calcular_progresso()
status_acoes = calcular_status_acoes()

# ========== EXIBIÇÃO ==========

# ---------- MÉTRICAS PRINCIPAIS ----------
st.subheader("📈 Métricas Principais")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Progresso", f"{progresso:.0f}%")
with col2:
    st.metric("Ações Totais", status_acoes["total"])
with col3:
    st.metric("Ações Concluídas", status_acoes["concluidas"], 
              delta=f"{status_acoes['concluidas']/status_acoes['total']*100:.0f}%" if status_acoes["total"] > 0 else "0%")
with col4:
    st.metric("Departamentos", contagens["departamentos"])
with col5:
    st.metric("Objetivos", contagens["objetivos"])

st.divider()

# ---------- PROGRESSO POR SEÇÃO ----------
st.subheader("📊 Progresso por Seção")

col_prog1, col_prog2 = st.columns(2)

with col_prog1:
    secao_status = {
        "Empresa": contagens["empresa"],
        "BMC": contagens["bmc"],
        "PESTEL": contagens["pestel"],
        "Porter": contagens["porter"],
        "SWOT": contagens["swot"],
        "MVV": 1 if data.get("mvv", {}).get("missao") or data.get("mvv", {}).get("visao") else 0
    }
    
    df_secoes = pd.DataFrame({
        "Seção": list(secao_status.keys()),
        "Status": ["✅" if v > 0 else "❌" for v in secao_status.values()],
        "Itens": list(secao_status.values())
    })
    
    st.dataframe(df_secoes, use_container_width=True, hide_index=True)

with col_prog2:
    df_progresso = pd.DataFrame({
        "Seção": list(secao_status.keys()),
        "Itens": list(secao_status.values())
    }).set_index("Seção")
    st.bar_chart(df_progresso)

st.divider()

# ---------- STATUS DAS AÇÕES ----------
st.subheader("📋 Status das Ações")

if status_acoes["total"] > 0:
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("✅ Concluídas", status_acoes["concluidas"])
            st.metric("🔄 Em andamento", status_acoes["andamento"])
        with col_s2:
            st.metric("⏳ Não iniciadas", status_acoes["nao_iniciadas"])
            st.metric("⚠️ Atrasadas", status_acoes["atrasadas"])
    
    with col_status2:
        df_status = pd.DataFrame({
            "Status": ["Concluídas", "Em andamento", "Não iniciadas", "Atrasadas"],
            "Quantidade": [status_acoes["concluidas"], status_acoes["andamento"], 
                          status_acoes["nao_iniciadas"], status_acoes["atrasadas"]]
        }).set_index("Status")
        st.bar_chart(df_status)
else:
    st.info("Nenhuma ação cadastrada ainda. Comece criando ações no Plano de Ação ou nos Planos Departamentais.")

st.divider()

# ---------- RESUMO DOS DEPARTAMENTOS ----------
st.subheader("🏢 Resumo dos Departamentos")

if data.get("departamentos"):
    depto_resumo = []
    for depto, info in data["departamentos"].items():
        depto_resumo.append({
            "Departamento": depto,
            "Objetivos": len(info.get("objetivos", [])),
            "Ações": len(info.get("acoes", [])),
            "Indicadores": len(info.get("indicadores", [])),
            "Recursos": len(info.get("recursos", []))
        })
    
    df_depto = pd.DataFrame(depto_resumo)
    st.dataframe(df_depto, use_container_width=True, hide_index=True)
    
    df_depto_grafico = df_depto.set_index("Departamento")[["Objetivos", "Ações", "Indicadores"]]
    st.bar_chart(df_depto_grafico)
else:
    st.info("Nenhum departamento cadastrado. Crie os planos departamentais primeiro.")

st.divider()

# ---------- PRÓXIMAS ETAPAS ----------
st.subheader("📌 Próximas Etapas Recomendadas")

proximas_etapas = []

if not data.get("empresa", {}).get("nome"):
    proximas_etapas.append("🏢 Cadastre os dados da empresa na página inicial")
if not any(data.get("bmc", {}).values()):
    proximas_etapas.append("📋 Preencha o Business Model Canvas")
if not any([any([i.get("descricao") for i in itens]) for itens in data.get("pestel", {}).values()]):
    proximas_etapas.append("🌍 Complete a Análise PESTEL")
if not data.get("porter_analise") or not any([v.get("notas") for v in data["porter_analise"].values()]):
    proximas_etapas.append("⚔️ Realize a análise das 5 Forças de Porter")
if not any([any([i.get("descricao") for i in itens]) for itens in data.get("swot", {}).values()]):
    proximas_etapas.append("🎯 Elabore a Análise SWOT")
if not data.get("objetivos") or not any([o.get("objetivo") for o in data["objetivos"]]):
    proximas_etapas.append("🎯 Defina os Objetivos Estratégicos")
if not data.get("acao_5w2h") or not any([a.get("what") for a in data["acao_5w2h"]]):
    proximas_etapas.append("✅ Crie o Plano de Ação 5W2H")
if not data.get("departamentos") or not any([any([v for v in depto.values() if v]) for depto in data["departamentos"].values()]):
    proximas_etapas.append("🏢 Desenvolva os Planos Departamentais")

if proximas_etapas:
    for etapa in proximas_etapas:
        st.caption(f"• {etapa}")
else:
    st.success("🎉 Parabéns! Todas as etapas do planejamento estratégico estão concluídas!")

st.divider()

# ---------- INSIGHTS DA IA ----------
st.subheader("🤖 Insights da IA")

if st.button("🔍 Gerar Insights do Planejamento", width="stretch"):
    with st.spinner("Analisando o planejamento estratégico..."):
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            resumo = f"""
            EMPRESA: {empresa_nome}
            SETOR: {empresa_setor}
            
            PROGRESSO:
            - Completo: {progresso:.0f}%
            - Departamentos: {contagens['departamentos']}
            - Objetivos: {contagens['objetivos']}
            - Ações: {status_acoes['total']} ({status_acoes['concluidas']} concluídas)
            - Análises realizadas: PESTEL, Porter, SWOT
            """
            
            prompt = f"""
            Você é um consultor sênior de estratégia analisando um planejamento estratégico.
            
            {resumo}
            
            Com base nessas informações, gere 3 insights estratégicos principais e 3 recomendações práticas.
            Responda em português do Brasil, de forma objetiva e direta.
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor sênior de estratégia. Responda em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            insights = response.choices[0].message.content
            st.markdown(insights)
            
            st.session_state["dashboard_insights"] = insights
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar insights: {str(e)}")

if "dashboard_insights" in st.session_state:
    st.markdown(st.session_state["dashboard_insights"])

# ========== ASSISTENTE IA ==========
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
    DASHBOARD EXECUTIVO:
    - Progresso: {progresso:.0f}%
    - Departamentos: {contagens['departamentos']}
    - Objetivos: {contagens['objetivos']}
    - Ações: {status_acoes['total']} (concluídas: {status_acoes['concluidas']})
    - PESTEL: {contagens['pestel']} itens
    - SWOT: {contagens['swot']} itens
    """

    system_prompt = """
    Você é um assistente especialista em Planejamento Estratégico.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Compreender o progresso do planejamento
    - Analisar métricas e indicadores
    - Identificar próximas etapas prioritárias
    - Tomar decisões baseadas em dados
    - Manter o foco nos objetivos estratégicos
    """

    render_chat(
        messages_key="messages_dashboard",
        placeholder="Pergunte ao assistente sobre o planejamento estratégico...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Gerar Relatório", width="stretch"):
        st.switch_page("pages/12_📄_Relatório_Completo.py")
