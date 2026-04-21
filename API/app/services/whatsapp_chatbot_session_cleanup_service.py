import logging
from datetime import UTC, datetime, timedelta

from app.repositories.whatsapp_chatbot_repository import WhatsAppChatbotRepository


CHATBOT_SESSION_TIMEOUT = timedelta(minutes=10)
logger = logging.getLogger(__name__)


class WhatsAppChatbotSessionCleanupService:
    def __init__(self, session) -> None:
        self.repository = WhatsAppChatbotRepository(session)

    async def close_inactive_sessions(self) -> int:
        cutoff = datetime.now(UTC) - CHATBOT_SESSION_TIMEOUT
        closed_count = await self.repository.close_inactive_sessions(cutoff)
        if closed_count:
            logger.info("Sessoes inativas do chatbot encerradas automaticamente. total=%s", closed_count)
        return closed_count