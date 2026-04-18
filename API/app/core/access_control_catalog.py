from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.schemas.access_control import PermissionResourceRead


RESOURCE_CATALOG: tuple[PermissionResourceRead, ...] = (
    PermissionResourceRead(resource_key="acesso_web", resource_label="Acesso Web", resource_group="Sistema", supported_actions=["read"]),
    PermissionResourceRead(resource_key="dashboard", resource_label="Dashboard", resource_group="Sistema", supported_actions=["read"]),
    PermissionResourceRead(resource_key="usuarios", resource_label="Usuarios", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="clientes", resource_label="Clientes", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="solicitacoes", resource_label="Solicitacoes", resource_group="Cadastros", supported_actions=["read", "update"]),
    PermissionResourceRead(resource_key="contratos", resource_label="Contratos", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="apis", resource_label="APIs", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="usuarios_api_keys", resource_label="Chaves de API dos usuarios", resource_group="Seguranca", supported_actions=["read", "update"]),
    PermissionResourceRead(resource_key="perfis", resource_label="Perfis e permissoes", resource_group="Seguranca", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="planos_pagamentos", resource_label="Planos de Pagamento", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_ufs", resource_label="UFs", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_cidades", resource_label="Cidades", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_bairros", resource_label="Bairros", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_feriados", resource_label="Feriados", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
)


def merge_catalog_permissions(permissions: Iterable[object]) -> list[dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}

    for permission in permissions:
        resource_key = str(getattr(permission, "resource_key", "")).strip().lower()
        if not resource_key:
            continue

        current = indexed.get(resource_key)
        item = {
            "id": getattr(permission, "id", None),
            "resource_key": resource_key,
            "resource_label": getattr(permission, "resource_label", None),
            "can_read": bool(getattr(permission, "can_read", False)),
            "can_create": bool(getattr(permission, "can_create", False)),
            "can_update": bool(getattr(permission, "can_update", False)),
            "can_delete": bool(getattr(permission, "can_delete", False)),
        }
        if current is None:
            indexed[resource_key] = item
            continue

        current["resource_label"] = current["resource_label"] or item["resource_label"]
        current["can_read"] = current["can_read"] or item["can_read"]
        current["can_create"] = current["can_create"] or item["can_create"]
        current["can_update"] = current["can_update"] or item["can_update"]
        current["can_delete"] = current["can_delete"] or item["can_delete"]

    merged: list[dict[str, Any]] = []
    for resource in RESOURCE_CATALOG:
        existing = indexed.pop(resource.resource_key, None)
        inherited = _build_inherited_permission(resource.resource_key, indexed)
        merged.append(
            {
                "id": None if existing is None else existing["id"],
                "resource_key": resource.resource_key,
                "resource_label": (None if existing is None else existing["resource_label"]) or resource.resource_label,
                "can_read": inherited["can_read"] if existing is None else existing["can_read"],
                "can_create": inherited["can_create"] if existing is None else existing["can_create"],
                "can_update": inherited["can_update"] if existing is None else existing["can_update"],
                "can_delete": inherited["can_delete"] if existing is None else existing["can_delete"],
            }
        )

    for resource_key in sorted(indexed):
        merged.append(indexed[resource_key])

    return merged


def _build_inherited_permission(resource_key: str, indexed: dict[str, dict[str, Any]]) -> dict[str, bool]:
    if resource_key != "solicitacoes":
        return {
            "can_read": False,
            "can_create": False,
            "can_update": False,
            "can_delete": False,
        }

    contracts_permission = indexed.get("contratos")
    if contracts_permission is None:
        return {
            "can_read": False,
            "can_create": False,
            "can_update": False,
            "can_delete": False,
        }

    return {
        "can_read": bool(contracts_permission["can_read"]),
        "can_create": False,
        "can_update": bool(contracts_permission["can_update"]),
        "can_delete": False,
    }