import pandas as pd
import streamlit as st
import json
import re
from utils.data_manager import init_data, get_data, sidebar_data_controls
from utils.chat import render_chat
from openai import OpenAI
from utils.analytics import UXMonitor
from analytics import Module
from analytics import module_started
from analytics import module_completed
from analytics import track
from analytics import EventType

monitor = UXMonitor()
page_name = "Planos Departamentais"
monitor.track_event('page_view', page_name)

st.set_page_config(page_title="Planos Departamentais", page_icon="🏢", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
module_started(
    Module.PLANO_FUNCAO
)
sidebar_data_controls()

st.title("🏢 Planos Departamentais")
st.caption(
    "Gerencie os planos de ação, objetivos, indicadores e recursos de cada departamento. "
    "A IA pode sugerir planos completos baseados nas análises estratégicas."
)

# ========== DEFINIÇÃO DOS DEPARTAMENTOS ==========
DEPARTAMENTOS = [
    "Financeiro",
    "Comercial",
    "Marketing",
    "Operações",
    "Recursos Humanos",
    "Tecnologia",
    "Inovação",
    "Sustentabilidade",
    "Jurídico"
]

# ========== INICIALIZAR DADOS ==========
if "departamentos" not in data:
    data["departamentos"] = {}
    for depto in DEPARTAMENTOS:
        data["departamentos"][depto] = {
            "objetivos": [],
            "acoes": [],
            "indicadores": [],
            "recursos": [],
            "riscos": []
        }

# ========== FUNÇÃO DE RENDERIZAÇÃO ==========
def render_tabela(departamento, secao, colunas, titulo):
    """Renderiza uma tabela editável e salva diretamente em data"""
    st.markdown(f"**{titulo}**")
    
    dados = data["departamentos"][departamento][secao]
    
    if dados:
        df = pd.DataFrame(dados)
        for col in colunas:
            if col not in df.columns:
                df[col] = ""
        df = df[colunas]
    else:
        df = pd.DataFrame(columns=colunas)
    
    column_config = {}
    for col in colunas:
        if col == "Prioridade":
            column_config[col] = st.column_config.SelectboxColumn(
                col,
                options=["Alta", "Média", "Baixa"],
                width="large"
            )
        elif col == "Status" or col == "Situação":
            column_config[col] = st.column_config.SelectboxColumn(
                col,
                options=["Não iniciado", "Em andamento", "Concluído", "Atrasado"],
                width="large"
            )
        elif col == "Probabilidade":
            column_config[col] = st.column_config.SelectboxColumn(
                col,
                options=["Baixa", "Média", "Alta"],
                width="large"
            )
        elif col == "Impacto":
            column_config[col] = st.column_config.SelectboxColumn(
                col,
                options=["Baixo", "Médio", "Alto"],
                width="large"
            )
        elif col == "Tipo":
            column_config[col] = st.column_config.SelectboxColumn(
                col,
                options=["Financeiro", "Humano", "Material", "Tecnológico", "Outro"],
                width="large"
            )
        else:
            column_config[col] = st.column_config.TextColumn(col, width="large")
    
    editor_key = f"editor_{departamento}_{secao}"
    
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=editor_key,
        column_config=column_config
    )
    
    if edited is not None:
        edited_fill = edited.fillna("")
        novos_dados = []
        for _, row in edited_fill.iterrows():
            item = {}
            valido = False
            for col in colunas:
                valor = str(row.get(col, "")).strip()
                item[col] = valor
                if valor:
                    valido = True
            if valido:
                novos_dados.append(item)
        
        dados_atuais = []
        for item in dados:
            if isinstance(item, dict):
                dados_atuais.append(item)
        
        if novos_dados != dados_atuais:
            data["departamentos"][departamento][secao] = novos_dados

# ========== FUNÇÕES DE IA ==========
def gerar_plano_departamento_ia(departamento):
    """Gera plano completo para um departamento usando IA"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
        
        empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
        empresa_setor = data.get("empresa", {}).get("setor", "não informado")
        
        swot_dados = ""
        if "swot" in data:
            for chave, itens in data["swot"].items():
                if itens:
                    nomes = {"forcas": "Forças", "fraquezas": "Fraquezas", 
                            "oportunidades": "Oportunidades", "ameacas": "Ameaças"}
                    swot_dados += f"\n{nomes.get(chave, chave)}:\n"
                    for item in itens[:3]:
                        swot_dados += f"  - {item.get('descricao', '')}\n"
        
        pestel_dados = ""
        if "pestel" in data:
            for cat, itens in data["pestel"].items():
                if itens:
                    pestel_dados += f"\n{cat}:\n"
                    for item in itens[:2]:
                        pestel_dados += f"  - {item.get('descricao', '')}\n"
        
        porter_dados = ""
        if "porter_analise" in data:
            for forca in data["porter_analise"].values():
                if forca.get("intensidade", 0) >= 4:
                    porter_dados += f"  - {forca.get('nome', '')}: Intensidade {forca.get('intensidade', 0)}/5\n"
        
        prompt = f"""
        Você é um consultor de planejamento estratégico especializado em planos departamentais.
        
        EMPRESA: {empresa_nome}
        SETOR: {empresa_setor}
        DEPARTAMENTO: {departamento}
        
        INFORMAÇÕES ESTRATÉGICAS DA EMPRESA:
        {swot_dados}
        {pestel_dados}
        {porter_dados}
        
        Com base nas informações acima, crie um plano completo para o departamento de {departamento}.
        
        FORMATO DE SAÍDA: Retorne APENAS um JSON com as seguintes chaves EXATAS:
        {{
            "objetivos": [
                {{"Objetivo": "texto", "Estratégia relacionada": "texto", "Prioridade": "Alta", 
                  "Responsável": "texto", "Prazo": "texto", "Status": "Não iniciado"}}
            ],
            "acoes": [
                {{"Ação": "texto", "Origem": "texto", "Responsável": "texto", 
                  "Data início": "texto", "Data fim": "texto", "Recursos necessários": "texto", 
                  "Custo estimado": "texto", "Indicador": "texto", "Meta": "texto", "Situação": "Não iniciado"}}
            ],
            "indicadores": [
                {{"Indicador": "texto", "Fórmula": "texto", "Meta": "texto", 
                  "Valor Atual": "texto", "Frequência": "texto", "Responsável": "texto"}}
            ],
            "recursos": [
                {{"Recurso": "texto", "Tipo": "texto", "Quantidade": "texto", 
                  "Valor estimado": "texto", "Observações": "texto"}}
            ],
            "riscos": [
                {{"Risco": "texto", "Probabilidade": "texto", "Impacto": "texto", 
                  "Plano de mitigação": "texto"}}
            ]
        }}
        
        Cada seção deve ter de 3 a 5 itens.
        Responda APENAS com o JSON.
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

# ========== TABS POR DEPARTAMENTO ==========
tabs = st.tabs(DEPARTAMENTOS)

for tab, depto in zip(tabs, DEPARTAMENTOS):
    with tab:
        st.subheader(f"📋 Plano - {depto}")
        
        col_ia1, col_ia2 = st.columns([3, 1])
        with col_ia1:
            st.caption(f"🤖 A IA vai gerar um plano completo para o departamento de {depto} baseado nas análises estratégicas")
        with col_ia2:
            if st.button(f"🤖 Sugerir Plano", key=f"ia_{depto}", width="stretch"):
                with st.spinner(f"Gerando plano para {depto}..."):
                    resultado = gerar_plano_departamento_ia(depto)
                    if resultado:
                        if "objetivos" in resultado:
                            data["departamentos"][depto]["objetivos"] = resultado["objetivos"]
                        if "acoes" in resultado:
                            data["departamentos"][depto]["acoes"] = resultado["acoes"]
                        if "indicadores" in resultado:
                            data["departamentos"][depto]["indicadores"] = resultado["indicadores"]
                        if "recursos" in resultado:
                            data["departamentos"][depto]["recursos"] = resultado["recursos"]
                        if "riscos" in resultado:
                            data["departamentos"][depto]["riscos"] = resultado["riscos"]
                        st.success(f"✅ Plano gerado para {depto}!")
                        st.rerun()
        
        st.divider()
        
        with st.expander("🎯 Objetivos", expanded=True):
            render_tabela(
                depto,
                "objetivos",
                ["Objetivo", "Estratégia relacionada", "Prioridade", "Responsável", "Prazo", "Status"],
                "Objetivos do departamento"
            )
        
        with st.expander("📋 Plano de Ações", expanded=True):
            render_tabela(
                depto,
                "acoes",
                ["Ação", "Origem", "Responsável", "Data início", "Data fim", 
                 "Recursos necessários", "Custo estimado", "Indicador", "Meta", "Situação"],
                "Plano de ações do departamento"
            )
        
        with st.expander("📊 Indicadores"):
            render_tabela(
                depto,
                "indicadores",
                ["Indicador", "Fórmula", "Meta", "Valor Atual", "Frequência", "Responsável"],
                "Indicadores do departamento"
            )
        
        with st.expander("💰 Recursos Necessários"):
            render_tabela(
                depto,
                "recursos",
                ["Recurso", "Tipo", "Quantidade", "Valor estimado", "Observações"],
                "Recursos necessários"
            )
        
        with st.expander("⚠️ Riscos"):
            render_tabela(
                depto,
                "riscos",
                ["Risco", "Probabilidade", "Impacto", "Plano de mitigação"],
                "Riscos do departamento"
            )

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
    contexto = "PLANOS DEPARTAMENTAIS:\n\n"
    for depto in DEPARTAMENTOS:
        dados = data["departamentos"][depto]
        contexto += f"{depto}:\n"
        if dados["objetivos"]:
            contexto += f"  Objetivos: {len(dados['objetivos'])}\n"
            for obj in dados["objetivos"][:2]:
                contexto += f"    • {obj.get('Objetivo', '')}\n"
        if dados["acoes"]:
            contexto += f"  Ações: {len(dados['acoes'])}\n"
        if dados["indicadores"]:
            contexto += f"  Indicadores: {len(dados['indicadores'])}\n"
        if dados["recursos"]:
            contexto += f"  Recursos: {len(dados['recursos'])}\n"
        if dados["riscos"]:
            contexto += f"  Riscos: {len(dados['riscos'])}\n"

    system_prompt = """
    Você é um assistente especialista em Planejamento Estratégico Departamental.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Estruturar planos para cada departamento
    - Definir objetivos e ações departamentais
    - Estabelecer indicadores de desempenho
    - Identificar recursos necessários e riscos
    - Conectar os planos departamentais à estratégia geral
    """

    render_chat(
        messages_key="messages_departamentos",
        placeholder="Pergunte ao assistente sobre os planos departamentais...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Orçamento", width="stretch"):
        st.switch_page("pages/8_💰_Orçamento.py")
