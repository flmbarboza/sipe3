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

st.set_page_config(page_title="Monitoramento Estratégico", page_icon="📊", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
sidebar_data_controls()

st.title("📊 Monitoramento Estratégico")
module_started(
    Module.MONITORAMENTO
)
st.caption(
    "Acompanhe o desempenho dos KPIs, status das ações e indicadores departamentais. "
    "Identifique alertas e mantenha o planejamento sob controle."
)

# ========== INICIALIZAR DADOS ==========
if "monitoramento" not in data:
    data["monitoramento"] = {
        "kpis_estrategicos": [],
        "alertas": [],
        "historico": {}
    }

# ========== FUNÇÕES DE CONSOLIDAÇÃO ==========
def consolidar_kpis_estrategicos():
    """Consolida KPIs estratégicos de todas as fontes"""
    kpis = []
    
    if "objetivos" in data:
        for obj in data["objetivos"]:
            if obj.get("objetivo") and obj.get("kpi"):
                kpis.append({
                    "KPI": obj.get("kpi", ""),
                    "Origem": "Objetivo Estratégico",
                    "Meta": obj.get("meta", ""),
                    "Prazo": obj.get("prazo", ""),
                    "Status": "Em andamento"
                })
    
    if "departamentos" in data:
        for depto, info in data["departamentos"].items():
            for indicador in info.get("indicadores", []):
                if indicador.get("Indicador"):
                    kpis.append({
                        "KPI": indicador.get("Indicador", ""),
                        "Origem": f"Departamento {depto}",
                        "Meta": indicador.get("Meta", ""),
                        "Prazo": indicador.get("Frequência", ""),
                        "Status": "Em andamento"
                    })
    
    return kpis

def consolidar_acoes():
    """Consolida todas as ações do sistema"""
    acoes = []
    
    if "acao_5w2h" in data:
        for acao in data["acao_5w2h"]:
            if acao.get("what"):
                acoes.append({
                    "Ação": acao.get("what", ""),
                    "Origem": "Plano 5W2H",
                    "Responsável": acao.get("who", ""),
                    "Prazo": acao.get("when", ""),
                    "Status": acao.get("status", "Não iniciado")
                })
    
    if "departamentos" in data:
        for depto, info in data["departamentos"].items():
            for acao in info.get("acoes", []):
                if acao.get("Ação"):
                    acoes.append({
                        "Ação": acao.get("Ação", ""),
                        "Origem": f"Departamento {depto}",
                        "Responsável": acao.get("Responsável", ""),
                        "Prazo": acao.get("Data fim", ""),
                        "Status": acao.get("Situação", "Não iniciado")
                    })
    
    return acoes

def gerar_alertas(acoes, kpis):
    """Gera alertas automáticos baseados no status"""
    alertas = []
    hoje = datetime.now()
    
    for acao in acoes:
        if acao.get("Status") in ["Não iniciado", "Em andamento"] and acao.get("Prazo"):
            try:
                prazo = datetime.strptime(acao["Prazo"], "%d/%m/%Y")
                if prazo < hoje:
                    alertas.append({
                        "Tipo": "Ação Atrasada",
                        "Descrição": f"Ação '{acao['Ação']}' está atrasada",
                        "Prioridade": "Alta",
                        "Origem": acao["Origem"]
                    })
            except:
                pass
    
    for kpi in kpis:
        if "meta" in kpi and kpi.get("meta"):
            try:
                meta = float(kpi["meta"].replace("%", "").replace("R$", "").strip())
                if meta == 0:
                    alertas.append({
                        "Tipo": "KPI Crítico",
                        "Descrição": f"KPI '{kpi['KPI']}' está com meta zerada",
                        "Prioridade": "Média",
                        "Origem": kpi["Origem"]
                    })
            except:
                pass
    
    return alertas

# ========== CONSOLIDAR DADOS ==========
kpis_consolidados = consolidar_kpis_estrategicos()
acoes_consolidados = consolidar_acoes()
alertas_gerados = gerar_alertas(acoes_consolidados, kpis_consolidados)

# ========== FUNÇÕES DE RENDERIZAÇÃO ==========
def render_tabela(dados, colunas, titulo, key):
    """Renderiza uma tabela com dados consolidados"""
    if dados:
        df = pd.DataFrame(dados)
        for col in colunas:
            if col not in df.columns:
                df[col] = ""
        df = df[colunas]
    else:
        df = pd.DataFrame(columns=colunas)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

# ========== EXIBIÇÃO ==========

# ---------- KPIs Estratégicos ----------
with st.expander("🎯 KPIs Estratégicos", expanded=True):
    st.markdown("### KPIs Estratégicos Consolidados")
    st.caption("KPIs extraídos dos objetivos estratégicos e planos departamentais")
    
    if kpis_consolidados:
        colunas_kpis = ["KPI", "Origem", "Meta", "Prazo", "Status"]
        render_tabela(kpis_consolidados, colunas_kpis, "KPIs", "kpis_estrategicos")
    else:
        st.info("Nenhum KPI estratégico encontrado. Defina objetivos e indicadores nos planos.")

# ---------- KPIs Departamentais ----------
with st.expander("📊 KPIs Departamentais", expanded=True):
    st.markdown("### KPIs por Departamento")
    
    if "departamentos" in data:
        for depto, info in data["departamentos"].items():
            if info.get("indicadores"):
                st.markdown(f"**{depto}**")
                df = pd.DataFrame(info["indicadores"])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption(f"{depto}: Nenhum indicador cadastrado")
    else:
        st.info("Nenhum departamento cadastrado.")

# ---------- Dashboard ----------
with st.expander("📈 Dashboard", expanded=True):
    st.markdown("### Dashboard de Desempenho")
    
    col_dash1, col_dash2, col_dash3 = st.columns(3)
    with col_dash1:
        total_acoes = len(acoes_consolidados)
        st.metric("Total de Ações", total_acoes)
    with col_dash2:
        concluidas = len([a for a in acoes_consolidados if a.get("Status") == "Concluído"])
        st.metric("Ações Concluídas", concluidas, delta=f"{concluidas/total_acoes*100:.0f}%" if total_acoes > 0 else "0%")
    with col_dash3:
        kpis_total = len(kpis_consolidados)
        st.metric("Total de KPIs", kpis_total)
    
    if acoes_consolidados:
        st.markdown("#### Status das Ações")
        df_acoes = pd.DataFrame(acoes_consolidados)
        status_count = df_acoes["Status"].value_counts()
        st.bar_chart(status_count)
        
        st.markdown("#### Origem das Ações")
        origem_count = df_acoes["Origem"].value_counts().head(10)
        st.bar_chart(origem_count)

# ---------- Evolução das Metas ----------
with st.expander("📈 Evolução das Metas"):
    st.markdown("### Evolução das Metas")
    st.caption("Acompanhe a evolução dos indicadores ao longo do tempo")
    
    if kpis_consolidados:
        kpi_selecionado = st.selectbox(
            "Selecione um KPI para acompanhar",
            options=[k["KPI"] for k in kpis_consolidados if k.get("KPI")]
        )
        
        if kpi_selecionado:
            import random
            meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
            valores = [random.randint(50, 100) for _ in range(12)]
            
            df_evolucao = pd.DataFrame({
                "Mês": meses,
                "Valor": valores
            })
            st.line_chart(df_evolucao.set_index("Mês"))
            
            kpi_atual = next((k for k in kpis_consolidados if k["KPI"] == kpi_selecionado), {})
            if kpi_atual.get("Meta"):
                st.metric("Meta", kpi_atual.get("Meta", ""))
    else:
        st.info("Nenhum KPI disponível para acompanhamento.")

# ---------- Status das Ações (Kanban) ----------
with st.expander("📋 Status das Ações"):
    st.markdown("### Status das Ações - Visão Kanban")
    
    if acoes_consolidados:
        df_acoes = pd.DataFrame(acoes_consolidados)
        
        col_kanban1, col_kanban2, col_kanban3, col_kanban4 = st.columns(4)
        
        with col_kanban1:
            st.markdown("**🔴 Não iniciado**")
            nao_iniciados = df_acoes[df_acoes["Status"] == "Não iniciado"]
            for _, row in nao_iniciados.iterrows():
                st.caption(f"• {row['Ação'][:50]}...")
        
        with col_kanban2:
            st.markdown("**🟡 Em andamento**")
            em_andamento = df_acoes[df_acoes["Status"] == "Em andamento"]
            for _, row in em_andamento.iterrows():
                st.caption(f"• {row['Ação'][:50]}...")
        
        with col_kanban3:
            st.markdown("**🟢 Concluído**")
            concluidos = df_acoes[df_acoes["Status"] == "Concluído"]
            for _, row in concluidos.iterrows():
                st.caption(f"• {row['Ação'][:50]}...")
        
        with col_kanban4:
            st.markdown("**🔶 Atrasado**")
            atrasados = df_acoes[df_acoes["Status"] == "Atrasado"]
            for _, row in atrasados.iterrows():
                st.caption(f"• {row['Ação'][:50]}...")
    else:
        st.info("Nenhuma ação cadastrada.")

# ---------- Alertas ----------
with st.expander("⚠️ Alertas", expanded=True):
    st.markdown("### Alertas Automáticos")
    
    if alertas_gerados:
        df_alertas = pd.DataFrame(alertas_gerados)
        st.dataframe(
            df_alertas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prioridade": st.column_config.Column(
                    "Prioridade",
                    help="Alta, Média ou Baixa"
                )
            }
        )
        
        alertas_count = df_alertas["Tipo"].value_counts()
        st.bar_chart(alertas_count)
    else:
        st.success("✅ Nenhum alerta ativo no momento.")

# ---------- Botão IA - Relatório Executivo ----------
st.divider()
st.subheader("🤖 Gerar Relatório Executivo")

if st.button("🤖 Gerar Relatório Executivo", width="stretch"):
    with st.spinner("Gerando relatório executivo com IA..."):
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            total_acoes = len(acoes_consolidados)
            concluidas = len([a for a in acoes_consolidados if a.get("Status") == "Concluído"])
            total_kpis = len(kpis_consolidados)
            
            prompt = f"""
            Você é um consultor sênior de estratégia analisando o desempenho de uma empresa.
            
            EMPRESA: {empresa_nome}
            SETOR: {empresa_setor}
            
            DADOS DE DESEMPENHO:
            - Total de Ações: {total_acoes}
            - Ações Concluídas: {concluidas} ({concluidas/total_acoes*100:.1f}% se total_acoes > 0 else 0)
            - Total de KPIs: {total_kpis}
            - Alertas Ativos: {len(alertas_gerados)}
            
            Com base nesses dados, gere um relatório executivo resumido contendo:
            1. Resumo do desempenho geral
            2. Principais riscos identificados
            3. Ações prioritárias recomendadas
            4. Recomendações estratégicas
            
            Seja objetivo, prático e direto ao ponto. Responda em português do Brasil.
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor sênior de estratégia. Responda em português do Brasil, de forma profissional e objetiva."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            relatorio = response.choices[0].message.content
            
            st.markdown("### 📋 Relatório Executivo")
            st.markdown(relatorio)
            
            st.session_state["relatorio_executivo"] = relatorio
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar relatório: {str(e)}")

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
    MONITORAMENTO ESTRATÉGICO:
    - Total de Ações: {len(acoes_consolidados)}
    - Ações Concluídas: {len([a for a in acoes_consolidados if a.get('Status') == 'Concluído'])}
    - Total de KPIs: {len(kpis_consolidados)}
    - Alertas Ativos: {len(alertas_gerados)}
    - Departamentos: {len(data.get('departamentos', {}))}
    """

    system_prompt = """
    Você é um assistente especialista em Monitoramento Estratégico.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Acompanhar o desempenho dos KPIs
    - Analisar o status das ações
    - Identificar alertas e riscos
    - Tomar decisões baseadas em dados
    - Conectar o monitoramento à estratégia geral
    """

    render_chat(
        messages_key="messages_monitoramento",
        placeholder="Pergunte ao assistente sobre o monitoramento...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Revisão", width="stretch"):
        st.switch_page("pages/10_🔄_Revisão.py")
