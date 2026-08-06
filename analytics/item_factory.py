from datetime import datetime
import uuid


def new_user_item(texto=""):
    agora = datetime.utcnow().isoformat()
    return {
        "id": uuid.uuid4().hex,
        "texto": texto,
        "created_by": "user",
        "created_at": agora,
        "updated_at": agora,
        "edited": False,
        "deleted": False,
        "ai_model": "",
        "prompt_version": ""
    }


def new_ai_item(texto, model, prompt_version):
    agora = datetime.utcnow().isoformat()
    return {
        "id": uuid.uuid4().hex,
        "texto": texto,
        "created_by": "ai",
        "created_at": agora,
        "updated_at": agora,
        "edited": False,
        "deleted": False,
        "ai_model": model,
        "prompt_version": prompt_version
    }
