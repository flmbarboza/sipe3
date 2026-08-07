import streamlit as st
from utils.data_manager import init_data, get_data, sidebar_data_controls
from utils.chat import render_chat
import base64
import pandas as pd
from datetime import datetime
from openai import OpenAI
from analytics import Module
from analytics import module_started
from analytics import module_completed
from analytics import track
from analytics import EventType

st.set_page_config(page_title="Relatório Completo", page_icon="📄", layout="wide")
init_data()
data = get_data()

st.sidebar.title("🧭 Gestor Estratégico")
module_started(
    Module.RELATORIO
)
sidebar_data_controls()

st.title("📄 Relatório Completo")
st.caption(
    "Compilação de todas as seções preenchidas, pronta para revisão, download e apresentação. "
    "Use o botão 'Imprimir' para gerar uma versão para PDF."
)


def linha(label, valor):
    return f"- **{label}:** {valor}\n" if valor else ""


def build_markdown():
    empresa = data.get("empresa", {})
    md = f"# Planejamento Estratégico — {empresa.get('nome') or '(empresa sem nome)'}\n\n"
    md += f"**Data de geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    md += linha("Setor", empresa.get("setor"))
    md += linha("Cidade/Estado", empresa.get("cidade_estado"))
    md += linha("Responsável", empresa.get("responsavel"))
    md += "\n---\n\n"

    # ========== 0. INÍCIO - DADOS DA EMPRESA ==========
    md += "## 0. Dados da Empresa\n\n"
    md += linha("Nome", empresa.get("nome"))
    md += linha("Setor", empresa.get("setor"))
    md += linha("Cidade/Estado", empresa.get("cidade_estado"))
    md += linha("Responsável", empresa.get("responsavel"))
    md += "\n---\n\n"

    # ========== 1. BUSINESS MODEL CANVAS ==========
    md += "## 1. Business Model Canvas\n\n"
    nomes_bmc = {
        "parcerias_chave": "Parcerias-Chave", 
        "atividades_chave": "Atividades-Chave",
        "recursos_chave": "Recursos-Chave", 
        "proposta_valor": "Proposta de Valor",
        "relacionamento_clientes": "Relacionamento com Clientes", 
        "canais": "Canais",
        "segmentos_clientes": "Segmentos de Clientes", 
        "estrutura_custos": "Estrutura de Custos",
        "fontes_receita": "Fontes de Receita",
    }
    
    if "bmc" in data and isinstance(data["bmc"], dict):
        for chave, nome in nomes_bmc.items():
            conteudo = data["bmc"].get(chave, "")
            if isinstance(conteudo, list):
                conteudo = "\n".join([f"- {item}" for item in conteudo if item])
            elif isinstance(conteudo, str):
                conteudo = conteudo.strip()
            else:
                conteudo = ""
            
            if conteudo:
                md += f"### {nome}\n{conteudo}\n\n"
    else:
        md += "*Nenhum dado do Business Model Canvas encontrado.*\n\n"

    md += "---\n\n"

    # ========== 2. ANÁLISE PESTEL ==========
    md += "## 2. Análise PESTEL\n\n"
    if "pestel" in data and isinstance(data["pestel"], dict):
        tem_pestel = False
        for cat, itens in data["pestel"].items():
            if isinstance(itens, list):
                itens_validos = [i for i in itens if isinstance(i, dict) and i.get("descricao")]
                if itens_validos:
                    tem_pestel = True
                    md += f"### {cat}\n"
                    for i in itens_validos:
                        md += f"- ({i.get('tipo', '')}, impacto {i.get('impacto', '')}) {i.get('descricao', '')}\n"
                    md += "\n"
        if not tem_pestel:
            md += "*Nenhum dado da análise PESTEL encontrado.*\n\n"
    else:
        md += "*Nenhum dado da análise PESTEL encontrado.*\n\n"

    md += "---\n\n"

    # ========== 3. 5 FORÇAS DE PORTER ==========
    md += "## 3. Cinco Forças de Porter\n\n"
    tem_porter = False
    if "porter_analise" in data and isinstance(data["porter_analise"], dict):
        for forca_id, info in data["porter_analise"].items():
            if isinstance(info, dict):
                tem_porter = True
                md += f"### {info.get('nome', forca_id)}\n"
                md += f"- **Intensidade:** {info.get('intensidade', 0)}/5\n"
                if info.get("notas"):
                    md += f"- **Observações:** {info['notas']}\n"
                md += "\n"
    elif "porter" in data and isinstance(data["porter"], dict):
        for forca, info in data["porter"].items():
            if isinstance(info, dict):
                tem_porter = True
                md += f"### {forca}\n"
                md += f"- **Intensidade:** {info.get('intensidade', 0)}/5\n"
                if info.get("notas"):
                    md += f"- **Observações:** {info['notas']}\n"
                md += "\n"
    if not tem_porter:
        md += "*Nenhum dado das 5 Forças de Porter encontrado.*\n\n"

    md += "---\n\n"

    # ========== 4. ANÁLISE SWOT ==========
    md += "## 4. Análise SWOT\n\n"
    nomes_swot = {"forcas": "💪 Forças", "fraquezas": "⚠️ Fraquezas", "oportunidades": "🌱 Oportunidades", "ameacas": "🌩️ Ameaças"}
    tem_swot = False
    if "swot" in data and isinstance(data["swot"], dict):
        for chave, nome in nomes_swot.items():
            itens = data["swot"].get(chave, [])
            if isinstance(itens, list):
                itens_validos = [i.get("descricao", "") for i in itens if isinstance(i, dict) and i.get("descricao")]
                if itens_validos:
                    tem_swot = True
                    md += f"### {nome}\n"
                    for i in itens_validos:
                        md += f"- {i}\n"
                    md += "\n"
    if not tem_swot:
        md += "*Nenhum dado da análise SWOT encontrado.*\n\n"

    md += "---\n\n"

    # ========== 5. PLANEJAMENTO ESTRATÉGICO ==========
    md += "## 5. Planejamento Estratégico\n\n"

    # 5.1 MVV
    md += "### 5.1 Missão, Visão e Valores\n\n"
    if "mvv" in data and isinstance(data["mvv"], dict):
        if data["mvv"].get("missao"):
            md += f"**Missão:** {data['mvv']['missao']}\n\n"
        if data["mvv"].get("visao"):
            md += f"**Visão:** {data['mvv']['visao']}\n\n"
        if data["mvv"].get("valores"):
            md += "**Valores:**\n"
            for v in data["mvv"]["valores"]:
                if v:
                    md += f"- {v}\n"
            md += "\n"
    else:
        md += "*Nenhum dado de Missão, Visão e Valores encontrado.*\n\n"

    # 5.2 SWOT Cruzada
    md += "### 5.2 SWOT Cruzada\n\n"
    nomes_cruz = {
        "SO": "🚀 SO — Forças + Oportunidades", 
        "ST": "🛡️ ST — Forças + Ameaças",
        "WO": "🔧 WO — Fraquezas + Oportunidades", 
        "WT": "🚧 WT — Fraquezas + Ameaças"
    }
    tem_cruz = False
    if "swot_cruzada" in data and isinstance(data["swot_cruzada"], dict):
        for chave, nome in nomes_cruz.items():
            itens = data["swot_cruzada"].get(chave, [])
            if isinstance(itens, list):
                itens_validos = [i.get("estrategia", "") for i in itens if isinstance(i, dict) and i.get("estrategia")]
                if itens_validos:
                    tem_cruz = True
                    md += f"**{nome}**\n"
                    for i in itens_validos:
                        md += f"- {i}\n"
                    md += "\n"
    if not tem_cruz:
        md += "*Nenhuma estratégia da SWOT Cruzada encontrada.*\n\n"

    # 5.3 Objetivos
    md += "### 5.3 Objetivos Estratégicos, KPIs e Metas\n\n"
    if "objetivos" in data and isinstance(data["objetivos"], list):
        tem_obj = False
        for obj in data["objetivos"]:
            if isinstance(obj, dict) and obj.get("objetivo"):
                tem_obj = True
                md += (
                    f"- **{obj.get('objetivo')}** ({obj.get('perspectiva', '')}) — "
                    f"KPI: {obj.get('kpi', '')} | Meta: {obj.get('meta', '')} | Prazo: {obj.get('prazo', '')}\n"
                )
        if not tem_obj:
            md += "*Nenhum objetivo estratégico encontrado.*\n\n"
        md += "\n"
    else:
        md += "*Nenhum objetivo estratégico encontrado.*\n\n"

    md += "---\n\n"

    # ========== 6. PLANO DE AÇÃO 5W2H ==========
    md += "## 6. Plano de Ação (5W2H)\n\n"
    if "acao_5w2h" in data and isinstance(data["acao_5w2h"], list):
        tem_acao = False
        for a in data["acao_5w2h"]:
            if isinstance(a, dict) and a.get("what"):
                tem_acao = True
                md += f"### {a.get('what')}\n"
                md += f"- **Por quê:** {a.get('why', '')}\n"
                md += f"- **Onde:** {a.get('where', '')}\n"
                md += f"- **Quando:** {a.get('when', '')}\n"
                md += f"- **Quem:** {a.get('who', '')}\n"
                md += f"- **Como:** {a.get('how', '')}\n"
                md += f"- **Quanto custa:** {a.get('how_much', '')}\n"
                md += f"- **Status:** {a.get('status', '')}\n\n"
        if not tem_acao:
            md += "*Nenhuma ação do plano 5W2H encontrada.*\n\n"
    else:
        md += "*Nenhum plano de ação encontrado.*\n\n"

    md += "---\n\n"

    # ========== 7. PLANOS POR FUNÇÃO ==========
    md += "## 7. Planos por Função (Departamentais)\n\n"
    if "departamentos" in data and isinstance(data["departamentos"], dict):
        for depto, info in data["departamentos"].items():
            md += f"### {depto}\n\n"
            
            if info.get("objetivos"):
                md += "**Objetivos:**\n"
                for obj in info["objetivos"]:
                    if obj.get("Objetivo"):
                        md += f"- {obj.get('Objetivo')} (Prioridade: {obj.get('Prioridade', '')}, Responsável: {obj.get('Responsável', '')})\n"
                md += "\n"
            
            if info.get("acoes"):
                md += "**Ações:**\n"
                for acao in info["acoes"]:
                    if acao.get("Ação"):
                        md += f"- {acao.get('Ação')} - Status: {acao.get('Situação', '')}\n"
                md += "\n"
            
            if info.get("indicadores"):
                md += "**Indicadores:**\n"
                for ind in info["indicadores"]:
                    if ind.get("Indicador"):
                        md += f"- {ind.get('Indicador')} - Meta: {ind.get('Meta', '')}\n"
                md += "\n"
            
            if info.get("recursos"):
                md += "**Recursos:**\n"
                for rec in info["recursos"]:
                    if rec.get("Recurso"):
                        md += f"- {rec.get('Recurso')} - Valor: {rec.get('Valor estimado', '')}\n"
                md += "\n"
            
            if info.get("riscos"):
                md += "**Riscos:**\n"
                for risco in info["riscos"]:
                    if risco.get("Risco"):
                        md += f"- {risco.get('Risco')} (Probabilidade: {risco.get('Probabilidade', '')}, Impacto: {risco.get('Impacto', '')})\n"
                md += "\n"
    else:
        md += "*Nenhum plano departamental encontrado.*\n\n"

    md += "---\n\n"

    # ========== 8. ORÇAMENTO ==========
    md += "## 8. Orçamento\n\n"
    if "orcamento" in data and isinstance(data["orcamento"], dict):
        orc = data["orcamento"]
        
        if orc.get("receitas"):
            md += "### Receitas Previstas\n"
            for r in orc["receitas"]:
                if r.get("Descrição"):
                    md += f"- {r.get('Descrição')}: R$ {r.get('Valor', '0')} (Fonte: {r.get('Fonte', '')})\n"
            md += "\n"
        
        if orc.get("investimentos"):
            md += "### Investimentos\n"
            for i in orc["investimentos"]:
                if i.get("Descrição"):
                    md += f"- {i.get('Descrição')}: R$ {i.get('Valor', '0')}\n"
            md += "\n"
        
        custos_departamentos = []
        if "departamentos" in data:
            for depto, info in data["departamentos"].items():
                for rec in info.get("recursos", []):
                    if rec.get("Recurso") and rec.get("Valor estimado"):
                        valor_str = str(rec.get("Valor estimado", "0"))
                        valor_limpo = valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        try:
                            valor = float(valor_limpo)
                        except:
                            valor = 0
                        custos_departamentos.append({
                            "Departamento": depto,
                            "Recurso": rec.get("Recurso"),
                            "Valor": valor
                        })
        
        if custos_departamentos:
            md += "### Custos Consolidados por Departamento\n"
            for c in custos_departamentos:
                md += f"- {c['Departamento']} - {c['Recurso']}: R$ {c['Valor']:,.2f}\n"
            md += "\n"
        
        md += "### Indicadores Financeiros\n"
        total_receitas = 0
        for r in orc.get("receitas", []):
            try:
                valor_str = str(r.get("Valor", "0")).replace("R$", "").replace(".", "").replace(",", ".").strip()
                total_receitas += float(valor_str)
            except:
                pass
        
        total_custos = sum([c["Valor"] for c in custos_departamentos])
        
        total_investimentos = 0
        for i in orc.get("investimentos", []):
            try:
                valor_str = str(i.get("Valor", "0")).replace("R$", "").replace(".", "").replace(",", ".").strip()
                total_investimentos += float(valor_str)
            except:
                pass
        
        md += f"- **Receita Total:** R$ {total_receitas:,.2f}\n"
        md += f"- **Custo Total:** R$ {total_custos:,.2f}\n"
        md += f"- **Investimento Total:** R$ {total_investimentos:,.2f}\n"
        if total_receitas > 0:
            margem = (total_receitas - total_custos) / total_receitas
            md += f"- **Margem:** {margem:.1%}\n"
        if total_investimentos > 0:
            roi = (total_receitas - total_custos - total_investimentos) / total_investimentos
            md += f"- **ROI:** {roi:.1%}\n"
        md += "\n"
    else:
        md += "*Nenhum dado de orçamento encontrado.*\n\n"

    # ========== 9. MONITORAMENTO ==========
    md += "## 9. Monitoramento\n\n"
    if "monitoramento" in data and isinstance(data["monitoramento"], dict):
        mon = data["monitoramento"]
        
        if mon.get("alertas"):
            md += "### Alertas Ativos\n"
            for alerta in mon["alertas"]:
                if alerta.get("Descrição"):
                    md += f"- **{alerta.get('Tipo', '')}**: {alerta.get('Descrição', '')} (Prioridade: {alerta.get('Prioridade', '')})\n"
            md += "\n"
        
        if "objetivos" in data:
            kpis = []
            for obj in data["objetivos"]:
                if obj.get("kpi"):
                    kpis.append({
                        "KPI": obj.get("kpi"),
                        "Meta": obj.get("meta", ""),
                        "Prazo": obj.get("prazo", "")
                    })
            if kpis:
                md += "### KPIs Estratégicos\n"
                for kpi in kpis:
                    md += f"- {kpi['KPI']} - Meta: {kpi['Meta']} - Prazo: {kpi['Prazo']}\n"
                md += "\n"
        
        total_acoes = 0
        concluidas = 0
        andamento = 0
        nao_iniciadas = 0
        atrasadas = 0
        
        for acao in data.get("acao_5w2h", []):
            if acao.get("what"):
                total_acoes += 1
                status = acao.get("status", "Não iniciado")
                if status == "Concluído":
                    concluidas += 1
                elif status == "Em andamento":
                    andamento += 1
                elif status == "Atrasado":
                    atrasadas += 1
                else:
                    nao_iniciadas += 1
        
        if total_acoes > 0:
            md += "### Status das Ações\n"
            md += f"- **Total:** {total_acoes}\n"
            md += f"- **Concluídas:** {concluidas}\n"
            md += f"- **Em andamento:** {andamento}\n"
            md += f"- **Não iniciadas:** {nao_iniciadas}\n"
            md += f"- **Atrasadas:** {atrasadas}\n"
            md += f"- **Taxa de Conclusão:** {concluidas/total_acoes*100:.1f}%\n\n"
    else:
        md += "*Nenhum dado de monitoramento encontrado.*\n\n"

    md += "---\n\n"

    # ========== 10. REVISÃO ==========
    md += "## 10. Revisão Estratégica\n\n"
    if "revisao" in data and isinstance(data["revisao"], dict):
        rev = data["revisao"]
        
        if rev.get("resultados"):
            md += "### Resultados Alcançados\n"
            for r in rev["resultados"]:
                if r.get("Resultado"):
                    md += f"- {r.get('Resultado')} - {r.get('Data', '')}\n"
            md += "\n"
        
        if rev.get("objetivos_atingidos"):
            md += "### Objetivos Atingidos\n"
            for o in rev["objetivos_atingidos"]:
                if o.get("Objetivo"):
                    md += f"- {o.get('Objetivo')} - {o.get('Data Conclusão', '')}\n"
            md += "\n"
        
        if rev.get("objetivos_nao_atingidos"):
            md += "### Objetivos Não Atingidos\n"
            for o in rev["objetivos_nao_atingidos"]:
                if o.get("Objetivo"):
                    md += f"- {o.get('Objetivo')} - Motivo: {o.get('Motivo', '')}\n"
            md += "\n"
        
        if rev.get("licoes_aprendidas"):
            md += f"### Lições Aprendidas\n{rev['licoes_aprendidas']}\n\n"
        
        if rev.get("mudancas"):
            md += "### Mudanças no Ambiente\n"
            for tipo, texto in rev["mudancas"].items():
                if texto:
                    md += f"- **{tipo.capitalize()}**: {texto}\n"
            md += "\n"
    else:
        md += "*Nenhum dado de revisão estratégica encontrado.*\n\n"

    md += "---\n\n"

    # ========== 11. PAINEL DE CONTROLE ==========
    md += "## 11. Painel de Controle (Dashboard)\n\n"
    
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
    
    md += f"**Progresso do Planejamento:** {progresso:.0f}%\n\n"
    md += f"**Seções preenchidas:** {preenchidas} de {total_secoes}\n\n"
    
    md += "### Status por Seção\n\n"
    secoes = [
        ("Dados da Empresa", data.get("empresa", {}).get("nome")),
        ("Business Model Canvas", any(data.get("bmc", {}).values())),
        ("Análise PESTEL", any([any([i.get("descricao") for i in itens]) for itens in data.get("pestel", {}).values()])),
        ("5 Forças de Porter", any([v.get("notas") for v in data.get("porter_analise", {}).values()])),
        ("Análise SWOT", any([any([i.get("descricao") for i in itens]) for itens in data.get("swot", {}).values()])),
        ("Missão, Visão e Valores", data.get("mvv", {}).get("missao") or data.get("mvv", {}).get("visao")),
        ("Objetivos Estratégicos", any([o.get("objetivo") for o in data.get("objetivos", [])])),
        ("Plano de Ação 5W2H", any([a.get("what") for a in data.get("acao_5w2h", [])])),
        ("Planos Departamentais", any([any([v for v in depto.values() if v]) for depto in data.get("departamentos", {}).values()])),
        ("Orçamento", data.get("orcamento", {}).get("receitas") or data.get("orcamento", {}).get("investimentos")),
        ("Monitoramento", data.get("monitoramento", {}).get("alertas")),
    ]
    
    for nome, status in secoes:
        status_texto = "✅" if status else "❌"
        md += f"- {status_texto} {nome}\n"
    
    total_acoes = 0
    concluidas = 0
    for acao in data.get("acao_5w2h", []):
        if acao.get("what"):
            total_acoes += 1
            if acao.get("status") == "Concluído":
                concluidas += 1
    
    md += f"\n### Resumo de Ações\n"
    md += f"- **Total de Ações:** {total_acoes}\n"
    md += f"- **Ações Concluídas:** {concluidas}\n"
    if total_acoes > 0:
        md += f"- **Taxa de Conclusão:** {concluidas/total_acoes*100:.1f}%\n"

    return md


markdown_texto = build_markdown()

st.subheader("👁️ Pré-visualização")
with st.container(border=True):
    st.markdown(markdown_texto)

st.divider()
st.subheader("⬇️ Exportar relatório")

col1, col2, col3 = st.columns(3)
with col1:
    st.download_button(
        "⬇️ Baixar em Markdown (.md)",
        data=markdown_texto.encode("utf-8"),
        file_name="relatorio_planejamento_estrategico.md",
        mime="text/markdown",
        width="stretch",
    )
with col2:
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; }}
            h1 {{ color: #1a1a2e; border-bottom: 2px solid #1a1a2e; }}
            h2 {{ color: #16213e; margin-top: 30px; }}
            h3 {{ color: #0f3460; }}
            ul {{ margin-top: 5px; }}
            li {{ margin-bottom: 3px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            @media print {{
                body {{ padding: 20px; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {markdown_texto.replace('\n', '<br>').replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>')}
        </div>
        <script>
            window.print();
        </script>
    </body>
    </html>
    """
    
    st.download_button(
        "🖨️ Imprimir / Salvar como PDF",
        data=html_content.encode("utf-8"),
        file_name="relatorio_planejamento_estrategico.html",
        mime="text/html",
        width="stretch",
        help="Baixe o HTML e abra no navegador para imprimir como PDF"
    )
    
    st.caption("💡 Baixe o HTML, abra no navegador e use Ctrl+P (ou Cmd+P) para salvar como PDF")

with col3:
    if st.button("📋 Copiar Relatório", width="stretch"):
        st.code(markdown_texto, language="markdown")

st.divider()
st.subheader("🤖 Validação final com a IA")
st.caption(
    "A IA vai analisar todo o planejamento estratégico e apontar inconsistências, lacunas, "
    "incoerências e problemas de gestão. Receba um diagnóstico completo do seu planejamento."
)

if st.button("🔍 Executar Revisão Completa do Planejamento", width="stretch"):
    with st.spinner("🔄 Analisando todo o planejamento estratégico..."):
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url="https://openrouter.ai/api/v1")
            
            empresa_nome = data.get("empresa", {}).get("nome", "a empresa")
            empresa_setor = data.get("empresa", {}).get("setor", "não informado")
            
            resumo = f"""
            EMPRESA: {empresa_nome}
            SETOR: {empresa_setor}
            
            DADOS DA EMPRESA:
            - Nome: {data.get('empresa', {}).get('nome', 'Não informado')}
            - Setor: {data.get('empresa', {}).get('setor', 'Não informado')}
            - Cidade: {data.get('empresa', {}).get('cidade_estado', 'Não informado')}
            
            BUSINESS MODEL CANVAS:
            {chr(10).join([f"- {k}: {v}" for k, v in data.get('bmc', {}).items() if v]) if data.get('bmc') else 'Não preenchido'}
            
            ANÁLISE PESTEL:
            {chr(10).join([f"- {cat}: {len([i for i in itens if i.get('descricao')])} itens" for cat, itens in data.get('pestel', {}).items()]) if data.get('pestel') else 'Não preenchido'}
            
            SWOT:
            - Forças: {len([i for i in data.get('swot', {}).get('forcas', []) if i.get('descricao')])}
            - Fraquezas: {len([i for i in data.get('swot', {}).get('fraquezas', []) if i.get('descricao')])}
            - Oportunidades: {len([i for i in data.get('swot', {}).get('oportunidades', []) if i.get('descricao')])}
            - Ameaças: {len([i for i in data.get('swot', {}).get('ameacas', []) if i.get('descricao')])}
            
            MVV:
            - Missão: {data.get('mvv', {}).get('missao', 'Não definida')}
            - Visão: {data.get('mvv', {}).get('visao', 'Não definida')}
            - Valores: {len(data.get('mvv', {}).get('valores', []))} valores definidos
            
            OBJETIVOS ESTRATÉGICOS:
            {len([o for o in data.get('objetivos', []) if o.get('objetivo')])} objetivos definidos
            
            PLANO DE AÇÃO 5W2H:
            {len([a for a in data.get('acao_5w2h', []) if a.get('what')])} ações definidas
            
            PLANOS DEPARTAMENTAIS:
            {len(data.get('departamentos', {}))} departamentos
            """
            
            prompt = f"""
            Você é um consultor sênior de estratégia empresarial especializado em diagnóstico e revisão de planejamentos estratégicos.
            
            {resumo}
            
            Analise criticamente TODO o planejamento estratégico apresentado acima e forneça um diagnóstico completo.
            
            Sua análise deve abordar OBRIGATORIAMENTE:
            
            1. INCONSISTÊNCIAS - identifique contradições entre as diferentes seções do planejamento
            2. LACUNAS - identifique o que está faltando ou incompleto
            3. INCOERÊNCIAS - identifique elementos que não fazem sentido juntos
            4. PROBLEMAS DE GESTÃO - identifique problemas de governança e execução
            5. RECOMENDAÇÕES PRIORITÁRIAS - liste as ações mais urgentes para corrigir os problemas identificados
            
            Seja rigoroso, crítico e objetivo. Não seja complacente.
            Aponte problemas reais que comprometem a execução do planejamento.
            
            Formate sua resposta como um relatório estruturado com os 5 tópicos acima.
            """
            
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Você é um consultor sênior de estratégia empresarial. Seja rigoroso, crítico e objetivo. Responda em português do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            resposta = response.choices[0].message.content
            st.session_state["revisao_ia"] = resposta
            
        except Exception as e:
            st.error(f"❌ Erro ao processar a revisão: {str(e)}")

if "revisao_ia" in st.session_state:
    st.markdown("### 📋 Diagnóstico do Planejamento")
    st.markdown(st.session_state["revisao_ia"])
    
    if st.button("🗑️ Limpar Revisão", width="stretch"):
        del st.session_state["revisao_ia"]
        st.rerun()

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
    RELATÓRIO COMPLETO DO PLANEJAMENTO ESTRATÉGICO

    EMPRESA: {empresa_nome}
    SETOR: {empresa.get('setor', 'Não informado')}
    LOCALIZAÇÃO: {empresa.get('cidade_estado', 'Não informado')}

    O relatório consolida todas as seções do planejamento:
    1. Dados da Empresa
    2. Business Model Canvas
    3. Análise PESTEL
    4. 5 Forças de Porter
    5. Análise SWOT
    6. Planejamento Estratégico (MVV, SWOT Cruzada, Objetivos)
    7. Plano de Ação 5W2H
    8. Planos por Função (Departamentais)
    9. Orçamento
    10. Monitoramento
    11. Revisão Estratégica
    12. Painel de Controle
    """

    system_prompt = """
    Você é um assistente especialista em Planejamento Estratégico.

    Responda em português do Brasil, de forma prática e objetiva.

    Ajude o usuário a:
    - Entender o conteúdo do relatório
    - Identificar pontos fortes e fracos do planejamento
    - Sugerir melhorias e ajustes
    - Preparar apresentações e comunicação
    """

    render_chat(
        messages_key="messages_relatorio",
        placeholder="Pergunte ao assistente sobre o relatório...",
        system_prompt=system_prompt,
        context=contexto,
    )

st.info(
    "💡 Este relatório consolida todas as 11 seções do planejamento estratégico na ordem correta: "
    "Início, BMC, PESTEL, Porter, SWOT, Planejamento Estratégico, Plano de Ação, Planos por Função, "
    "Orçamento, Monitoramento, Revisão e Painel de Controle."
)
