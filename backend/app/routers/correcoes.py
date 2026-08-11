"""
Rotas do motor de correção (Fase 3).

Aplica a rubrica já estruturada (Fase 2) sobre o texto já extraído
(Fase 2) de cada ficha de aluno, critério por critério, e persiste o
resultado: nota final, feedback por critério, pontos fortes/a melhorar
e comentário final.
"""
import datetime
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_professor_atual
from app.services.correction_engine import corrigir
from app.services.ai_provider import IAIndisponivelError
from app.services.serializers import serializar_correcao

router = APIRouter(tags=["Correção"])


def _corrigir_uma(correcao: models.Correcao, db: Session) -> None:
    """
    Executa a correção de UMA ficha e persiste o resultado.
    Lança ValueError/IAIndisponivelError em caso de falha — quem chama
    decide como reportar (a correção individual vira HTTP 4xx/5xx; o lote
    captura e segue para a próxima).
    """
    atividade = correcao.atividade
    rubrica = atividade.rubrica
    ficha_modelo = atividade.ficha_modelo

    if not rubrica.criterios_json:
        raise ValueError(
            "A rubrica desta atividade ainda não foi estruturada em critérios. "
            "Configure a ANTHROPIC_API_KEY e reprocesse a rubrica "
            "(POST /api/upload/rubrica/{id}/reestruturar) antes de corrigir."
        )
    if correcao.status == models.StatusCorrecao.ERRO and correcao.erro_extracao:
        raise ValueError(
            f"Esta ficha teve erro na extração de texto e não pode ser corrigida: "
            f"{correcao.erro_extracao}"
        )
    if not correcao.texto_extraido:
        raise ValueError("Esta ficha não tem texto extraído para corrigir.")

    criterios_rubrica = json.loads(rubrica.criterios_json)["criterios"]
    campos_ficha = json.loads(ficha_modelo.campos_json)["campos"] if ficha_modelo.campos_json else None

    correcao.status = models.StatusCorrecao.PROCESSANDO
    correcao.erro_correcao = None
    db.commit()

    resultado = corrigir(criterios_rubrica, campos_ficha, correcao.texto_extraido)

    # Remove critérios de uma correção anterior, caso esta seja uma re-correção
    for criterio_antigo in list(correcao.criterios):
        db.delete(criterio_antigo)

    proporcao = (resultado["nota_bruta"] / resultado["nota_maxima_bruta"]) if resultado["nota_maxima_bruta"] else 0.0
    correcao.nota_final = round(proporcao * atividade.pontuacao_maxima, 2)
    correcao.pontos_fortes = "\n".join(f"- {p}" for p in resultado["pontos_fortes"])
    correcao.pontos_a_melhorar = "\n".join(f"- {p}" for p in resultado["pontos_a_melhorar"])
    correcao.comentario_final = resultado["comentario_final"]
    correcao.status = models.StatusCorrecao.CONCLUIDA
    correcao.corrigido_em = datetime.datetime.utcnow()

    for c in resultado["criterios"]:
        db.add(models.CriterioAvaliado(
            correcao_id=correcao.id,
            nome_criterio=c["nome"],
            pontuacao_obtida=c["pontuacao_obtida"],
            pontuacao_maxima=c["pontuacao_maxima"],
            justificativa=c["justificativa"],
        ))

    db.commit()
    db.refresh(correcao)


@router.post("/correcoes/{correcao_id}/corrigir", response_model=schemas.CorrecaoOut)
def corrigir_uma_ficha(
    correcao_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    correcao = db.query(models.Correcao).get(correcao_id)
    if not correcao or correcao.atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Correção não encontrada.")

    try:
        _corrigir_uma(correcao, db)
    except IAIndisponivelError as e:
        correcao.status = models.StatusCorrecao.ERRO
        correcao.erro_correcao = str(e)
        db.commit()
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        correcao.status = models.StatusCorrecao.ERRO
        correcao.erro_correcao = str(e)
        db.commit()
        raise HTTPException(status_code=422, detail=str(e))

    return serializar_correcao(correcao)


@router.get("/correcoes/{correcao_id}", response_model=schemas.CorrecaoOut)
def obter_correcao(
    correcao_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    correcao = db.query(models.Correcao).get(correcao_id)
    if not correcao or correcao.atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Correção não encontrada.")
    return serializar_correcao(correcao)


@router.post("/atividades/{atividade_id}/corrigir-tudo")
def corrigir_todas_da_atividade(
    atividade_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    """
    Corrige em lote todas as fichas pendentes (ou que falharam antes) de
    uma atividade. Uma falha individual NÃO interrompe as demais — cada
    resultado é reportado separadamente em `sucesso`/`falha`.
    """
    atividade = db.query(models.Atividade).get(atividade_id)
    if not atividade or atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    elegveis = [
        c for c in atividade.correcoes
        if c.status in (models.StatusCorrecao.PENDENTE, models.StatusCorrecao.ERRO)
        and c.erro_extracao is None  # fichas com erro de EXTRAÇÃO precisam ser reenviadas, não recorrigidas
    ]

    sucesso, falha = [], []
    for correcao in elegveis:
        try:
            _corrigir_uma(correcao, db)
            sucesso.append(correcao.id)
        except (ValueError, IAIndisponivelError) as e:
            correcao.status = models.StatusCorrecao.ERRO
            correcao.erro_correcao = str(e)
            db.commit()
            falha.append({"correcao_id": correcao.id, "erro": str(e)})

    return {
        "atividade_id": atividade_id,
        "total_processadas": len(elegveis),
        "sucesso": sucesso,
        "falha": falha,
    }
