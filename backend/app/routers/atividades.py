"""
Rotas de atividades — vincula turma + rubrica + ficha modelo.

Todas as rotas exigem autenticação. A criação de atividade verifica que
turma, rubrica e ficha modelo pertencem TODAS ao professor autenticado —
não dá pra vincular uma rubrica de outro professor à sua turma, por exemplo.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_professor_atual
from app.services.serializers import serializar_correcoes

router = APIRouter(prefix="/atividades", tags=["Atividades"])


@router.post("", response_model=schemas.AtividadeOut)
def criar_atividade(
    payload: schemas.AtividadeCreate,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    turma = db.query(models.Turma).get(payload.turma_id)
    rubrica = db.query(models.Rubrica).get(payload.rubrica_id)
    ficha_modelo = db.query(models.FichaModelo).get(payload.ficha_modelo_id)

    if not turma or turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    if not rubrica or rubrica.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Rubrica não encontrada.")
    if not ficha_modelo or ficha_modelo.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Ficha modelo não encontrada.")

    atividade = models.Atividade(
        titulo=payload.titulo,
        turma_id=payload.turma_id,
        rubrica_id=payload.rubrica_id,
        ficha_modelo_id=payload.ficha_modelo_id,
        pontuacao_maxima=payload.pontuacao_maxima,
    )
    db.add(atividade)
    db.commit()
    db.refresh(atividade)
    return atividade


@router.get("/turma/{turma_id}", response_model=list[schemas.AtividadeOut])
def listar_atividades_da_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    turma = db.query(models.Turma).get(turma_id)
    if not turma or turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return db.query(models.Atividade).filter_by(turma_id=turma_id).all()


@router.get("/{atividade_id}/correcoes", response_model=list[schemas.CorrecaoOut])
def listar_correcoes_da_atividade(
    atividade_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    atividade = db.query(models.Atividade).get(atividade_id)
    if not atividade or atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    return serializar_correcoes(atividade.correcoes)
