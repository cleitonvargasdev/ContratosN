from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApiConfig(Base):
    __tablename__ = "apis"

    api_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    nome_api: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    funcionalidade: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key1: Mapped[str | None] = mapped_column(String(100), nullable=True)
    value1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key2: Mapped[str | None] = mapped_column(String(100), nullable=True)
    value2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key3: Mapped[str | None] = mapped_column(String(100), nullable=True)
    value3: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key4: Mapped[str | None] = mapped_column(String(100), nullable=True)
    value4: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key5: Mapped[str | None] = mapped_column(String(100), nullable=True)
    value5: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)