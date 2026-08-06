from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Module:
    HOME = "home"
    CANVAS = "canvas"
    PESTEL = "pestel"
    PORTER = "porter"
    SWOT = "swot"
    PLANEJAMENTO = "planejamento"
    FINANCEIRO = "financeiro"
    PLANO_ACAO = "5w2h"
    PLANO_FUNCAO = "planos_funcao"
    MONITORAMENTO = "monitoramento"
    REVIEW = "review"
    PAINEL = "painel"
    RELATORIO = "relatorio"


@dataclass
class Event:
    timestamp: str
    event_id: str
    session_id: str
    user_id: str           # ← identificador único do usuário/máquina
    operation_id: str
    page: str
    module: str
    event: str
    action: str = ""
    duration_ms: int = 0
    company_name: str = ""
    company_sector: str = ""
    completion_pct: float = 0.0
    ai_used: bool = False
    metadata: dict = field(default_factory=dict)


def now():
    return datetime.utcnow().isoformat()


def new_uuid():
    return uuid.uuid4().hex
