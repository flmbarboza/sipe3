import json
import os


ARQUIVO = "data/projeto.json"


def salvar_json(dados):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            dados,
            f,
            ensure_ascii=False,
            indent=4
        )


def carregar_json():

    if not os.path.exists(ARQUIVO):
        return None

    with open(
        ARQUIVO,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)
