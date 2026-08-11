"""
Rotas de gestão acadêmica: turmas e alunos do professor autenticado.

O cadastro de professor foi para app/routers/auth.py (POST /auth/registrar),
já que "criar minha própria conta" é conceitualmente autenticação, não
gestão de turma.

Todas as rotas aqui exigem um token válido (via Depends(get_professor_atual))
e nunca aceitam professor_id vindo da URL/corpo da requisição — o professor
é sempre o dono do token, o que evita que alguém tente forjar acesso a
turmas de outro professor só trocando um ID na URL.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_professor_atual

router = APIRouter(tags=["Turmas e Alunos"])


def _turma_do_professor_ou_404(turma_id: int, professor_atual: models.Professor, db: Session) -> models.Turma:
    turma = db.query(models.Turma).get(turma_id)
    if not turma or turma.professor_id != professor_atual.id:
        # 404 (não 403) de propósito: não revela se a turma existe e é de outra pessoa.
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma


# --- Turmas ---
@router.post("/turmas", response_model=schemas.TurmaOut)
def criar_turma(
    payload: schemas.TurmaCreate,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    turma = models.Turma(nome=payload.nome, ano_letivo=payload.ano_letivo, professor_id=professor_atual.id)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return turma


@router.get("/turmas", response_model=list[schemas.TurmaOut])
def listar_minhas_turmas(
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    return db.query(models.Turma).filter_by(professor_id=professor_atual.id).all()


# --- Alunos ---
@router.post("/alunos", response_model=schemas.AlunoOut)
def criar_aluno(
    payload: schemas.AlunoCreate,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    turma = _turma_do_professor_ou_404(payload.turma_id, professor_atual, db)

    aluno = models.Aluno(nome=payload.nome, numero_chamada=payload.numero_chamada)
    aluno.turmas.append(turma)
    db.add(aluno)
    db.commit()
    db.refresh(aluno)
    return aluno


@router.get("/turmas/{turma_id}/alunos", response_model=list[schemas.AlunoOut])
def listar_alunos_da_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    turma = _turma_do_professor_ou_404(turma_id, professor_atual, db)
    return turma.alunos
