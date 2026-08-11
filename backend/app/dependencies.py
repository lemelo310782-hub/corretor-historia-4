"""
Dependência de autenticação compartilhada por todos os routers protegidos.

Uso em qualquer rota:

    @router.get("/algo")
    def minha_rota(professor_atual: models.Professor = Depends(get_professor_atual)):
        ...

O FastAPI injeta automaticamente o professor já validado (ou devolve 401
antes mesmo de a função da rota rodar, se o token for inválido/ausente).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services.auth import decodificar_token, JWTError

# tokenUrl é só o endereço que o Swagger (/docs) usa para o botão "Authorize" —
# não afeta a validação em si, que é feita por decodificar_token abaixo.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_professor_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Professor:
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou sessão expirada. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decodificar_token(token)
        professor_id = payload.get("sub")
        if professor_id is None:
            raise erro_credenciais
    except JWTError:
        raise erro_credenciais

    professor = db.query(models.Professor).get(int(professor_id))
    if professor is None:
        raise erro_credenciais
    return professor
