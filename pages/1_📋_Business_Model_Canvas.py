import streamlit as st
import pandas as pd
import json
import uuid
import re
import streamlit.components.v1 as components    
from openai import OpenAI
from copy import deepcopy
from utils.data_manager import init_data, get_data, sidebar_data_controls
from utils.chat import render_chat
from analytics import init_page
from analytics import Module
from analytics import module_started
from analytics import module_completed
from analytics import track, begin_observation, end_observation
from analytics.item_factory import new_user_item

def get_item_text(item):
    """
    Retorna o texto de um item do Canvas.
    Compatível com o novo formato (dict) e antigo (string).
    """
    if isinstance(item, dict):
        return item.get("texto", "")
    
    return str(item)
    
st.set_page_config(page_title="Business Model Canvas",page_icon="📋",layout="wide")
init_page(Module.CANVAS)
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
sidebar_data_controls()

# ============================================================
# TÍTULO
# ============================================================
st.title("📋 Business Model Canvas")
st.caption(
    "Construa seu modelo de negócio passo a passo. "
    "O SIPE irá guiá-lo desde a identificação dos clientes até a estrutura financeira."
)

if "canvas_started" not in st.session_state:

    module_started(
        Module.CANVAS
    )

    st.session_state.canvas_started = True
# ============================================================
# INICIALIZAÇÃO DOS DADOS
# ============================================================
if "bmc" not in data:
    data["bmc"] = {}
if "bmc_etapa" not in st.session_state:
    st.session_state.bmc_etapa = 0

# ============================================================
# ORDEM GUIADA DO CANVAS
# ============================================================
ETAPAS_BMC = [
    {
        "chave": "segmentos_clientes",
        "titulo": "🎯 Segmentos de Clientes",
        "pergunta": "Quem são as pessoas ou organizações que compram sua solução?",
        "explicacao": """
Os clientes são o ponto de partida do modelo de negócio.

Identifique:
- Quem compra seu produto ou serviço?
- Quem utiliza sua solução?
- Existem diferentes grupos de clientes?
""",
        "exemplos": ["Consumidores finais","Pequenas empresas","Indústrias","Órgãos públicos"]
    },

    {
        "chave": "proposta_valor",
        "titulo": "💎 Proposta de Valor",
        "pergunta": "Qual problema você resolve e qual valor entrega ao cliente?",
        "explicacao": """
A proposta de valor explica por que o cliente escolhe sua empresa.

Pense:
- Qual necessidade você atende?
- Que benefício entrega?
- O que diferencia sua solução?
""",
        "exemplos": ["Preço acessível","Maior qualidade","Conveniência","Experiência diferenciada"]
    },

    {
        "chave": "canais",
        "titulo": "📡 Canais",
        "pergunta": "Como o cliente encontra, compra e recebe sua solução?",
        "explicacao": """
Os canais representam os meios utilizados para chegar até o cliente.

Considere:
- Divulgação
- Venda
- Entrega
- Atendimento
""",
        "exemplos": ["Loja física","Instagram","Site","WhatsApp"]
    },

    {
        "chave": "relacionamento_clientes",
        "titulo": "❤️ Relacionamento com Clientes",
        "pergunta": "Como sua empresa conquista e mantém clientes?",
        "explicacao": """
Defina como será a interação com seus clientes.

Exemplos:
- Atendimento personalizado
- Programa de fidelidade
- Comunidade
- Suporte pós-venda
""",
        "exemplos": ["Atendimento personalizado","Programa de fidelidade","Pós-venda"]
    },

    {
        "chave": "fontes_receita",
        "titulo": "💰 Fontes de Receita",
        "pergunta": "Como sua empresa gera receita?",
        "explicacao": """
Aqui descrevemos como o negócio transforma valor entregue em dinheiro.

Considere:
- O que o cliente paga?
- Como paga?
- Qual modelo de cobrança?
""",
        "exemplos": ["Venda direta","Assinatura mensal","Comissão","Licenciamento"]
    },

    {
        "chave": "recursos_chave",
        "titulo": "🧱 Recursos-Chave",
        "pergunta": "Quais recursos são necessários para o negócio funcionar?",
        "explicacao": """
São os recursos indispensáveis para entregar sua proposta de valor.

Podem ser:
- Pessoas
- Equipamentos
- Tecnologia
- Marca
- Capital
""",
        "exemplos": ["Equipe especializada","Máquinas","Sistema de gestão"]
    },

    {
        "chave": "atividades_chave",
        "titulo": "⚙️ Atividades-Chave",
        "pergunta": "Quais atividades precisam ser realizadas?",
        "explicacao": """
São as principais ações que fazem o modelo funcionar.

Exemplos:
- Produção
- Desenvolvimento
- Atendimento
- Logística
""",
        "exemplos": ["Produção","Marketing","Entrega"]
    },

    {
        "chave": "parcerias_chave",
        "titulo": "🤝 Parcerias-Chave",
        "pergunta": "Quem são os parceiros importantes para o negócio?",
        "explicacao": """
Empresas e pessoas que ajudam seu negócio a funcionar melhor.

Exemplos:
- Fornecedores
- Distribuidores
- Parceiros estratégicos
""",
        "exemplos": ["Fornecedores","Representantes","Parceiros comerciais"]
    },
    {
        "chave": "estrutura_custos",
        "titulo": "💸 Estrutura de Custos",
        "pergunta": "Quais são os principais custos do negócio?",
        "explicacao": """
Liste os principais gastos necessários para operar.

Considere:
- Custos fixos
- Custos variáveis
- Investimentos
""",
        "exemplos": ["Salários", "Aluguel", "Matéria-prima"]
    }
]

# ============================================================
# FUNÇÃO PARA GARANTIR ESTRUTURA DOS DADOS
# ============================================================
def garantir_bloco(chave):
    if chave not in data["bmc"]:
        data["bmc"][chave] = []
    if not isinstance(data["bmc"][chave], list):
        data["bmc"][chave] = []

# ============================================================
# ETAPA ATUAL DO CANVAS
# ============================================================
etapa_atual = st.session_state.bmc_etapa
etapa = ETAPAS_BMC[etapa_atual]
chave = etapa["chave"]
garantir_bloco(chave)

session_key = f"items_{chave}"

# CORREÇÃO: Inicializar com lista de dicionários
if session_key not in st.session_state:
    itens = data["bmc"].get(chave, [])
    if not itens:
        itens = [""]
    st.session_state[session_key] = [
        {
            "id": uuid.uuid4().hex,
            "texto": texto
        }
        for texto in itens
    ]
else:
    # Garantir que os itens estejam no formato correto (dicionários)
    if isinstance(st.session_state[session_key], list):
        # Verificar se já está no formato correto
        if st.session_state[session_key] and isinstance(st.session_state[session_key][0], str):
            # Converter de string para dicionário
            st.session_state[session_key] = [
                {
                    "id": uuid.uuid4().hex,
                    "texto": texto
                }
                for texto in st.session_state[session_key]
            ]    
# ============================================================
# BARRA DE PROGRESSO
# ============================================================
progresso = (etapa_atual + 1) / len(ETAPAS_BMC)
st.progress(progresso,text=f"Etapa {etapa_atual + 1} de {len(ETAPAS_BMC)}")

st.divider()

# ============================================================
# TÍTULO DA ETAPA
# ============================================================
st.header(etapa["titulo"])
st.markdown(
    f"""
### 🤔 Pergunta principal

**{etapa["pergunta"]}**
"""
)

# ============================================================
# EXPLICAÇÃO DIDÁTICA
# ============================================================
with st.expander("💡 Entenda esta etapa", expanded=True):
    st.markdown(etapa["explicacao"])

with st.expander("📌 Exemplos", expanded=False):
    for exemplo in etapa["exemplos"]:
        st.markdown(f"- {exemplo}")

st.divider()
# ============================================================
# ÁREA DE PREENCHIMENTO
# ============================================================
st.subheader("✍️ Construa sua resposta")
indice_remover = None
begin_observation(
    key=chave,
    items=st.session_state[session_key]
)

for item in st.session_state[session_key]:
    col1, col2 = st.columns([18,1], vertical_alignment="center")
    with col1:
        widget_key = f"{chave}_{item['id']}"
        texto = st.text_input(
            "",
            value=item["texto"],
            key=widget_key,
            placeholder="Digite uma informação...",
            label_visibility="collapsed"
        )
        item["texto"] = texto

    with col2:
        if len(st.session_state[session_key]) > 1:
            if st.button(
                "🗑️",
                key=f"remover_{item['id']}",
                use_container_width=True
            ):
                indice_remover = item["id"]

if indice_remover is not None:
    st.session_state[session_key] = [
        x for x in st.session_state[session_key]
        if x["id"] != indice_remover
    ]
    st.rerun()

if st.button(
    "➕ Adicionar outro item",
    use_container_width=True
):
    st.session_state[session_key].append(
        new_user_item()
    )
    st.rerun()

# Atualiza o formato antigo utilizado pelo restante do sistema
data["bmc"][chave] = deepcopy(
    st.session_state[session_key]
)

end_observation(
    key=chave,
    items=st.session_state[session_key],
    module=Module.CANVAS
)
track(
    event="canvas_saved",
    module=Module.CANVAS,
    metadata={
        "filled_blocks": 9
    }
)

# ============================================================
# AJUDA DA IA - GERAR SUGESTÕES
# ============================================================
st.divider()
col_ia1, col_ia2 = st.columns([3,1])
with col_ia1:
    st.info(
        "💡 Use a IA para gerar sugestões para este bloco. "
        "As sugestões serão inseridas automaticamente para você revisar."
    )
with col_ia2:
    gerar_sugestao = st.button("🤖 Gerar sugestões", width="stretch", key=f"ia_{chave}")

if gerar_sugestao:
    track(
        event="ai_request",
        module=Module.CANVAS,
        ai_used=True,
        metadata={
            "block": chave
        }
    )
    
    with st.spinner("🤔 Analisando o modelo de negócio..."):
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            
            empresa = data.get("empresa", {})
            empresa_nome = empresa.get("nome", "").strip()
            empresa_setor = empresa.get("setor", "").strip()
            empresa_cidade = empresa.get("cidade_estado", "").strip()
            
            contexto_empresa = f"""
            EMPRESA: {empresa_nome or "Não informado"}
            SETOR: {empresa_setor or "Não informado"}
            LOCALIZAÇÃO: {empresa_cidade or "Não informado"}
            """
            
            prompt_ia = f"""
            Você é um consultor especialista em Business Model Canvas.
            
            Bloco: {etapa["titulo"]}
            Pergunta orientadora: {etapa["pergunta"]}
            
            Contexto da empresa: {contexto_empresa}
            
            IMPORTANTE: Gere APENAS uma lista de itens simples, sem explicações, sem numeração, sem bullets.
            Cada item deve ser uma frase curta respondendo diretamente à pergunta.
            
            Exemplo de resposta correta:
            {{"sugestoes": ["Consumidores finais da classe média", "Pequenas empresas locais", "Jovens empreendedores"]}}
            
            Responda APENAS com o JSON.
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor de estratégia. Responda APENAS com JSON válido, sem explicações."},
                    {"role": "user", "content": prompt_ia}
                ],
                temperature=0.7
            )
            
            conteudo = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
            if json_match:
                dados = json.loads(json_match.group())
                sugestoes = dados.get("sugestoes", [])
                
                if sugestoes and isinstance(sugestoes, list):
                    sugestoes = [s.strip() for s in sugestoes if s and s.strip()]
                    sugestoes = list(dict.fromkeys(sugestoes))
                    
                    if sugestoes:
                        itens_existentes = data["bmc"].get(chave, [])
                        itens_existentes_texto = [
                            item.get("texto", "")
                            if isinstance(item, dict)
                            else str(item)
                            for item in itens_existentes
                        ]
                        
                        itens_existentes_texto = [
                            item
                            for item in itens_existentes_texto
                            if item.strip()
                        ]
                        
                        existentes_set = set(
                            item.lower().strip()
                            for item in itens_existentes_texto
                        )
                        adicionados = 0
                        for sugestao in sugestoes:
                            if sugestao.lower().strip() not in existentes_set:
                                itens_existentes.append(
                                    {
                                        "id": uuid.uuid4().hex,
                                        "texto": sugestao
                                    }
                                )
                                existentes_set.add(sugestao.lower().strip())
                                adicionados += 1
                        
                        if adicionados > 0:
                                # Atualiza o formato antigo utilizado pelo restante do sistema
                                data["bmc"][chave] = [
                                    item["texto"] if isinstance(item, dict) else str(item)
                                    for item in st.session_state[session_key]
                                    if (isinstance(item, dict) and item["texto"].strip()) or (isinstance(item, str) and item.strip())
                                ]
                                # Converte para o formato usado pela interface
                                st.session_state[session_key] = [
                                    {
                                        "id": uuid.uuid4().hex,
                                        "texto": item["texto"] if isinstance(item, dict) else item
                                    }
                                    for item in itens_existentes
                                ]
                                st.success(
                                    f"✅ {adicionados} sugestões adicionadas! Revise e edite abaixo."
                                )
                                st.rerun()
                        else:
                            st.info("ℹ️ Todas as sugestões já existem no bloco.")
                    else:
                        st.warning("Nenhuma sugestão válida gerada. Tente novamente.")
                else:
                    st.warning("Formato de resposta inválido. Tente novamente.")
            else:
                st.error("Erro ao processar a resposta da IA.")
                st.code(conteudo)
                
        except Exception as e:
            st.error(f"❌ Erro ao consultar IA: {str(e)}")

# ============================================================
# NAVEGAÇÃO
# ============================================================
st.divider()
col_voltar, col_meio, col_avancar = st.columns([1,2,1])
with col_voltar:
    if etapa_atual > 0:
        if st.button("⬅️ Voltar", width="stretch"):
            st.session_state.bmc_etapa -= 1
            st.rerun()

with col_avancar:
    if etapa_atual < len(ETAPAS_BMC)-1:
        if st.button("Próxima etapa do Canvas ➡️",width="stretch"):
            st.session_state.bmc_etapa += 1
            st.rerun()
    else:
        if st.button("🎉 Finalizar Canvas", width="stretch"):
            st.session_state.bmc_finalizado = True
            st.rerun()

# ============================================================
# VISUALIZAÇÃO COMPLETA DO CANVAS - FORMATO TRADICIONAL ALINHADO
# ============================================================
def html_lista(chave):

    itens = data["bmc"].get(chave, [])

    if not itens:
        return "<i>Nenhum item informado.</i>"

    html = "<ul>"

    for item in itens:

        if isinstance(item, dict):
            texto = item.get("texto", "")
        else:
            texto = str(item)

        if texto.strip():
            html += f"<li>{texto}</li>"

    html += "</ul>"

    return html
    
st.divider()

st.header("📊 Business Model Canvas")

canvas_html = f"""

<style>

.canvas{{
display:grid;
grid-template-columns:19% 19% 20% 19% 19%;
grid-template-rows:250px 250px 180px;
gap:10px;
font-family:Arial;
}}

.box{{
border:2px solid #d0d0d0;
border-radius:10px;
padding:12px;
background:#fffef6;
overflow:auto;
}}

.box h3{{
margin-top:0;
margin-bottom:10px;
font-size:18px;
color:#0b5394;
}}

.box ul{{
padding-left:20px;
margin:0;
}}

.box li{{
margin-bottom:6px;
}}

.parcerias{{grid-column:1;grid-row:1;}}

.recursos{{grid-column:1;grid-row:2;}}

.atividades{{grid-column:2;grid-row:1 / span 2;}}

.proposta{{grid-column:3;grid-row:1 / span 2;}}

.relacionamento{{grid-column:4;grid-row:1;}}

.canais{{grid-column:4;grid-row:2;}}

.segmentos{{grid-column:5;grid-row:1 / span 2;}}

.custos{{grid-column:1 / span 3;grid-row:3;}}

.receitas{{grid-column:4 / span 2;grid-row:3;}}

</style>

<div class="canvas">

<div class="box parcerias">
<h3>🤝 Parcerias-Chave</h3>
{html_lista("parcerias_chave")}
</div>

<div class="box recursos">
<h3>🧱 Recursos-Chave</h3>
{html_lista("recursos_chave")}
</div>

<div class="box atividades">
<h3>⚙️ Atividades-Chave</h3>
{html_lista("atividades_chave")}
</div>

<div class="box proposta">
<h3>💎 Proposta de Valor</h3>
{html_lista("proposta_valor")}
</div>

<div class="box relacionamento">
<h3>❤️ Relacionamento</h3>
{html_lista("relacionamento_clientes")}
</div>

<div class="box canais">
<h3>📡 Canais</h3>
{html_lista("canais")}
</div>

<div class="box segmentos">
<h3>🎯 Segmentos de Clientes</h3>
{html_lista("segmentos_clientes")}
</div>

<div class="box custos">
<h3>💸 Estrutura de Custos</h3>
{html_lista("estrutura_custos")}
</div>

<div class="box receitas">
<h3>💰 Fontes de Receita</h3>
{html_lista("fontes_receita")}
</div>

</div>

"""

components.html(canvas_html,height=760,scrolling=True)

# ============================================================
# EXPORTAÇÃO
# ============================================================
st.divider()
col_export1, col_export2, col_export3 = st.columns(3)

with col_export1:
    texto_canvas = "BUSINESS MODEL CANVAS\n"
    texto_canvas += "=" * 40
    texto_canvas += "\n\n"
    
    # Ordem tradicional do Canvas
    ordem_canvas = [
        ("parcerias_chave", "Parcerias-Chave"),
        ("atividades_chave", "Atividades-Chave"),
        ("recursos_chave", "Recursos-Chave"),
        ("proposta_valor", "Proposta de Valor"),
        ("relacionamento_clientes", "Relacionamento com Clientes"),
        ("canais", "Canais"),
        ("segmentos_clientes", "Segmentos de Clientes"),
        ("estrutura_custos", "Estrutura de Custos"),
        ("fontes_receita", "Fontes de Receita")
    ]

    for chave, titulo in ordem_canvas:
        itens = data["bmc"].get(chave, [])
        texto_canvas += f"{titulo}\n"
        if itens:
            for item in itens:
                texto = item.get("texto","") if isinstance(item,dict) else str(item)
                if texto.strip():
                    texto_canvas += f"• {texto}\n"
        else:
            texto_canvas += "(não preenchido)\n"
        texto_canvas += "\n"

    if st.button("📋 Mostrar Canvas em Texto", width="stretch"):
        st.code(texto_canvas, language="markdown")

with col_export2:
    json_canvas = json.dumps(data["bmc"], indent=2, ensure_ascii=False)
    st.download_button(
        "⬇️ Baixar Canvas (.json)",
        data=json_canvas,
        file_name="business_model_canvas.json",
        mime="application/json",
        width="stretch"
    )

with col_export3:
    html_canvas = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ text-align: center; color: #1a1a2e; }}
            .canvas-grid {{ display: grid; grid-template-columns: 1.2fr 1.6fr 1.2fr; gap: 15px; margin-top: 20px; }}
            .bloco {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; min-height: 150px; }}
            .bloco h3 {{ margin-top: 0; }}
            .infra {{ background: #f8f4ff; }}
            .proposta {{ background: #fff8e1; }}
            .canais {{ background: #e3f2fd; }}
            .clientes {{ background: #fff3e0; }}
            .financas {{ background: #e8f5e9; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
            @media print {{
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Business Model Canvas</h1>
            <div class="canvas-grid">
                <div>
                    <div class="bloco infra"><h3>🤝 Parcerias-Chave</h3>
                        <ul>
    """
    
    itens = data["bmc"].get("parcerias_chave", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div>"
    
    html_canvas += f"""
                    <div class="bloco infra"><h3>⚙️ Atividades-Chave</h3><ul>
    """
    itens = data["bmc"].get("atividades_chave", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div>"
    
    html_canvas += f"""
                    <div class="bloco infra"><h3>🧱 Recursos-Chave</h3><ul>
    """
    itens = data["bmc"].get("recursos_chave", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div></div>"
    
    html_canvas += f"""
                <div>
                    <div class="bloco proposta"><h3>💎 Proposta de Valor</h3><ul>
    """
    itens = data["bmc"].get("proposta_valor", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div>"
    
    html_canvas += f"""
                    <div class="bloco canais"><h3>📡 Canais</h3><ul>
    """
    itens = data["bmc"].get("canais", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div>"
    
    html_canvas += f"""
                    <div class="bloco canais"><h3>❤️ Relacionamento com Clientes</h3><ul>
    """
    itens = data["bmc"].get("relacionamento_clientes", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div></div>"
    
    html_canvas += f"""
                <div>
                    <div class="bloco clientes"><h3>🎯 Segmentos de Clientes</h3><ul>
    """
    itens = data["bmc"].get("segmentos_clientes", [])
    if itens:
        for item in itens:
    
            texto = get_item_text(item)
    
            if texto.strip():
                html_canvas += f"<li>{texto}</li>"
    
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    
    html_canvas += f"""
                    <div class="bloco financas"><h3>💸 Estrutura de Custos</h3><ul>
    """
    itens = data["bmc"].get("estrutura_custos", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div>"
    
    html_canvas += f"""
                    <div class="bloco financas"><h3>💰 Fontes de Receita</h3><ul>
    """
    itens = data["bmc"].get("fontes_receita", [])
    if itens:
        for item in itens:
            if item.strip():
                html_canvas += f"<li>{item}</li>"
    else:
        html_canvas += "<li><em>não preenchido</em></li>"
    html_canvas += "</ul></div></div></div></div></body></html>"
    
    st.download_button(
        "⬇️ Baixar Canvas (HTML)",
        data=html_canvas.encode("utf-8"),
        file_name="business_model_canvas.html",
        mime="text/html",
        width="stretch",
        help="Baixe o HTML para imprimir ou visualizar o Canvas no formato tradicional"
    )

# ============================================================
# ASSISTENTE IA GERAL DO CANVAS
# ============================================================
st.divider()
st.subheader("💬 Tem dúvidas? Consulte nosso Assistente IA sobre o Business Model Canvas")

empresa = data.get("empresa", {})
empresa_nome = empresa.get("nome", "").strip()

if not empresa_nome:
    st.warning("⚠️ Cadastre os dados da empresa para utilizar o assistente.")
else:
    contexto_canvas = ""
    for bloco in ETAPAS_BMC:
        itens = data["bmc"].get(bloco["chave"], [])
        contexto_canvas += f"\n{bloco['titulo']}:\n"
        for item in itens:
            contexto_canvas += f"- {item}\n"
    
    contexto = f"""
EMPRESA: {empresa_nome}
SETOR: {empresa.get("setor", "Não informado")}
BUSINESS MODEL CANVAS ATUAL: {contexto_canvas}
"""
    system_prompt = """
Você é um consultor especialista em Business Model Canvas.
Ajude o empreendedor a analisar, melhorar e questionar seu modelo de negócio.
Explique conceitos quando necessário.
Sugira melhorias práticas.
Responda sempre em português do Brasil,
com linguagem simples e objetiva.
"""
    render_chat(
        messages_key="messages_bmc",
        placeholder="Pergunte ao assistente sobre seu Canvas...",
        system_prompt=system_prompt,
        context=contexto
    )

# ============================================================
# BOTÃO PRÓXIMA ETAPA
# ============================================================
col_prox1, col_prox2, col_prox3 = st.columns([1, 2, 1])
with col_prox2:
    if st.button("➡️ Vamos para a Próxima Etapa? > Análise PESTEL", width="stretch"):
        st.switch_page("pages/2_🌍_Análise_PESTEL.py")
