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

st.set_page_config(page_title="5 Forças de Porter", page_icon="⚔️", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
sidebar_data_controls()

st.title("⚔️ 5 Forças de Porter")
module_started(
    Module.PORTER
)
st.caption(
    "Avalie a intensidade de cada força competitiva do setor (1 = muito baixa, 5 = muito alta) "
    "e registre suas observações. Isso ajuda a construir a Análise SWOT."
)

FORCAS = [
    {"id": "rivalidade", "nome": "Rivalidade entre concorrentes", 
     "ajuda": "Número e força dos concorrentes diretos, guerra de preços, diferenciação."},
    {"id": "clientes", "nome": "Poder de barganha dos clientes", 
     "ajuda": "Concentração de clientes, sensibilidade a preço, custo de troca."},
    {"id": "fornecedores", "nome": "Poder de barganha dos fornecedores", 
     "ajuda": "Concentração de fornecedores, insumos críticos, custo de troca."},
    {"id": "entrantes", "nome": "Ameaça de novos entrantes", 
     "ajuda": "Barreiras de entrada, capital necessário, regulação, economia de escala."},
    {"id": "substitutos", "nome": "Ameaça de produtos substitutos", 
     "ajuda": "Alternativas que atendem à mesma necessidade do cliente."},
]

if "porter_analise" not in data:
    data["porter_analise"] = {}
    for forca in FORCAS:
        data["porter_analise"][forca["id"]] = {
            "intensidade": 3,
            "notas": "",
            "nome": forca["nome"]
        }

empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
empresa_setor = data.get("empresa", {}).get("setor", "não informado")
empresa_cidade = data.get("empresa", {}).get("cidade_estado", "")

def gerar_analise_ia(forca_id=None):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
        
        # ========== COLETAR DADOS DAS OUTRAS PÁGINAS ==========
        # Dados da empresa
        empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
        empresa_setor = data.get("empresa", {}).get("setor", "não informado")
        empresa_cidade = data.get("empresa", {}).get("cidade_estado", "")
        
        # Dados do BMC
        bmc_dados = ""
        if "bmc" in data and isinstance(data["bmc"], dict):
            bmc_itens = []
            for chave, valor in data["bmc"].items():
                if valor:
                    if isinstance(valor, list):
                        bmc_itens.append(f"- {chave}: {', '.join(valor)}")
                    elif isinstance(valor, str) and valor.strip():
                        bmc_itens.append(f"- {chave}: {valor}")
            if bmc_itens:
                bmc_dados = "\n".join(bmc_itens)
        
        # Dados do PESTEL
        pestel_dados = ""
        if "pestel" in data and isinstance(data["pestel"], dict):
            pestel_itens = []
            for cat, itens in data["pestel"].items():
                if itens and isinstance(itens, list):
                    for item in itens:
                        if isinstance(item, dict) and item.get("descricao"):
                            pestel_itens.append(f"- {cat}: {item['descricao']} ({item.get('tipo', '')})")
            if pestel_itens:
                pestel_dados = "\n".join(pestel_itens[:10])
        
        # Dados da SWOT
        swot_dados = ""
        if "swot" in data and isinstance(data["swot"], dict):
            swot_itens = []
            for chave, itens in data["swot"].items():
                if itens and isinstance(itens, list):
                    for item in itens:
                        if isinstance(item, dict) and item.get("descricao"):
                            swot_itens.append(f"- {chave}: {item['descricao']}")
            if swot_itens:
                swot_dados = "\n".join(swot_itens[:10])
        
        # Montar contexto
        contexto = f"""
        INFORMAÇÕES DA EMPRESA:
        - Nome: {empresa_nome}
        - Setor: {empresa_setor}
        - Localização: {empresa_cidade or "Não informado"}
        
        BUSINESS MODEL CANVAS:
        {bmc_dados or "Não informado"}
        
        ANÁLISE PESTEL:
        {pestel_dados or "Não informado"}
        
        ANÁLISE SWOT:
        {swot_dados or "Não informado"}
        """
        
        if forca_id:
            forca = next(f for f in FORCAS if f["id"] == forca_id)
            prompt = f"""
            Você é um consultor especialista em 5 Forças de Porter.
            
            {contexto}
            
            Força de Porter: {forca['nome']}
            Descrição: {forca['ajuda']}
            
            Com base nas informações da empresa, setor e demais análises, gere uma análise objetiva em português do Brasil para esta força.
            Responda APENAS com um JSON: {{"intensidade": 3, "notas": "análise detalhada"}}
            """
        else:
            prompt = f"""
            Você é um consultor especialista em 5 Forças de Porter.
            
            {contexto}
            
            Com base nas informações da empresa, setor e demais análises, analise as 5 Forças de Porter em português do Brasil.
            
            FORMATO DE SAÍDA: Retorne APENAS um JSON com:
            {{
                "rivalidade": {{"intensidade": 3, "notas": "análise"}},
                "clientes": {{"intensidade": 3, "notas": "análise"}},
                "fornecedores": {{"intensidade": 3, "notas": "análise"}},
                "entrantes": {{"intensidade": 3, "notas": "análise"}},
                "substitutos": {{"intensidade": 3, "notas": "análise"}}
            }}
            """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "Você é um consultor especialista em Porter. Responda em português do Brasil. Retorne APENAS JSON válido."},
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

def render_forca(forca):
    """Renderiza uma força usando data_editor em tabela"""
    
    chave = forca["id"]
    dados = data["porter_analise"][chave]
    
    # Criar DataFrame com uma única linha
    df = pd.DataFrame([{
        "intensidade": dados["intensidade"],
        "notas": dados.get("notas", "")
    }])
    
    df_hash = hash(str(dados)) 
    editor_key = f"porter_editor_{chave}_{df_hash}"
    
    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key=editor_key,
        column_config={
            "intensidade": st.column_config.SelectboxColumn(
                "Intensidade",
                options=[1, 2, 3, 4, 5],
                help="1=Muito Baixa, 5=Muito Alta"
            ),
            "notas": st.column_config.TextColumn(
                "Observações",
                width="large"
            )
        },
        height=80
    )
    
    # Atualizar dados se editados
    if edited is not None and not edited.empty:
        nova_intensidade = edited.iloc[0].get("intensidade", 3)
        novas_notas = edited.iloc[0].get("notas", "")
        
        if nova_intensidade != dados["intensidade"]:
            dados["intensidade"] = int(nova_intensidade)
        if novas_notas != dados.get("notas", ""):
            dados["notas"] = novas_notas

st.subheader("🚀 Ações com IA")

col_gerar1, col_gerar2, col_gerar3 = st.columns([3, 1, 1])
with col_gerar1:
    st.caption("A IA vai analisar seu setor e gerar análise para todas as 5 forças")
with col_gerar2:
    if st.button("🔄 Gerar Análise Completa", width="stretch"):
        with st.spinner("Gerando análise completa..."):
            resultado = gerar_analise_ia()
            if resultado:
                for forca in FORCAS:
                    if forca["id"] in resultado:
                        data["porter_analise"][forca["id"]]["intensidade"] = resultado[forca["id"]]["intensidade"]
                        data["porter_analise"][forca["id"]]["notas"] = resultado[forca["id"]]["notas"]
                st.success("✅ Análise completa gerada!")
                st.rerun()
with col_gerar3:
    if st.button("🗑️ Limpar Análise", width="stretch"):
        for forca in FORCAS:
            data["porter_analise"][forca["id"]]["intensidade"] = 3
            data["porter_analise"][forca["id"]]["notas"] = ""
        st.rerun()

st.divider()

for forca in FORCAS:
    st.markdown(f"### {forca['nome']}")
    st.caption(forca['ajuda'])
    
    # Botões IA e Limpar
    col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1])
    with col_btn1:
        if st.button(f"🤖 Sugerir", key=f"sugerir_porter_{forca['id']}", width="stretch"):
            with st.spinner(f"Gerando análise para {forca['nome']}..."):
                resultado = gerar_analise_ia(forca["id"])
                if resultado:
                    data["porter_analise"][forca["id"]]["intensidade"] = resultado.get("intensidade", 3)
                    data["porter_analise"][forca["id"]]["notas"] = resultado.get("notas", "")
                    st.success(f"✅ Análise atualizada para {forca['nome']}!")
                    st.rerun()
    with col_btn2:
        if st.button(f"🗑️ Limpar", key=f"limpar_porter_{forca['id']}", width="stretch"):
            data["porter_analise"][forca["id"]]["intensidade"] = 3
            data["porter_analise"][forca["id"]]["notas"] = ""
            st.rerun()
    
    render_forca(forca)
    
    st.markdown("---")

st.subheader("📊 Resumo visual")

df_resumo = pd.DataFrame([
    {"Força": forca["nome"], "Intensidade": data["porter_analise"][forca["id"]]["intensidade"]}
    for forca in FORCAS
]).set_index("Força")
st.bar_chart(df_resumo)

media = df_resumo["Intensidade"].mean() if not df_resumo.empty else 0
st.metric("Intensidade competitiva média do setor", f"{media:.1f} / 5")

st.divider()
col_export1, col_export2 = st.columns(2)
with col_export1:
    if st.button("📋 Ver Análise Completa", width="stretch"):
        texto = "ANÁLISE DAS 5 FORÇAS DE PORTER\n" + "="*50 + "\n\n"
        for forca in FORCAS:
            dados = data["porter_analise"][forca["id"]]
            texto += f"{forca['nome']}:\n"
            texto += f"  Intensidade: {dados['intensidade']}/5\n"
            texto += f"  Observações: {dados['notas'] or '(vazio)'}\n\n"
        st.code(texto, language="markdown")

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
    porter_atual = ""
    for forca in FORCAS:
        dados = data["porter_analise"][forca["id"]]
        porter_atual += f"\n{forca['nome']}:\n"
        porter_atual += f"  Intensidade: {dados['intensidade']}/5\n"
        porter_atual += f"  Observações: {dados['notas'] or '(vazio)'}\n"

    contexto = f"""
    SIPE - SISTEMA INTEGRADO DE PLANEJAMENTO ESTRATÉGICO

    EMPRESA:
    {empresa_nome}

    SETOR:
    {empresa.get('setor', 'Não informado')}

    LOCALIZAÇÃO:
    {empresa.get('cidade_estado', 'Não informado')}

    ANÁLISE DAS 5 FORÇAS DE PORTER:
    {porter_atual}
    """

    system_prompt = """
    Você é um assistente especialista em Estratégia e 5 Forças de Porter.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Entender cada uma das 5 forças competitivas
    - Avaliar a intensidade de cada força (1 a 5)
    - Identificar oportunidades e ameaças do setor
    - Relacionar as forças com o negócio
    """

    render_chat(
        messages_key="messages_porter",
        placeholder="Pergunte ao assistente sobre as 5 Forças de Porter...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Análise SWOT", width="stretch"):
        st.switch_page("pages/4_🎯_Análise_SWOT.py")

