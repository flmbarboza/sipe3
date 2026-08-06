from .tracker import (
    track,
    init_page,
    module_started,
    module_completed,
    begin_observation,
    end_observation,
    track_ai_request,
    track_ai_response,
    track_ai_error,
    track_data_import,
    track_data_clear,
    track_data_export,
    track_navigation,
    track_chat_message,
    track_error,
)

from .models import Module, Event
from .session import get_session, get_operation, get_user_id, new_operation
from .config import EventType

# Compatibilidade com páginas antigas
def init_session():
    return get_session()


def update_activity():
    return None


def check_timeout():
    return False


__all__ = [
    "track",
    "init_page",
    "module_started",
    "module_completed",
    "begin_observation",
    "end_observation",
    "Module",
    "Event",
    "EventType",
    "get_session",
    "get_operation",
    "get_user_id",
    "new_operation",
    "init_session",
    "update_activity",
    "check_timeout",
    "track_ai_request",
    "track_ai_response",
    "track_ai_error",
    "track_data_import",
    "track_data_clear",
    "track_data_export",
    "track_navigation",
    "track_chat_message",
    "track_error",
]
