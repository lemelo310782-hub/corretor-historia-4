"""
Rotas de autenticação: cadastro de professor e login.

O login segue o padrão OAuth2PasswordRequestForm do FastAPI (campos
`username`/`password`, em x-www-form-urlencoded) — isso é o que permite
usar o botão "Authorize" do Swagger (/docs) diretamente, sem precisar de
nenhuma ferramenta externa para testar. No formulário, `username` é o
e-mail do professor.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_professor_atual
from app.services.auth import hash_senha, verificar_senha, criar_token_acesso

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/registrar", response_model=schemas.ProfessorOut)
def registrar_professor(payload: schemas.ProfessorCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Professor).filter_by(email=payload.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um professor cadastrado com este e-mail.")

    professor = models.Professor(
        nome=payload.nome,
        email=payload.email,
        escola=payload.escola,
        senha_hash=hash_senha(payload.senha),
    )
    db.add(professor)
    db.commit()
    db.refresh(professor)
    return professor


@router.post("/login", response_model=schemas.TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    professor = db.query(models.Professor).filter_by(email=form.username).first()
    if not professor or not verificar_senha(form.password, professor.senha_hash):
        # Mensagem genérica de propósito: não revela se o e-mail existe ou não.
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    token = criar_token_acesso(professor.id, professor.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/eu", response_model=schemas.ProfessorOut)
def meus_dados(professor_atual: models.Professor = Depends(get_professor_atual)):
    """Endpoint simples para o frontend confirmar quem está logado (e validar o token salvo)."""
    return professor_atual
