from datetime import date, datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.access_control import Profile, UserApiKey


@dataclass(slots=True)
class EffectiveProfilePermission:
    resource_key: str
    resource_label: str | None
    can_read: bool = False
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
    id: int | None = None


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    login: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    funcao: Mapped[str] = mapped_column(String(40), default="Operador", nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(20), nullable=True)
    flag_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cep: Mapped[str | None] = mapped_column(String(8), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numero: Mapped[str | None] = mapped_column(String(20), nullable=True)
    complemento: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bairro_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bairros.bairro_id", ondelete="SET NULL"), nullable=True)
    cidade_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cidades.cidade_id", ondelete="SET NULL"), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), ForeignKey("uf.uf", ondelete="SET NULL"), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date(), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profiles: Mapped[list["Profile"]] = relationship(
        "Profile",
        secondary="usuarios_perfis",
        back_populates="users",
        lazy="selectin",
        order_by="Profile.nome",
    )
    api_key: Mapped["UserApiKey | None"] = relationship(
        "UserApiKey",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def profile(self) -> "Profile | None":
        return self.profiles[0] if self.profiles else None

    @property
    def perfil_nome(self) -> str | None:
        return self.perfil_nomes[0] if self.perfil_nomes else None

    @property
    def perfil_id(self) -> int | None:
        return self.perfil_ids[0] if self.perfil_ids else None

    @property
    def perfil_nomes(self) -> list[str]:
        return [profile.nome for profile in self.profiles]

    @property
    def perfil_ids(self) -> list[int]:
        return [profile.id for profile in self.profiles]

    @property
    def permissions(self) -> list[EffectiveProfilePermission]:
        aggregated: dict[str, EffectiveProfilePermission] = {}

        for profile in self.profiles:
            if not profile.ativo:
                continue

            for permission in profile.permissions:
                current = aggregated.get(permission.resource_key)
                if current is None:
                    aggregated[permission.resource_key] = EffectiveProfilePermission(
                        id=permission.id,
                        resource_key=permission.resource_key,
                        resource_label=permission.resource_label,
                        can_read=permission.can_read,
                        can_create=permission.can_create,
                        can_update=permission.can_update,
                        can_delete=permission.can_delete,
                    )
                    continue

                current.resource_label = current.resource_label or permission.resource_label
                current.can_read = current.can_read or permission.can_read
                current.can_create = current.can_create or permission.can_create
                current.can_update = current.can_update or permission.can_update
                current.can_delete = current.can_delete or permission.can_delete

        return [aggregated[key] for key in sorted(aggregated)]

    @property
    def api_key_info(self) -> "UserApiKey | None":
        return self.api_key
