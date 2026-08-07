import streamlit as st
from openai import OpenAI


def render_chat(
    *,
    messages_key: str,
    placeholder: str,
    system_prompt: str,
    context: str = "",
    model: str = "openai/gpt-oss-20b",
    temperature: float = 0.7,
):
    """
    Renderiza um chat de IA reutilizável.

    Parameters
    ----------
    messages_key
        Nome da chave no st.session_state para armazenar o histórico.

    placeholder
        Texto exibido no campo de entrada.

    system_prompt
        Prompt específico da página.

    context
        Contexto dinâmico (empresa, Canvas, SWOT etc.).

    model
        Modelo utilizado.

    temperature
        Temperatura da IA.
    """

    if messages_key not in st.session_state:
        st.session_state[messages_key] = []

    # Botão limpar
   # col1, col2 = st.columns([5, 1])

    #with col2:
     #   if st.button("🗑️ Limpar Chat", key=f"clear_{messages_key}"):
      #      st.session_state[messages_key] = []
       #     st.rerun()

    # Histórico
    for msg in st.session_state[messages_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Campo de pergunta + botões
    col_input, col_buttons = st.columns([5, 1])
   
    with col_input:
       pergunta = st.text_area(
           "",
           placeholder=placeholder,
           height=100,
           key=f"pergunta_{messages_key}",
           label_visibility="collapsed"
       )
   
    with col_buttons:
       enviar = st.button(
           "👽 Enviar",
           key=f"enviar_{messages_key}",
           width="stretch"
       )
   
       limpar = st.button(
           "🗑️ Limpar",
           key=f"limpar_{messages_key}",
           width="stretch"
       )
   
    if limpar:
       st.session_state[messages_key] = []
       st.rerun()
   
    if not enviar or not pergunta.strip():
       return
    
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.spinner("🤔 Pensando..."):

        try:

            client = OpenAI(
                api_key=st.secrets["OPENAI_API_KEY"],
                base_url="https://openrouter.ai/api/v1",
            )

            messages = [
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\n{context}",
                }
            ] + st.session_state[messages_key]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )

            resposta = response.choices[0].message.content

            st.session_state[messages_key].append(
                {
                    "role": "assistant",
                    "content": resposta,
                }
            )

            with st.chat_message("assistant"):
                st.markdown(resposta)

        except Exception as e:
            st.error(f"Erro: {e}")
