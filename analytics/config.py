"""Configurações centralizadas do analytics SIPE."""

# ── Google Sheets ─────────────────────────────────────────
GOOGLE_SHEET = "SIPE10 Analytics"
WORKSHEET = "events"

# ── Buffer & Rate Limiting ───────────────────────────────
BUFFER_SIZE = 20              # Eventos acumulados antes de tentar flush
RATE_LIMIT_SECONDS = 5        # Mínimo entre requisições ao Google Sheets
MAX_RETRIES = 3               # Tentativas de reenvio (lógica de backoff)
RETRY_BACKOFF_BASE = 2        # Base para cálculo de espera entre retries

# ── Event Types padronizados ─────────────────────────────
class EventType:
    # Navegação
    PAGE_VIEW = "page_view"
    PAGE_EXIT = "page_exit"
    NAVIGATION = "navigation"

    # Módulos
    MODULE_STARTED = "module_started"
    MODULE_COMPLETED = "module_completed"

    # Dados / CRUD
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    ITEM_UPDATED = "item_updated"
    DATA_IMPORTED = "data_imported"
    DATA_CLEARED = "data_cleared"
    DATA_EXPORTED = "data_exported"

    # IA
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"

    # Chat
    CHAT_MESSAGE = "chat_message"

    # Sessão
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # Erros
    ERROR = "error"
