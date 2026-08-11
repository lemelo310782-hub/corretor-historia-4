"""
Rota de dashboard. Calcula estatísticas reais a partir das correções já
salvas no banco (funciona assim que a Fase 3 - motor de correção - estiver
gerando CriterioAvaliado). Em Fase 1, retorna zeros/nulos com a turma vazia.
"""
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_professor_atual

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/atividade/{atividade_id}", response_model=schemas.DashboardOut)
def dashboard_atividade(
    atividade_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    atividade = db.query(models.Atividade).get(atividade_id)
    if not atividade or atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    correcoes_concluidas = [
        c for c in atividade.correcoes if c.status == models.StatusCorrecao.CONCLUIDA
    ]

    if not correcoes_concluidas:
        return schemas.DashboardOut(
            total_corrigidos=0,
            media_turma=None,
            criterio_mais_dificil=None,
            criterio_melhor_desempenho=None,
            media_por_criterio={},
        )

    notas = [c.nota_final for c in correcoes_concluidas if c.nota_final is not None]
    media_turma = sum(notas) / len(notas) if notas else None

    soma_por_criterio = defaultdict(list)
    for correcao in correcoes_concluidas:
        for criterio in correcao.criterios:
            proporcao = criterio.pontuacao_obtida / criterio.pontuacao_maxima
            soma_por_criterio[criterio.nome_criterio].append(proporcao)

    media_por_criterio = {
        nome: round(sum(valores) / len(valores) * 100, 1)
        for nome, valores in soma_por_criterio.items()
    }

    criterio_mais_dificil = min(media_por_criterio, key=media_por_criterio.get) if media_por_criterio else None
    criterio_melhor = max(media_por_criterio, key=media_por_criterio.get) if media_por_criterio else None

    return schemas.DashboardOut(
        total_corrigidos=len(correcoes_concluidas),
        media_turma=round(media_turma, 2) if media_turma is not None else None,
        criterio_mais_dificil=criterio_mais_dificil,
        criterio_melhor_desempenho=criterio_melhor,
        media_por_criterio=media_por_criterio,
    )
