"""DEPRECATED: Este arquivo foi unificado no pacote `analytics/`.
Mantenha importações de `analytics` diretamente. As classes aqui são
wrappers de compatibilidade que redirecionam para o novo sistema.
"""

import warnings
from analytics import track, EventType

warnings.warn(
    "utils.analytics está deprecado. Importe de 'analytics' diretamente.",
    DeprecationWarning,
    stacklevel=2
)


class UXMonitor:
    """
    Wrapper de compatibilidade para a página 7 (Planos por Função).
    Redireciona todas as chamadas para o novo tracker unificado.
    """

    def __init__(self):
        pass

    def track_event(self, event_type, page, metadata=None, deduplicate=True):
        """Redireciona para track()."""
        track(event_type, page, metadata=metadata or {})

    def track_page_time(self, page):
        """Não utilizado no novo sistema (tempo é trackado automaticamente)."""
        pass

    def track_error(self, page, error_type, error_msg):
        """Redireciona para track_error()."""
        track(EventType.ERROR, page, metadata={
            "error_type": error_type,
            "message": str(error_msg)[:100]
        })

    def track_ai_generation(self, page, field, items_count):
        """Redireciona para track_ai_response()."""
        track(EventType.AI_RESPONSE, page, metadata={
            "field": field,
            "items_generated": items_count
        })

    def track_interaction(self, page, action_type, field=None):
        """Redireciona para track genérico."""
        track(EventType.ITEM_UPDATED, page, metadata={
            "action": action_type,
            "field": field
        })

    def get_insights(self):
        return "Use o pacote analytics diretamente."
