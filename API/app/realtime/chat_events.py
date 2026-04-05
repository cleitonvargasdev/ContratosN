import asyncio

from fastapi import WebSocket


class ChatEventBroker:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        became_online = False
        await websocket.accept()
        async with self._lock:
            connections = self._connections.setdefault(user_id, set())
            became_online = not connections
            connections.add(websocket)

        if became_online:
            await self.broadcast({"resource": "chat", "event": "presence", "user_id": user_id, "online": True})

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        became_offline = False
        async with self._lock:
            connections = self._connections.get(user_id)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                self._connections.pop(user_id, None)
                became_offline = True

        if became_offline:
            await self.broadcast({"resource": "chat", "event": "presence", "user_id": user_id, "online": False})

    def is_user_online(self, user_id: int) -> bool:
        return bool(self._connections.get(user_id))

    async def broadcast(self, payload: dict[str, object]) -> None:
        async with self._lock:
            connections = [connection for user_connections in self._connections.values() for connection in user_connections]

        stale_connections: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception:
                stale_connections.append(connection)

        if stale_connections:
            async with self._lock:
                for user_id, user_connections in list(self._connections.items()):
                    for connection in stale_connections:
                        user_connections.discard(connection)
                    if not user_connections:
                        self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict[str, object]) -> bool:
        async with self._lock:
            connections = list(self._connections.get(user_id, set()))

        delivered = False

        stale_connections: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(payload)
                delivered = True
            except Exception:
                stale_connections.append(connection)

        if stale_connections:
            async with self._lock:
                active_connections = self._connections.get(user_id, set())
                for connection in stale_connections:
                    active_connections.discard(connection)
                if not active_connections:
                    self._connections.pop(user_id, None)

        return delivered


chat_event_broker = ChatEventBroker()