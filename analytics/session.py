import streamlit as st
import uuid
import time
import hashlib


def _get_browser_fingerprint():
    """
    Gera um fingerprint do navegador baseado em IP + User-Agent.
    Permite identificar o mesmo usuário em sessões diferentes
    (desde que use o mesmo navegador na mesma rede).
    """
    try:
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", headers.get("Remote-Addr", "unknown"))
        ua = headers.get("User-Agent", "unknown")
        raw = f"{ip}|{ua}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception:
        return None


def get_user_id():
    """
    Retorna um identificador único do usuário.
    Ordem de prioridade:
      1. Email do Streamlit Cloud (se autenticado)
      2. Fingerprint do navegador (IP + User-Agent)
      3. UUID persistente na sessão (fallback)
    """
    if "analytics_user_id" not in st.session_state:
        user_id = None

        # 1. Streamlit Cloud auth
        try:
            email = st.experimental_user.email
            if email:
                user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
        except Exception:
            pass

        # 2. Browser fingerprint
        if not user_id:
            user_id = _get_browser_fingerprint()

        # 3. Sessão local (muda se recarregar, mas útil para debug)
        if not user_id:
            user_id = f"sess_{uuid.uuid4().hex[:12]}"

        st.session_state.analytics_user_id = user_id

    return st.session_state.analytics_user_id


def module_enter(module):
    st.session_state["analytics_current_module"] = module
    st.session_state["analytics_module_start"] = time.time()


def module_duration():
    inicio = st.session_state.get("analytics_module_start")
    if inicio is None:
        return 0
    return int((time.time() - inicio) * 1000)


def get_session():
    if "analytics_session" not in st.session_state:
        st.session_state.analytics_session = uuid.uuid4().hex
    return st.session_state.analytics_session


def get_operation():
    if "analytics_operation" not in st.session_state:
        st.session_state.analytics_operation = uuid.uuid4().hex
    return st.session_state.analytics_operation


def new_operation():
    st.session_state.analytics_operation = uuid.uuid4().hex
    return st.session_state.analytics_operation
