from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Change:
    event: str
    item_id: str
    before: dict | None = None
    after: dict | None = None
    changed_fields: list[str] = field(default_factory=list)


class Observer:
    """
    Compara duas listas de objetos e identifica:
        - item_added
        - item_removed
        - item_updated
    """

    def observe(
        self,
        before: list[dict],
        after: list[dict],
        *,
        key: str = "id",
        watched_fields: list[str] | None = None,
    ) -> list[Change]:

        watched_fields = watched_fields or ["texto"]

        before = deepcopy(before)
        after = deepcopy(after)

        before_map = {
            item[key]: item
            for item in before
        }

        after_map = {
            item[key]: item
            for item in after
        }

        changes: list[Change] = []

        # --------------------------
        # Novos itens
        # --------------------------

        for item_id, item in after_map.items():

            if item_id not in before_map:

                changes.append(
                    Change(
                        event="item_added",
                        item_id=item_id,
                        after=item
                    )
                )

        # --------------------------
        # Itens removidos
        # --------------------------

        for item_id, item in before_map.items():

            if item_id not in after_map:

                changes.append(
                    Change(
                        event="item_removed",
                        item_id=item_id,
                        before=item
                    )
                )

        # --------------------------
        # Itens alterados
        # --------------------------

        for item_id in before_map.keys():

            if item_id not in after_map:
                continue

            before_item = before_map[item_id]
            after_item = after_map[item_id]

            modified_fields = []

            for field in watched_fields:

                if before_item.get(field) != after_item.get(field):
                    modified_fields.append(field)

            if modified_fields:

                changes.append(
                    Change(
                        event="item_updated",
                        item_id=item_id,
                        before=before_item,
                        after=after_item,
                        changed_fields=modified_fields
                    )
                )

        return changes


observer = Observer()
