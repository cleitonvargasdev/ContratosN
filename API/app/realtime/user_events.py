import asyncio
from collections.abc import Iterable

from fastapi import WebSocket


class UserEventBroker:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(
        self,
        event: str,
        *,
        user_id: int | None = None,
        changed_fields: Iterable[str] | None = None,
    ) -> None:
        payload: dict[str, object] = {"resource": "usuarios", "event": event}
        if user_id is not None:
            payload["user_id"] = user_id

        changed_fields_list = list(changed_fields or [])
        if changed_fields_list:
            payload["changed_fields"] = changed_fields_list

        async with self._lock:
            connections = list(self._connections)

        stale_connections: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception:
                stale_connections.append(connection)

        if stale_connections:
            async with self._lock:
                for connection in stale_connections:
                    self._connections.discard(connection)


user_event_broker = UserEventBroker()