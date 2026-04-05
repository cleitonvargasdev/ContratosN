import asyncio

from sqlalchemy import select, func

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.access_control import Profile
from app.models.user import User


TEST_USERS = [
    {"nome": "Ana Souza", "login": "ana.souza", "email": "ana.souza@example.com", "funcao": "Administrador", "telefone": "11990000001", "ativo": True},
    {"nome": "Bruno Lima", "login": "bruno.lima", "email": "bruno.lima@example.com", "funcao": "Operador", "telefone": "11990000002", "ativo": True},
    {"nome": "Carla Mendes", "login": "carla.mendes", "email": "carla.mendes@example.com", "funcao": "Operador", "telefone": "11990000003", "ativo": True},
    {"nome": "Daniel Rocha", "login": "daniel.rocha", "email": "daniel.rocha@example.com", "funcao": "Operador", "telefone": "11990000004", "ativo": True},
    {"nome": "Elaine Martins", "login": "elaine.martins", "email": "elaine.martins@example.com", "funcao": "Operador", "telefone": "11990000005", "ativo": True},
    {"nome": "Fabio Castro", "login": "fabio.castro", "email": "fabio.castro@example.com", "funcao": "Operador", "telefone": "11990000006", "ativo": True},
    {"nome": "Gabriela Alves", "login": "gabriela.alves", "email": "gabriela.alves@example.com", "funcao": "Operador", "telefone": "11990000007", "ativo": True},
    {"nome": "Henrique Dias", "login": "henrique.dias", "email": "henrique.dias@example.com", "funcao": "Operador", "telefone": "11990000008", "ativo": False},
    {"nome": "Isabela Nunes", "login": "isabela.nunes", "email": "isabela.nunes@example.com", "funcao": "Operador", "telefone": "11990000009", "ativo": True},
    {"nome": "Joao Pereira", "login": "joao.pereira", "email": "joao.pereira@example.com", "funcao": "Operador", "telefone": "11990000010", "ativo": True},
]

DEFAULT_PASSWORD = "123456"


async def main() -> None:
    async with AsyncSessionLocal() as session:
        profile_result = await session.execute(select(Profile.id, Profile.nome))
        profile_ids = {nome: profile_id for profile_id, nome in profile_result.all()}

        count_stmt = select(func.count()).select_from(User)
        existing = await session.scalar(count_stmt)
        if existing and existing >= len(TEST_USERS):
            print("Users already seeded.")
            return

        result = await session.execute(select(User.email))
        existing_emails = set(result.scalars().all())

        users = [
            User(
                **payload,
                perfil_id=profile_ids.get("Administrador") if payload["funcao"] == "Administrador" else profile_ids.get("Operacional"),
                senha_hash=hash_password(DEFAULT_PASSWORD),
            )
            for payload in TEST_USERS
            if payload["email"] not in existing_emails
        ]
        if not users:
            print("No new users to insert.")
            return

        session.add_all(users)
        await session.commit()
        print(f"Inserted {len(users)} users.")


if __name__ == "__main__":
    asyncio.run(main())
