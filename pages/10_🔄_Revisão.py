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

st.set_page_config(page_title="Revisão Estratégica", page_icon="🔄", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
sidebar_data_controls()

st.title("🔄 Revisão Estratégica")
module_started(
    Module.REVIEW
)
st.caption(
    "Revise periodicamente o planejamento estratégico. Registre resultados, lições aprendidas, "
    "mudanças no ambiente e atualize a SWOT e o Plano de Ação com base nas recomendações da IA."
)

# ========== INICIALIZAR DADOS ==========
if "revisao" not in data:
    data["revisao"] = {
        "resultados": [],
        "objetivos_atingidos": [],
        "objetivos_nao_atingidos": [],
        "licoes_aprendidas": "",
        "mudancas": {
            "economicas": "",
            "politicas": "",
            "tecnologicas": "",
            "sociais": "",
            "ambientais": "",
            "legais": ""
        },
        "data_revisao": datetime.now().strftime("%d/%m/%Y"),
        "historico": []
    }

# ========== FUNÇÕES DE RENDERIZAÇÃO ==========
def render_tabela_editavel(dados, colunas, titulo, chave, altura=200):
    """Renderiza uma tabela editável genérica"""
    if dados:
        df = pd.DataFrame(dados)
        for col in colunas:
            if col not in df.columns:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=colunas)
    
    df_hash = hash(str(df.to_dict())) if not df.empty else 0
    editor_key = f"revisao_{chave}_{df_hash}"
    
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=editor_key,
        column_config={col: st.column_config.TextColumn(col, width="large") for col in colunas}
    )
    
    if edited is not None:
        edited = edited.fillna("")
        novos_dados = []
        for _, row in edited.iterrows():
            item = {}
            valido = False
            for col in colunas:
                valor = str(row.get(col, "")).strip()
                item[col] = valor
                if valor and not valido:
                    valido = True
            if valido:
                novos_dados.append(item)
        return novos_dados
    return dados

# ========== FUNÇÃO DE REVISÃO COM IA ==========
def gerar_revisao_ia():
    """Gera recomendações de revisão estratégica com IA"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
        
        empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
        empresa_setor = data.get("empresa", {}).get("setor", "não informado")
        
        swot_atual = ""
        if "swot" in data:
            for chave, itens in data["swot"].items():
                nomes = {"forcas": "Forças", "fraquezas": "Fraquezas", 
                        "oportunidades": "Oportunidades", "ameacas": "Ameaças"}
                swot_atual += f"\n{nomes.get(chave, chave)}:\n"
                for item in itens[:5]:
                    swot_atual += f"  - {item.get('descricao', '')}\n"
        
        acoes_atual = ""
        if "acao_5w2h" in data:
            for acao in data["acao_5w2h"][:5]:
                if acao.get("what"):
                    acoes_atual += f"  - {acao.get('what', '')} ({acao.get('status', '')})\n"
        
        objetivos_atual = ""
        if "objetivos" in data:
            for obj in data["objetivos"][:5]:
                if obj.get("objetivo"):
                    objetivos_atual += f"  - {obj.get('objetivo', '')} - {obj.get('status', '')}\n"
        
        prompt = f"""
        Você é um consultor sênior de estratégia especializado em revisão estratégica.
        
        EMPRESA: {empresa_nome}
        SETOR: {empresa_setor}
        
        PLANEJAMENTO ATUAL:
        
        SWOT:
        {swot_atual or "Nenhum dado disponível"}
        
        OBJETIVOS:
        {objetivos_atual or "Nenhum objetivo definido"}
        
        AÇÕES:
        {acoes_atual or "Nenhuma ação definida"}
        
        Com base nas informações acima, faça uma revisão estratégica completa, respondendo APENAS com um JSON:
        {{
            "estrategias_remover": ["estratégia1", "estratégia2"],
            "estrategias_incluir": ["estratégia1", "estratégia2"],
            "acoes_prioritarias": ["ação1", "ação2"],
            "novos_riscos": ["risco1", "risco2"],
            "novas_oportunidades": ["oportunidade1", "oportunidade2"],
            "recomendacoes_gerais": "texto com recomendações gerais"
        }}
        
        Responda em português do Brasil. Seja objetivo e prático.
        """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "Você é um consultor sênior de estratégia. Responda em português do Brasil. Retorne APENAS JSON válido."},
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

# ========== EXIBIÇÃO ==========

# ---------- RESULTADOS ALCANÇADOS ----------
with st.expander("📊 Resultados Alcançados", expanded=True):
    st.markdown("### Resultados Alcançados")
    st.caption("Registre os resultados obtidos no período")
    
    colunas_resultados = ["Resultado", "Data", "Responsável", "Evidências", "Observações"]
    novos = render_tabela_editavel(
        data["revisao"].get("resultados", []),
        colunas_resultados,
        "Resultados",
        "resultados"
    )
    if novos != data["revisao"].get("resultados", []):
        data["revisao"]["resultados"] = novos

# ---------- OBJETIVOS ATINGIDOS ----------
with st.expander("✅ Objetivos Atingidos", expanded=True):
    st.markdown("### Objetivos Atingidos")
    st.caption("Liste os objetivos estratégicos que foram alcançados")
    
    colunas_atingidos = ["Objetivo", "Data Conclusão", "Responsável", "Comentários"]
    novos = render_tabela_editavel(
        data["revisao"].get("objetivos_atingidos", []),
        colunas_atingidos,
        "Objetivos Atingidos",
        "objetivos_atingidos"
    )
    if novos != data["revisao"].get("objetivos_atingidos", []):
        data["revisao"]["objetivos_atingidos"] = novos

# ---------- OBJETIVOS NÃO ATINGIDOS ----------
with st.expander("❌ Objetivos Não Atingidos", expanded=True):
    st.markdown("### Objetivos Não Atingidos")
    st.caption("Liste os objetivos que não foram alcançados e os motivos")
    
    colunas_nao_atingidos = ["Objetivo", "Motivo", "Lições", "Ações Corretivas"]
    novos = render_tabela_editavel(
        data["revisao"].get("objetivos_nao_atingidos", []),
        colunas_nao_atingidos,
        "Objetivos Não Atingidos",
        "objetivos_nao_atingidos"
    )
    if novos != data["revisao"].get("objetivos_nao_atingidos", []):
        data["revisao"]["objetivos_nao_atingidos"] = novos

# ---------- LIÇÕES APRENDIDAS ----------
with st.expander("📝 Lições Aprendidas", expanded=True):
    st.markdown("### Lições Aprendidas")
    st.caption("Registre as principais lições aprendidas durante o período")
    
    licoes = st.text_area(
        "Lições Aprendidas",
        value=data["revisao"].get("licoes_aprendidas", ""),
        height=150,
        key="licoes_aprendidas"
    )
    if data["revisao"].get("licoes_aprendidas") != licoes:
        data["revisao"]["licoes_aprendidas"] = licoes

# ---------- MUDANÇAS NO AMBIENTE ----------
with st.expander("🌍 Mudanças no Ambiente", expanded=True):
    st.markdown("### Mudanças no Ambiente Externo")
    st.caption("Registre mudanças relevantes no ambiente que podem afetar o planejamento")
    
    mudancas = data["revisao"].get("mudancas", {})
    
    col_mud1, col_mud2 = st.columns(2)
    with col_mud1:
        mudancas["economicas"] = st.text_area(
            "💰 Mudanças Econômicas",
            value=mudancas.get("economicas", ""),
            height=80,
            key="mud_economicas"
        )
        mudancas["politicas"] = st.text_area(
            "🏛️ Mudanças Políticas",
            value=mudancas.get("politicas", ""),
            height=80,
            key="mud_politicas"
        )
        mudancas["tecnologicas"] = st.text_area(
            "💻 Mudanças Tecnológicas",
            value=mudancas.get("tecnologicas", ""),
            height=80,
            key="mud_tecnologicas"
        )
    
    with col_mud2:
        mudancas["sociais"] = st.text_area(
            "👥 Mudanças Sociais",
            value=mudancas.get("sociais", ""),
            height=80,
            key="mud_sociais"
        )
        mudancas["ambientais"] = st.text_area(
            "🌱 Mudanças Ambientais",
            value=mudancas.get("ambientais", ""),
            height=80,
            key="mud_ambientais"
        )
        mudancas["legais"] = st.text_area(
            "⚖️ Mudanças Legais",
            value=mudancas.get("legais", ""),
            height=80,
            key="mud_legais"
        )
    
    data["revisao"]["mudancas"] = mudancas

# ---------- ATUALIZAÇÃO DA SWOT ----------
with st.expander("🔄 Atualização da SWOT"):
    st.markdown("### Atualização da Análise SWOT")
    st.caption("Revise e atualize os quadrantes da SWOT com base nas mudanças identificadas")
    
    if "swot" in data:
        for chave, titulo in [("forcas", "💪 Forças"), ("fraquezas", "⚠️ Fraquezas"),
                             ("oportunidades", "🌱 Oportunidades"), ("ameacas", "🌩️ Ameaças")]:
            st.markdown(f"**{titulo}**")
            itens = data["swot"].get(chave, [])
            if itens:
                for i, item in enumerate(itens):
                    novo_valor = st.text_input(
                        f"Item {i+1}",
                        value=item.get("descricao", ""),
                        key=f"swot_update_{chave}_{i}"
                    )
                    if novo_valor != item.get("descricao", ""):
                        data["swot"][chave][i]["descricao"] = novo_valor
            else:
                st.caption("Nenhum item cadastrado.")

# ---------- ATUALIZAÇÃO DO PLANO DE AÇÃO ----------
with st.expander("📋 Atualização do Plano de Ação"):
    st.markdown("### Atualização do Plano de Ação")
    st.caption("Revise e atualize as ações do plano 5W2H")
    
    if "acao_5w2h" in data:
        for i, acao in enumerate(data["acao_5w2h"]):
            if acao.get("what"):
                st.markdown(f"**Ação {i+1}: {acao.get('what', '')}**")
                
                col_acao1, col_acao2 = st.columns(2)
                with col_acao1:
                    novo_status = st.selectbox(
                        "Status",
                        options=["Não iniciado", "Em andamento", "Concluído", "Atrasado"],
                        index=["Não iniciado", "Em andamento", "Concluído", "Atrasado"].index(acao.get("status", "Não iniciado")),
                        key=f"acao_status_{i}"
                    )
                    if novo_status != acao.get("status", ""):
                        data["acao_5w2h"][i]["status"] = novo_status
                
                with col_acao2:
                    novas_obs = st.text_input(
                        "Observações da revisão",
                        value="",
                        key=f"acao_obs_{i}",
                        placeholder="Adicione observações sobre esta ação..."
                    )
                    if novas_obs:
                        if "observacoes_revisao" not in data["acao_5w2h"][i]:
                            data["acao_5w2h"][i]["observacoes_revisao"] = []
                        data["acao_5w2h"][i]["observacoes_revisao"].append({
                            "data": datetime.now().strftime("%d/%m/%Y"),
                            "observacao": novas_obs
                        })
                        st.success("Observação adicionada!")

# ---------- RECOMENDAÇÕES DA IA ----------
st.divider()
st.subheader("🤖 Recomendações da IA - Revisão Estratégica")

col_ia1, col_ia2 = st.columns([3, 1])
with col_ia1:
    st.caption("A IA vai analisar todo o planejamento e sugerir ajustes estratégicos")
with col_ia2:
    if st.button("🤖 Revisar Estratégia", width="stretch"):
        with st.spinner("Analisando planejamento e gerando recomendações..."):
            resultado = gerar_revisao_ia()
            if resultado:
                st.session_state["revisao_ia_resultado"] = resultado
                st.rerun()

if "revisao_ia_resultado" in st.session_state:
    resultado = st.session_state["revisao_ia_resultado"]
    
    st.markdown("### 📋 Recomendações da IA")
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        if resultado.get("estrategias_remover"):
            st.markdown("**❌ Estratégias a Remover:**")
            for item in resultado["estrategias_remover"]:
                st.caption(f"• {item}")
        
        if resultado.get("novos_riscos"):
            st.markdown("**⚠️ Novos Riscos Identificados:**")
            for item in resultado["novos_riscos"]:
                st.caption(f"• {item}")
        
        if resultado.get("acoes_prioritarias"):
            st.markdown("**🎯 Ações Prioritárias:**")
            for item in resultado["acoes_prioritarias"]:
                st.caption(f"• {item}")
    
    with col_rec2:
        if resultado.get("estrategias_incluir"):
            st.markdown("**✅ Estratégias a Incluir:**")
            for item in resultado["estrategias_incluir"]:
                st.caption(f"• {item}")
        
        if resultado.get("novas_oportunidades"):
            st.markdown("**🌟 Novas Oportunidades:**")
            for item in resultado["novas_oportunidades"]:
                st.caption(f"• {item}")
    
    if resultado.get("recomendacoes_gerais"):
        st.markdown("**📝 Recomendações Gerais:**")
        st.info(resultado["recomendacoes_gerais"])
    
    if st.button("Aplicar Recomendações", width="stretch"):
        if resultado.get("novas_oportunidades") and "swot" in data:
            existentes = {item["descricao"].lower().strip() for item in data["swot"].get("oportunidades", [])}
            for item in resultado["novas_oportunidades"]:
                if item.lower().strip() not in existentes:
                    data["swot"]["oportunidades"].append({"descricao": item})
        
        if resultado.get("novos_riscos") and "swot" in data:
            existentes = {item["descricao"].lower().strip() for item in data["swot"].get("ameacas", [])}
            for item in resultado["novos_riscos"]:
                if item.lower().strip() not in existentes:
                    data["swot"]["ameacas"].append({"descricao": item})
        
        st.success("✅ Recomendações aplicadas com sucesso!")
        st.rerun()

# ---------- HISTÓRICO DE REVISÕES ----------
with st.expander("📜 Histórico de Revisões"):
    st.markdown("### Histórico de Revisões")
    
    if "historico" not in data["revisao"]:
        data["revisao"]["historico"] = []
    
    if st.button("📌 Salvar Revisão Atual", width="stretch"):
        data["revisao"]["historico"].append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "resultados": len(data["revisao"].get("resultados", [])),
            "objetivos_atingidos": len(data["revisao"].get("objetivos_atingidos", [])),
            "licoes": data["revisao"].get("licoes_aprendidas", "")[:100]
        })
        st.success("Revisão salva no histórico!")
        st.rerun()
    
    if data["revisao"]["historico"]:
        df_historico = pd.DataFrame(data["revisao"]["historico"])
        st.dataframe(df_historico, use_container_width=True, hide_index=True)

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
    REVISÃO ESTRATÉGICA:
    - Resultados: {len(data['revisao'].get('resultados', []))}
    - Objetivos Atingidos: {len(data['revisao'].get('objetivos_atingidos', []))}
    - Objetivos Não Atingidos: {len(data['revisao'].get('objetivos_nao_atingidos', []))}
    - Lições Aprendidas: {data['revisao'].get('licoes_aprendidas', 'Não informado')[:100]}
    - Mudanças Registradas: {len([k for k, v in data['revisao'].get('mudancas', {}).items() if v])}
    """

    system_prompt = """
    Você é um assistente especialista em Revisão Estratégica.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Registrar resultados e lições aprendidas
    - Identificar mudanças no ambiente
    - Atualizar a SWOT e o Plano de Ação
    - Aplicar recomendações estratégicas
    - Manter o histórico de revisões
    """

    render_chat(
        messages_key="messages_revisao",
        placeholder="Pergunte ao assistente sobre a revisão estratégica...",
        system_prompt=system_prompt,
        context=contexto,
    )

# ========== BOTÃO PRÓXIMA ETAPA ==========
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Painel de Controle", width="stretch"):
        st.switch_page("pages/11_📈_Painel_de_Controle.py")
