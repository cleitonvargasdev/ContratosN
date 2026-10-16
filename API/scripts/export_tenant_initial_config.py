"""Explicitly export allowlisted current defaults; never export business records."""
import asyncio
import json
from pathlib import Path

from app.tenancy.initial_config import ConfigData
from app.tenancy.provisioning import encode_payload, read_template


async def export_config():
    source = await read_template()
    for field in ("usuario_api_whatsapp", "msg_renovacao", "msg_negociacao", "msg_campanha"):
        source["parameters"][field] = source["parameters"].get(field) or ""
    snapshot = ConfigData.model_validate(source).snapshot()
    target = Path(__file__).resolve().parents[1] / "app/tenancy/initial_config.json"
    target.write_text(json.dumps({"format": 1, "payload": encode_payload(snapshot)}, indent=2) + "\n", encoding="utf-8")
    print(f"Configuração exportada: {len(snapshot['profiles'])} perfis e {len(snapshot['apis'])} APIs. Conteúdo criptografado.")


if __name__ == "__main__":
    try:
        asyncio.run(export_config())
    except Exception as exc:
        raise SystemExit(f"Exportação interrompida ({type(exc).__name__}); confira conexão, chave e dados do modelo.") from None
