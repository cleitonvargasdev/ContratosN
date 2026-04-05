from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


user_profiles_table = Table(
    "usuarios_perfis",
    Base.metadata,
    Column("user_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("perfil_id", ForeignKey("perfis.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class Profile(Base):
    __tablename__ = "perfis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    permissions: Mapped[list[ProfilePermission]] = relationship(
        "ProfilePermission",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    users: Mapped[list[User]] = relationship("User", secondary=user_profiles_table, back_populates="profiles", lazy="selectin")


class ProfilePermission(Base):
    __tablename__ = "perfil_permissoes"
    __table_args__ = (UniqueConstraint("perfil_id", "resource_key", name="uq_perfil_permissoes_recurso"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfis.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    can_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_update: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profile: Mapped[Profile] = relationship("Profile", back_populates="permissions")


class UserApiKey(Base):
    __tablename__ = "usuarios_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="api_key")
