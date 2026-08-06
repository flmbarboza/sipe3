import streamlit as st
import time
from threading import Lock
from . import config
from . import sheets


class Buffer:
    """
    Buffer inteligente de eventos com:
    - Acumulação em memória (session_state)
    - Flush automático ao atingir BUFFER_SIZE
    - Rate limiting para respeitar quotas da API Google Sheets
    - Fallback: se falhar, mantém em session_state para retry na próxima interação
    """

    def __init__(self):
        self.lock = Lock()
        self.max_size = config.BUFFER_SIZE

    def _ensure_state(self):
        if "analytics_buffer" not in st.session_state:
            st.session_state.analytics_buffer = []
        if "analytics_last_flush" not in st.session_state:
            st.session_state.analytics_last_flush = 0
        if "analytics_backup_events" not in st.session_state:
            st.session_state.analytics_backup_events = []

    def add(self, event):
        with self.lock:
            self._ensure_state()
            st.session_state.analytics_buffer.append(event)

            total = len(st.session_state.analytics_buffer) + len(st.session_state.analytics_backup_events)
            if total >= self.max_size:
                self.flush()

    def flush(self):
        """Tenta enviar todos os eventos pendentes para o Google Sheets."""
        self._ensure_state()

        # Consolida buffer + backup
        events = st.session_state.analytics_buffer + st.session_state.analytics_backup_events
        st.session_state.analytics_buffer = []
        st.session_state.analytics_backup_events = []

        if not events:
            return

        # Rate limiting: respeita o intervalo mínimo entre requisições
        now = time.time()
        if now - st.session_state.analytics_last_flush < config.RATE_LIMIT_SECONDS:
            # Ainda não pode enviar, volta para backup
            st.session_state.analytics_backup_events = events
            return

        # Tenta enviar
        try:
            sheets.save_many(events)
            st.session_state.analytics_last_flush = time.time()
        except Exception:
            # Falhou (API indisponível, quota excedida, etc.)
            # Volta para backup para tentar na próxima interação do usuário
            st.session_state.analytics_backup_events = events


buffer = Buffer()
