"""
Rotas de exportação (Fase 4):
- PDF individual da correção de um aluno
- Relatório da turma inteira em Excel

Ambas exigem que já exista pelo menos uma correção concluída — não faz
sentido exportar "nada".
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_professor_atual
from app.services.pdf_export import gerar_pdf_correcao
from app.services.excel_export import gerar_excel_turma

router = APIRouter(tags=["Exportação"])


@router.get("/correcoes/{correcao_id}/exportar-pdf")
def exportar_pdf_correcao(
    correcao_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    correcao = db.query(models.Correcao).get(correcao_id)
    if not correcao or correcao.atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Correção não encontrada.")
    if correcao.status != models.StatusCorrecao.CONCLUIDA:
        raise HTTPException(
            status_code=422,
            detail="Esta ficha ainda não foi corrigida — não há nota nem feedback para exportar.",
        )

    caminho = gerar_pdf_correcao(correcao, correcao.atividade)
    nome_aluno = correcao.aluno.nome if correcao.aluno else "aluno"
    nome_download = f"Correcao_{nome_aluno.replace(' ', '_')}.pdf"
    return FileResponse(str(caminho), media_type="application/pdf", filename=nome_download)


@router.get("/atividades/{atividade_id}/exportar-excel")
def exportar_excel_turma(
    atividade_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    atividade = db.query(models.Atividade).get(atividade_id)
    if not atividade or atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    if not atividade.correcoes:
        raise HTTPException(status_code=422, detail="Esta atividade ainda não tem nenhuma ficha enviada.")

    caminho = gerar_excel_turma(atividade)
    nome_download = f"Relatorio_{atividade.titulo.replace(' ', '_')}.xlsx"
    return FileResponse(
        str(caminho),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=nome_download,
    )
