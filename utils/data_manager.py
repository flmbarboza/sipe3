"""
Gerenciador central de dados do Gestor Estratégico.

Toda a informação do app fica em st.session_state["data"], seguindo
uma estrutura única (dicionário aninhado). Este módulo cuida de:
- inicializar a estrutura padrão
- exportar/importar tudo em JSON (upload/download)
- funções auxiliares de leitura/escrita seguras
"""

import json
import copy
import streamlit as st
import pandas as pd

DEFAULT_DATA = {
    "empresa": {
        "nome": "",
        "setor": "",
        "cidade_estado": "",
        "responsavel": "",
    },
    "bmc": {
        "parcerias_chave": "",
        "atividades_chave": "",
        "recursos_chave": "",
        "proposta_valor": "",
        "relacionamento_clientes": "",
        "canais": "",
        "segmentos_clientes": "",
        "estrutura_custos": "",
        "fontes_receita": "",
    },
    "pestel": {
        "Político": [],
        "Econômico": [],
        "Social": [],
        "Tecnológico": [],
        "Ecológico": [],
        "Legal": [],
    },
    "porter": {
        "Rivalidade entre concorrentes": {"intensidade": 3, "notas": ""},
        "Poder de barganha dos clientes": {"intensidade": 3, "notas": ""},
        "Poder de barganha dos fornecedores": {"intensidade": 3, "notas": ""},
        "Ameaça de novos entrantes": {"intensidade": 3, "notas": ""},
        "Ameaça de produtos substitutos": {"intensidade": 3, "notas": ""},
    },
    "swot": {
        "forcas": [],
        "fraquezas": [],
        "oportunidades": [],
        "ameacas": [],
    },
    "mvv": {
        "missao": "",
        "visao": "",
        "valores": [],
    },
    "swot_cruzada": {
        "SO": [],
        "ST": [],
        "WO": [],
        "WT": [],
    },
    "objetivos": [],
    "financeiro": {
        "investimento_inicial": 0.0,
        "receitas": [],
        "custos": [],
        "horizonte_meses": 12,
    },
    "acao_5w2h": [],
}


def init_data():
    """Garante que st.session_state['data'] existe com a estrutura padrão."""
    if "data" not in st.session_state:
        st.session_state["data"] = copy.deepcopy(DEFAULT_DATA)
    else:
        # Preenche chaves novas que possam ter sido adicionadas em versões futuras
        _merge_defaults(st.session_state["data"], DEFAULT_DATA)


def _merge_defaults(current, defaults):
    for key, value in defaults.items():
        if key not in current:
            current[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(current.get(key), dict):
            _merge_defaults(current[key], value)


def get_data():
    init_data()
    return st.session_state["data"]


def to_json_bytes():
    data = get_data()
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def load_json_bytes(file_bytes):
    """Carrega um JSON exportado anteriormente e substitui os dados da sessão."""
    novo = json.loads(file_bytes.decode("utf-8"))
    merged = copy.deepcopy(DEFAULT_DATA)
    _merge_defaults(novo, DEFAULT_DATA)
    merged.update(novo)
    st.session_state["data"] = merged


def reset_data():
    st.session_state["data"] = copy.deepcopy(DEFAULT_DATA)


def sidebar_data_controls():
    """Widgets de upload/download reutilizados em todas as páginas (barra lateral)."""
    st.sidebar.markdown("### 💾 Dados do planejamento")

    st.sidebar.download_button(
        "⬇️ Baixar dados (.json)",
        data=to_json_bytes(),
        file_name="gestor_estrategico_dados.json",
        mime="application/json",
        use_container_width=True,
    )

    uploaded = st.sidebar.file_uploader(
        "⬆️ Carregar dados (.json)", type=["json"], key="upload_dados_json"
    )
    if uploaded is not None:
        if st.sidebar.button("Confirmar importação", use_container_width=True):
            try:
                load_json_bytes(uploaded.getvalue())
                st.sidebar.success("Dados carregados com sucesso!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Erro ao importar: {e}")

    with st.sidebar.expander("⚠️ Zerar tudo"):
        st.write("Isso apaga todos os dados preenchidos na sessão atual.")
        if st.button("Confirmar reset total", type="primary"):
            reset_data()
            st.rerun()
