from inspect import stack
from utils.data_manager import get_data
from .buffer import buffer
from .models import Event, now, new_uuid
from .session import get_session, get_operation, get_user_id, module_duration, module_enter
from .observer import observer
from . import config
from copy import deepcopy
import time
import streamlit as st


_last_event_time = None


def _page_name():
    """Extrai o nome do arquivo da página chamadora."""
    try:
        frame = stack()[2]
        return frame.filename.split("/")[-1]
    except Exception:
        return ""


def _ensure_state_cache():
    """Garante que o cache de estado use session_state (thread-safe por usuário)."""
    if "analytics_state_cache" not in st.session_state:
        st.session_state.analytics_state_cache = {}
    return st.session_state.analytics_state_cache


def track(
    event,
    module,
    action="",
    metadata=None,
    completion_pct=0.0,
    ai_used=False
):
    """
    Registra um evento no analytics.
    Compatível com a API anterior — todas as páginas continuam funcionando.
    """
    global _last_event_time

    agora = time.time()
    if _last_event_time is None:
        duration = 0
    else:
        duration = int((agora - _last_event_time) * 1000)
    _last_event_time = agora

    if metadata is None:
        metadata = {}

    data = get_data()
    empresa = data.get("empresa", {})

    e = Event(
        timestamp=now(),
        event_id=new_uuid(),
        session_id=get_session(),
        user_id=get_user_id(),
        operation_id=get_operation(),
        page=_page_name(),
        module=module,
        event=event,
        action=action,
        duration_ms=duration,
        company_name=empresa.get("nome", ""),
        company_sector=empresa.get("setor", ""),
        completion_pct=completion_pct,
        ai_used=ai_used,
        metadata=metadata
    )

    buffer.add(e)


# ── Tracking especializado ──────────────────────────────

def track_ai_request(module, metadata=None):
    """Track quando usuário solicita geração de IA."""
    track(config.EventType.AI_REQUEST, module, ai_used=True, metadata=metadata or {})


def track_ai_response(module, success=True, items_count=0, metadata=None):
    """Track quando IA responde com sucesso ou falha."""
    meta = metadata or {}
    meta["success"] = success
    meta["items_count"] = items_count
    track(config.EventType.AI_RESPONSE, module, ai_used=True, metadata=meta)


def track_ai_error(module, error_msg, metadata=None):
    """Track erro na chamada de IA."""
    meta = metadata or {}
    meta["error"] = str(error_msg)[:200]
    track(config.EventType.AI_ERROR, module, ai_used=True, metadata=meta)


def track_data_import(module, source_module, items_count=0, metadata=None):
    """Track importação de dados de outro módulo (ex: PESTEL → SWOT)."""
    meta = metadata or {}
    meta["source"] = source_module
    meta["items_count"] = items_count
    track(config.EventType.DATA_IMPORTED, module, metadata=meta)


def track_data_clear(module, target, items_count=0, metadata=None):
    """Track limpeza/deleção de dados de uma seção."""
    meta = metadata or {}
    meta["target"] = target
    meta["items_count"] = items_count
    track(config.EventType.DATA_CLEARED, module, metadata=meta)


def track_data_export(module, format_type, metadata=None):
    """Track exportação de dados (JSON, CSV, HTML, PDF, Markdown)."""
    meta = metadata or {}
    meta["format"] = format_type
    track(config.EventType.DATA_EXPORTED, module, metadata=meta)


def track_navigation(from_module, to_page, metadata=None):
    """Track clique em botão de navegação entre páginas."""
    meta = metadata or {}
    meta["to_page"] = to_page
    track(config.EventType.NAVIGATION, from_module, metadata=meta)


def track_chat_message(module, metadata=None):
    """Track mensagem enviada no chat do assistente IA."""
    track(config.EventType.CHAT_MESSAGE, module, metadata=metadata or {})


def track_error(module, error_type, error_msg, metadata=None):
    """Track erro genérico da aplicação."""
    meta = metadata or {}
    meta["error_type"] = error_type
    meta["message"] = str(error_msg)[:200]
    track(config.EventType.ERROR, module, metadata=meta)


# ── Observação de estado (CRUD automático) ──────────────

def begin_observation(key: str, items: list[dict]):
    """
    Salva uma cópia do estado atual de uma coleção.
    Chame no início do formulário/editor.
    """
    cache = _ensure_state_cache()
    cache[key] = deepcopy(items)


def end_observation(key: str, items: list[dict], module: str):
    """
    Compara o estado anterior com o atual e registra eventos de mudança
    (item_added, item_removed, item_updated).
    """
    cache = _ensure_state_cache()
    before = cache.get(key)

    if before is None:
        cache[key] = deepcopy(items)
        return

    changes = observer.observe(before=before, after=items)

    for change in changes:
        track(
            event=change.event,
            module=module,
            metadata={
                "item_id": change.item_id,
                "fields": ",".join(change.changed_fields),
                "before": change.before,
                "after": change.after
            }
        )

    cache[key] = deepcopy(items)


# ── Controle de páginas e módulos ───────────────────────

def init_page(module=None):
    """
    Inicialização da página.
    Registra entrada na página e saída da página anterior (com duração).
    """
    page = _page_name()

    # Se estava em outra página, registra saída com duração
    prev_page = st.session_state.get("analytics_current_page")
    if prev_page and prev_page != page:
        start_key = f"analytics_page_start_{prev_page}"
        start_time = st.session_state.get(start_key)
        if start_time:
            duration = int((time.time() - start_time) * 1000)
            track(
                event=config.EventType.PAGE_EXIT,
                module=st.session_state.get("analytics_current_module", ""),
                action=prev_page,
                metadata={"duration_ms": duration, "next_page": page}
            )

    # Registra entrada na nova página
    st.session_state.analytics_current_page = page
    st.session_state.analytics_current_module = module or ""
    st.session_state[f"analytics_page_start_{page}"] = time.time()

    if module:
        module_enter(module)

    track(
        event=config.EventType.PAGE_VIEW,
        module=module or "",
        action=page
    )


def module_started(module):
    """Registra o início de um módulo/análise."""
    module_enter(module)
    track(
        event=config.EventType.MODULE_STARTED,
        module=module
    )


def module_completed(module, metadata=None):
    """
    Registra a conclusão de um módulo.
    Inclui duração e metadados opcionais.
    """
    if metadata is None:
        metadata = {}

    duration = module_duration()
    metadata["duration_ms"] = duration

    track(
        event=config.EventType.MODULE_COMPLETED,
        module=module,
        metadata=metadata
    )
