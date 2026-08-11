"""
Autenticação: hash de senha com bcrypt e emissão/validação de token JWT.

Substitui o hash provisório (sha256 puro) usado nas Fases 1-4. Bcrypt é
o padrão recomendado para senha porque é deliberadamente lento (dificulta
força bruta) e já cuida do salt automaticamente — sha256 puro não faz
nenhuma das duas coisas.
"""
import datetime

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

ALGORITHM = "HS256"
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return _pwd_context.hash(senha)


def verificar_senha(senha_em_texto: str, senha_hash: str) -> bool:
    return _pwd_context.verify(senha_em_texto, senha_hash)


def criar_token_acesso(professor_id: int, email: str) -> str:
    expira_em = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(professor_id), "email": email, "exp": expira_em}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Lança jose.JWTError se o token for inválido, malformado ou expirado."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


__all__ = ["hash_senha", "verificar_senha", "criar_token_acesso", "decodificar_token", "JWTError"]
