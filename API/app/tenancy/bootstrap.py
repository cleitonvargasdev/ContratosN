"""Initialize a NEW tenant database from an allowlisted configuration snapshot."""
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.orm import Session

from app.core.access_control_catalog import RESOURCE_CATALOG
from app.core.security import hash_password, verify_password
from app.models.access_control import Profile, ProfilePermission
from app.models.api_config import ApiConfig
from app.models.parameter import Parametro
from app.models.user import User


def seed_database(url, job_id, domain, snapshot):
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE IF NOT EXISTS tenant_bootstrap_marker (job_id varchar(32) PRIMARY KEY)"))
        with Session(engine) as session, session.begin():
            marker = session.scalar(text("SELECT job_id FROM tenant_bootstrap_marker"))
            if marker:
                if marker != job_id:
                    raise ValueError("Banco pertence a outra criação")
                return
            if session.scalar(select(func.count()).select_from(User)):
                raise ValueError("Banco não está vazio; inicialização recusada")
            # Migrations provide built-in profiles; merge template profiles without source IDs.
            for definition in snapshot["profiles"]:
                profile = session.scalar(select(Profile).where(Profile.nome == definition["nome"]))
                if profile is None:
                    profile = Profile(nome=definition["nome"])
                    session.add(profile)
                    session.flush()
                profile.descricao, profile.ativo = definition["descricao"], definition["ativo"]
                session.execute(delete(ProfilePermission).where(ProfilePermission.perfil_id == profile.id))
                session.add_all(ProfilePermission(perfil_id=profile.id, **p) for p in definition["permissions"])
            admin_profile = session.scalar(select(Profile).where(Profile.nome == "Administrador"))
            if admin_profile is None:
                admin_profile = Profile(nome="Administrador", descricao="Administração completa")
                session.add(admin_profile)
                session.flush()
            admin_profile.ativo = True
            session.execute(delete(ProfilePermission).where(ProfilePermission.perfil_id == admin_profile.id))
            session.add_all(ProfilePermission(perfil_id=admin_profile.id, resource_key=r.resource_key,
                resource_label=r.resource_label, **{f"can_{action}": action in r.supported_actions
                    for action in ("read", "create", "update", "delete")}) for r in RESOURCE_CATALOG)
            admin = User(nome="Administrador", login="Admin", email=f"admin@{domain}", funcao="Administrador",
                         ativo=True, senha_hash=hash_password("Admin"))
            admin.profiles.append(admin_profile)
            session.add(admin)
            session.flush()
            # Existing fresh-install parameter defaults may be replaced, never business data.
            if session.scalar(select(func.count()).select_from(Parametro)):
                raise ValueError("Parâmetros já existem em banco não inicializado por este processo")
            session.add(Parametro(**snapshot["parameters"], score_atualizacao_automatica=False, score_agendamentos=[],
                whatsapp_cobranca_automatica=False, whatsapp_agendamentos=[], emitir_sons=True,
                ligar_websocket=False, silenciar_mensagem=False))
            for api in snapshot["apis"]:
                session.add(ApiConfig(**api, usuario_id=admin.id))
            session.execute(text("INSERT INTO tenant_bootstrap_marker (job_id) VALUES (:id)"), {"id": job_id})
        with Session(engine) as session:
            admin = session.scalar(select(User).where(User.login == "Admin"))
            if not admin or not verify_password("Admin", admin.senha_hash) or not any(
                p.resource_key == "acesso_web" and p.can_read for p in admin.permissions
            ):
                raise ValueError("Administrador inicial não possui acesso web")
    finally:
        engine.dispose()
