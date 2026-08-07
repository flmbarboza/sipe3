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

st.set_page_config(page_title="Plano de Ação 5W2H", page_icon="✅", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
module_started(
    Module.PLANO_ACAO
)
sidebar_data_controls()

st.title("✅ Plano de Ação (5W2H)")
st.caption(
    "What (o quê), Why (por quê), Where (onde), When (quando), Who (quem), "
    "How (como) e How much (quanto custa)."
)

# ========== SEÇÃO DE INFORMAÇÕES ADICIONAIS ==========
with st.expander("📋 Informações para o Plano de Ação", expanded=True):
    st.markdown("**Preencha as informações abaixo para ajudar a IA a gerar um plano de ação mais preciso:**")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        pessoas = st.text_area(
            "👥 Pessoas envolvidas",
            value=data.get("acao_info", {}).get("pessoas", ""),
            placeholder="Ex: João (Gerente de Vendas), Maria (Marketing), Carlos (Operações)...",
            height=80,
            help="Liste as principais pessoas envolvidas na execução do plano"
        )
        
        recursos = st.text_area(
            "🔧 Recursos disponíveis",
            value=data.get("acao_info", {}).get("recursos", ""),
            placeholder="Ex: Orçamento de R$ 50.000, equipe de 5 pessoas, software X, veículos...",
            height=80,
            help="Recursos materiais, financeiros e humanos disponíveis"
        )
    
    with col_info2:
        restricoes = st.text_area(
            "⚠️ Restrições ou limitações",
            value=data.get("acao_info", {}).get("restricoes", ""),
            placeholder="Ex: Prazo máximo de 3 meses, orçamento limitado, falta de pessoal...",
            height=80,
            help="O que pode limitar a execução do plano"
        )
        
        observacoes = st.text_area(
            "📝 Observações adicionais",
            value=data.get("acao_info", {}).get("observacoes", ""),
            placeholder="Ex: Prioridade para ações de baixo custo, foco em resultados rápidos...",
            height=80,
            help="Qualquer informação adicional relevante"
        )
    
    if "acao_info" not in data:
        data["acao_info"] = {}
    data["acao_info"]["pessoas"] = pessoas
    data["acao_info"]["recursos"] = recursos
    data["acao_info"]["restricoes"] = restricoes
    data["acao_info"]["observacoes"] = observacoes

# ========== BOTÃO PARA GERAR PLANO COM IA ==========
st.divider()

objetivos = [o.get("objetivo", "") for o in data.get("objetivos", []) if o.get("objetivo")]

col_gerar1, col_gerar2, col_gerar3 = st.columns([3, 1, 1])
with col_gerar1:
    st.markdown("**🤖 Gerar Plano de Ação com IA**")
    st.caption("A IA vai analisar seus objetivos estratégicos e gerar um plano 5W2H personalizado")
with col_gerar2:
    gerar_plano = st.button("🚀 Gerar Plano", width="stretch")
with col_gerar3:
    limpar_plano = st.button("🗑️ Limpar Plano", width="stretch", help="Remove todas as ações do plano")
    
    if limpar_plano:
        data["acao_5w2h"] = []
        st.rerun()

if gerar_plano:
    if not objetivos:
        st.warning("⚠️ Nenhum objetivo estratégico encontrado. Por favor, defina os objetivos na página de Planejamento Estratégico primeiro.")
    else:
        with st.spinner("🧠 Gerando plano de ação com IA..."):
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
                
                empresa = data.get("empresa", {}).get("nome", "a empresa")
                setor = data.get("empresa", {}).get("setor", "não informado")
                
                acoes_existentes = data.get("acao_5w2h", [])
                resumo_existente = "\n".join([f"- {a.get('what', '')}" for a in acoes_existentes if a.get('what')])
                
                prompt = f"""
                Você é um consultor de gestão especializado em planos de ação 5W2H.
                
                INFORMAÇÕES DA EMPRESA:
                - Nome: {empresa}
                - Setor: {setor}
                
                OBJETIVOS ESTRATÉGICOS:
                {chr(10).join([f"- {obj}" for obj in objetivos])}
                
                AÇÕES JÁ EXISTENTES NO PLANO:
                {resumo_existente or "Nenhuma ação existente"}
                
                PESSOAS ENVOLVIDAS:
                {pessoas or "Não informado"}
                
                RECURSOS DISPONÍVEIS:
                {recursos or "Não informado"}
                
                RESTRIÇÕES:
                {restricoes or "Não informado"}
                
                OBSERVAÇÕES:
                {observacoes or "Não informado"}
                
                IMPORTANTE: 
                1. Gere APENAS ações que ainda NÃO existem no plano (evite duplicatas)
                2. Gere de 2 a 4 ações novas
                3. Cada ação deve ter todos os campos do 5W2H preenchidos
                4. Seja específico e prático
                
                FORMATO DE SAÍDA (OBRIGATÓRIO): Retorne APENAS um JSON com a lista de ações, onde cada ação é um objeto com os campos: what, why, where, when, who, how, how_much, status (sempre "Não iniciado").
                
                Exemplo de formato:
                {{
                    "acoes": [
                        {{
                            "what": "Implementar CRM",
                            "why": "Melhorar gestão de clientes",
                            "where": "Departamento comercial",
                            "when": "Até 30/06/2026",
                            "who": "João (Gerente)",
                            "how": "Contratar sistema e treinar equipe",
                            "how_much": "R$ 15.000",
                            "status": "Não iniciado"
                        }}
                    ]
                }}
                
                Responda APENAS com o JSON, sem texto adicional.
                """
                
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": "Você é um consultor de gestão especializado em planos de ação 5W2H. Responda em português do Brasil. Retorne APENAS JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                conteudo = response.choices[0].message.content
                
                try:
                    json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
                    if json_match:
                        dados = json.loads(json_match.group())
                        novas_acoes = dados.get("acoes", [])
                    else:
                        dados = json.loads(conteudo)
                        novas_acoes = dados.get("acoes", [])
                    
                    if novas_acoes:
                        existentes_what = {a.get("what", "").lower().strip() for a in acoes_existentes}
                        acoes_adicionadas = []
                        
                        for acao in novas_acoes:
                            what = acao.get("what", "").strip()
                            if what and what.lower() not in existentes_what:
                                for campo in ["why", "where", "when", "who", "how", "how_much"]:
                                    if campo not in acao:
                                        acao[campo] = ""
                                acao["status"] = "Não iniciado"
                                acoes_adicionadas.append(acao)
                                existentes_what.add(what.lower())
                        
                        if acoes_adicionadas:
                            data["acao_5w2h"] = acoes_existentes + acoes_adicionadas
                            st.success(f"✅ {len(acoes_adicionadas)} novas ações geradas e adicionadas ao plano!")
                            st.rerun()
                        else:
                            st.info("ℹ️ Todas as ações sugeridas já existem no plano.")
                    else:
                        st.warning("⚠️ A IA não gerou novas ações. Tente novamente com mais informações.")
                        
                except json.JSONDecodeError as e:
                    st.error(f"❌ Erro ao parsear resposta da IA: {str(e)}")
                    st.code(conteudo)
                    
            except Exception as e:
                st.error(f"❌ Erro ao gerar plano: {str(e)}")

# ========== EXIBIÇÃO DO PLANO DE AÇÃO ==========
st.divider()
st.subheader("📋 Plano de Ação")

itens = data.get("acao_5w2h", [])
colunas = ["what", "why", "where", "when", "who", "how", "how_much", "status"]
nomes_colunas = {
    "what": "O quê (What)",
    "why": "Por quê (Why)",
    "where": "Onde (Where)",
    "when": "Quando (When)",
    "who": "Quem (Who)",
    "how": "Como (How)",
    "how_much": "Quanto custa (How much)",
    "status": "Status",
}

for item in itens:
    for col in colunas:
        if col not in item:
            item[col] = ""

if itens:
    df = pd.DataFrame(itens)
    for col in colunas:
        if col not in df.columns:
            df[col] = ""
        if col != "status":
            df[col] = df[col].astype(str)
else:
    df = pd.DataFrame({col: pd.Series(dtype="object") for col in colunas})

df_hash = hash(str(sorted([str(item) for item in itens]))) if itens else 0
editor_key = f"editor_5w2h_{df_hash}"

edited = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key=editor_key,
    column_config={
        "what": st.column_config.TextColumn(nomes_colunas["what"], width="large"),
        "why": st.column_config.TextColumn(nomes_colunas["why"], width="large"),
        "where": st.column_config.TextColumn(nomes_colunas["where"]),
        "when": st.column_config.TextColumn(nomes_colunas["when"]),
        "who": st.column_config.TextColumn(nomes_colunas["who"]),
        "how": st.column_config.TextColumn(nomes_colunas["how"], width="large"),
        "how_much": st.column_config.TextColumn(nomes_colunas["how_much"]),
        "status": st.column_config.SelectboxColumn(
            nomes_colunas["status"], options=["Não iniciado", "Em andamento", "Concluído", "Atrasado"]
        ),
    },
)

if edited is not None:
    edited = edited.fillna("")
    novos_itens = []
    for _, row in edited.iterrows():
        what = str(row.get("what", "")).strip()
        if what:
            novo_item = {}
            for col in colunas:
                valor = row.get(col, "")
                if col == "status" and not valor:
                    valor = "Não iniciado"
                novo_item[col] = str(valor).strip() if col != "status" else valor
            novos_itens.append(novo_item)
    
    if novos_itens != data.get("acao_5w2h", []):
        data["acao_5w2h"] = novos_itens
        st.rerun()

col_download1, col_download2 = st.columns([1, 5])
with col_download1:
    if data.get("acao_5w2h"):
        df_download = pd.DataFrame(data["acao_5w2h"])
        st.download_button(
            "⬇️ Baixar CSV",
            data=df_download.rename(columns=nomes_colunas).to_csv(index=False).encode("utf-8-sig"),
            file_name="plano_de_acao_5w2h.csv",
            mime="text/csv",
            width="stretch"
        )

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
    plano_atual = ""
    for i, acao in enumerate(data.get("acao_5w2h", []), 1):
        plano_atual += f"\nAção {i}:\n"
        plano_atual += f"  What: {acao.get('what', '')}\n"
        plano_atual += f"  Why: {acao.get('why', '')}\n"
        plano_atual += f"  Where: {acao.get('where', '')}\n"
        plano_atual += f"  When: {acao.get('when', '')}\n"
        plano_atual += f"  Who: {acao.get('who', '')}\n"
        plano_atual += f"  How: {acao.get('how', '')}\n"
        plano_atual += f"  How much: {acao.get('how_much', '')}\n"
        plano_atual += f"  Status: {acao.get('status', 'Não iniciado')}\n"

    objetivos_texto = ""
    if objetivos:
        for obj in objetivos[:5]:
            objetivos_texto += f"  • {obj}\n"

    contexto = f"""
    SIPE - SISTEMA INTEGRADO DE PLANEJAMENTO ESTRATÉGICO

    EMPRESA:
    {empresa_nome}

    SETOR:
    {empresa.get('setor', 'Não informado')}

    LOCALIZAÇÃO:
    {empresa.get('cidade_estado', 'Não informado')}

    OBJETIVOS ESTRATÉGICOS:
    {objetivos_texto or 'Nenhum objetivo definido'}

    PLANO DE AÇÃO 5W2H ATUAL:
    {plano_atual or 'Nenhuma ação definida'}

    PESSOAS ENVOLVIDAS:
    {pessoas or 'Não informado'}

    RECURSOS DISPONÍVEIS:
    {recursos or 'Não informado'}

    RESTRIÇÕES:
    {restricoes or 'Não informado'}
    """

    system_prompt = """
    Você é um assistente especializado em planos de ação 5W2H e gestão estratégica.

    Responda em português do Brasil, de forma prática e orientada a execução.

    Ajude o usuário a:
    - Estruturar ações nos 7 campos do 5W2H
    - Definir prazos e responsáveis
    - Estimar custos e recursos
    - Acompanhar o status das ações
    - Conectar as ações aos objetivos estratégicos

    Se o usuário pedir para ADICIONAR ações ao plano, gere as ações no formato 5W2H.
    """

    render_chat(
        messages_key="messages_acao",
        placeholder="Pergunte ao assistente sobre seu plano de ação...",
        system_prompt=system_prompt,
        context=contexto,
    )
    
# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Planos por Função", width="stretch"):
        st.switch_page("pages/7_📋_Planos_por_Função.py")
