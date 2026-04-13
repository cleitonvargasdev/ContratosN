from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClientScoreLog(Base):
    __tablename__ = "client_score_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.clientes_id", ondelete="CASCADE"), nullable=False, index=True)
    data_hora_evento: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    evento: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    pontuacao_anterior: Mapped[int] = mapped_column(Integer, nullable=False)
    variacao_pontos: Mapped[int] = mapped_column(Integer, nullable=False)
    pontuacao_atual: Mapped[int] = mapped_column(Integer, nullable=False)
    regra_pontos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantidade_referencia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalhe_calculo: Mapped[str | None] = mapped_column(String(200), nullable=True)
