"""
Integração com a API da Anthropic (Claude) para o botão "🤖 Consultar IA".

Fornece:
- get_api_key(): busca a chave em st.secrets ou na sessão (campo da barra lateral)
- ask_claude(system, prompt): chama o modelo e retorna o texto de resposta
- ai_assist_widget(...): componente pronto (expander + botão) para usar em qualquer página
"""

import streamlit as st

MODEL = "claude-sonnet-4-6"


def get_api_key():
    if "api_key_anthropic" in st.session_state and st.session_state["api_key_anthropic"]:
        return st.session_state["api_key_anthropic"]
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


def sidebar_api_key_input():
    st.sidebar.markdown("### 🤖 Assistente de IA (Claude)")
    key = st.sidebar.text_input(
        "Chave da API Anthropic",
        type="password",
        value=st.session_state.get("api_key_anthropic", ""),
        help="Cole sua chave da API da Anthropic. Fica salva apenas na sessão do navegador.",
    )
    st.session_state["api_key_anthropic"] = key
    if not key and "ANTHROPIC_API_KEY" not in st.secrets:
        st.sidebar.caption("Sem chave configurada, os botões 'Consultar IA' ficarão desativados.")


def ask_claude(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    api_key = get_api_key()
    if not api_key:
        return (
            "⚠️ Nenhuma chave de API configurada. Informe sua chave da Anthropic "
            "na barra lateral para usar o assistente de IA."
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        return "\n".join(parts).strip() or "A IA não retornou conteúdo."
    except Exception as e:
        return f"❌ Erro ao consultar a IA: {e}"


def ai_assist_widget(field_key: str, contexto_label: str, system_prompt: str, prompt_builder):
    """
    Componente reutilizável de apoio da IA.

    field_key: chave única (usada nos widgets internos)
    contexto_label: texto mostrado no título do expander
    system_prompt: instrução de sistema para o Claude (papel/consultor)
    prompt_builder: função que recebe (instrucao_usuario) e devolve o prompt final,
                     já incluindo o contexto atual preenchido pelo usuário.

    Retorna a sugestão aceita pelo usuário (string) ou None.
    """
    resp_key = f"ai_resp_{field_key}"
    with st.expander(f"🤖 Consultar IA — {contexto_label}"):
        instrucao = st.text_area(
            "Peça algo específico (opcional): sugestão de preenchimento, exemplo, validação do que já escrevi...",
            key=f"ai_inst_{field_key}",
            placeholder="Ex: sugira 3 exemplos, ou valide o que já escrevi e aponte melhorias",
            height=80,
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            consultar = st.button("Consultar IA", key=f"ai_btn_{field_key}", use_container_width=True)
        with col2:
            limpar = st.button("Limpar resposta", key=f"ai_clear_{field_key}", use_container_width=True)

        if limpar and resp_key in st.session_state:
            del st.session_state[resp_key]
            st.rerun()

        if consultar:
            prompt = prompt_builder(instrucao)
            with st.spinner("Consultando a IA..."):
                resposta = ask_claude(system_prompt, prompt)
            st.session_state[resp_key] = resposta

        if resp_key in st.session_state:
            st.markdown("**Sugestão da IA:**")
            st.markdown(st.session_state[resp_key])
            return st.session_state[resp_key]
    return None
