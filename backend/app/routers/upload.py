"""
Rotas de upload de arquivos.

Fase 1: salva os arquivos com segurança (nome sanitizado, extensão
validada, tamanho limitado) e cria o registro no banco.

Fase 2: logo após salvar, o texto é extraído automaticamente (PDF nativo,
DOCX, ou OCR quando necessário) e:
- para a RUBRICA: o texto é estruturado em critérios/pontuação via IA;
- para a FICHA MODELO: os campos/perguntas são identificados via IA;
- para as FICHAS DOS ALUNOS: o texto é extraído e tentamos casar
  automaticamente com um aluno já cadastrado na turma (por nome).

Fase 5 (este arquivo passa a exigir): todas as rotas exigem um professor
autenticado. Rubrica e Ficha Modelo passam a pertencer a quem fez o
upload (`professor_id`), e o upload de fichas de alunos só é aceito se a
atividade pertencer ao professor autenticado — impedindo que um professor
veja ou manipule dados de outro.
"""
import json
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_professor_atual
from app.config import (
    RUBRICAS_DIR, FICHAS_MODELO_DIR, FICHAS_ALUNOS_DIR, BASE_DIR,
    ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB,
)
from app.services.extraction import extrair_texto
from app.services.rubrica_parser import estruturar_rubrica
from app.services.ficha_parser import identificar_campos
from app.services.ai_provider import IAIndisponivelError
from app.services.identificacao import extrair_nome_candidato, casar_aluno

router = APIRouter(prefix="/upload", tags=["Upload"])


def _nome_seguro(nome_original: str) -> str:
    """
    Sanitiza o nome do arquivo para evitar path traversal e XSS ao exibir
    o nome depois na interface (ex: <script> em nome de arquivo).
    Gera um prefixo único (uuid) + nome limpo.
    """
    base = Path(nome_original).name  # remove qualquer caminho embutido
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return f"{uuid.uuid4().hex[:8]}_{base}"


async def _salvar_arquivo(arquivo: UploadFile, destino_dir: Path) -> Path:
    """Salva o arquivo em disco e devolve o caminho ABSOLUTO (para extração)."""
    ext = Path(arquivo.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado: {ext or 'desconhecido'}. "
                   f"Formatos aceitos: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    conteudo = await arquivo.read()
    tamanho_mb = len(conteudo) / (1024 * 1024)
    if tamanho_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande ({tamanho_mb:.1f}MB). Limite: {MAX_UPLOAD_SIZE_MB}MB.",
        )

    nome_final = _nome_seguro(arquivo.filename or "arquivo")
    caminho = destino_dir / nome_final
    caminho.write_bytes(conteudo)
    return caminho


def _caminho_relativo(caminho_absoluto: Path) -> str:
    return str(caminho_absoluto.relative_to(BASE_DIR))


@router.post("/rubrica", response_model=schemas.RubricaOut)
async def upload_rubrica(
    titulo: str,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    caminho_abs = await _salvar_arquivo(arquivo, RUBRICAS_DIR)

    try:
        texto, _usou_ocr = extrair_texto(caminho_abs)
    except ValueError as e:
        caminho_abs.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(e))

    rubrica = models.Rubrica(
        professor_id=professor_atual.id,
        titulo=titulo,
        arquivo_original=_caminho_relativo(caminho_abs),
        conteudo_extraido=texto,
    )

    aviso = None
    try:
        estrutura = estruturar_rubrica(texto)
        rubrica.criterios_json = json.dumps(estrutura, ensure_ascii=False)
    except IAIndisponivelError as e:
        aviso = str(e)
    except ValueError as e:
        aviso = f"Texto extraído com sucesso, mas não foi possível estruturar os critérios: {e}"

    db.add(rubrica)
    db.commit()
    db.refresh(rubrica)

    resultado = schemas.RubricaOut.model_validate(rubrica)
    resultado.aviso = aviso
    return resultado


@router.post("/ficha-modelo", response_model=schemas.FichaModeloOut)
async def upload_ficha_modelo(
    titulo: str,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    caminho_abs = await _salvar_arquivo(arquivo, FICHAS_MODELO_DIR)

    try:
        texto, _usou_ocr = extrair_texto(caminho_abs)
    except ValueError as e:
        caminho_abs.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(e))

    ficha = models.FichaModelo(
        professor_id=professor_atual.id,
        titulo=titulo,
        arquivo_original=_caminho_relativo(caminho_abs),
        conteudo_extraido=texto,
    )

    aviso = None
    try:
        estrutura = identificar_campos(texto)
        ficha.campos_json = json.dumps(estrutura, ensure_ascii=False)
    except IAIndisponivelError as e:
        aviso = str(e)
    except ValueError as e:
        aviso = f"Texto extraído com sucesso, mas não foi possível identificar os campos: {e}"

    db.add(ficha)
    db.commit()
    db.refresh(ficha)

    resultado = schemas.FichaModeloOut.model_validate(ficha)
    resultado.aviso = aviso
    return resultado


@router.post("/fichas-alunos/{atividade_id}")
async def upload_fichas_alunos(
    atividade_id: int,
    arquivos: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    """
    Recebe múltiplas fichas de alunos para uma atividade já criada (e que
    precisa pertencer ao professor autenticado).

    Para cada arquivo: extrai o texto (com OCR se necessário) e tenta casar
    automaticamente com um aluno já matriculado na turma da atividade, pelo
    nome escrito na ficha. Se não conseguir, a correção fica com aluno_id
    nulo e nome_detectado preenchido, para associação manual na interface.

    Uma ficha que falhar na extração NÃO interrompe as demais — ela é salva
    com status "erro" e a mensagem em erro_extracao, para o professor saber
    exatamente quais arquivos precisam de atenção.
    """
    atividade = db.query(models.Atividade).get(atividade_id)
    if not atividade or atividade.turma.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")

    alunos_da_turma = atividade.turma.alunos

    resultados = []
    for arquivo in arquivos:
        caminho_abs = await _salvar_arquivo(arquivo, FICHAS_ALUNOS_DIR)

        correcao = models.Correcao(
            atividade_id=atividade_id,
            arquivo_original=_caminho_relativo(caminho_abs),
            status=models.StatusCorrecao.PENDENTE,
        )

        try:
            texto, usou_ocr = extrair_texto(caminho_abs)
            correcao.texto_extraido = texto
            correcao.usou_ocr = "true" if usou_ocr else "false"

            nome_candidato = extrair_nome_candidato(texto)
            aluno = casar_aluno(nome_candidato, alunos_da_turma) if nome_candidato else None
            if aluno:
                correcao.aluno_id = aluno.id
            else:
                correcao.nome_detectado = nome_candidato

        except ValueError as e:
            correcao.status = models.StatusCorrecao.ERRO
            correcao.erro_extracao = str(e)

        db.add(correcao)
        resultados.append(correcao)

    db.commit()
    for correcao in resultados:
        db.refresh(correcao)

    total_identificados = sum(1 for c in resultados if c.aluno_id is not None)
    total_com_erro = sum(1 for c in resultados if c.status == models.StatusCorrecao.ERRO)

    return {
        "atividade_id": atividade_id,
        "total_recebidas": len(resultados),
        "identificadas_automaticamente": total_identificados,
        "com_erro_de_extracao": total_com_erro,
        "correcoes": [schemas.CorrecaoOut.model_validate(c) for c in resultados],
    }


@router.post("/rubrica/{rubrica_id}/reestruturar", response_model=schemas.RubricaOut)
def reestruturar_rubrica(
    rubrica_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    """
    Reprocessa a estruturação de critérios de uma rubrica já enviada pelo
    professor autenticado. Útil quando o upload original aconteceu sem
    ANTHROPIC_API_KEY configurada — não é preciso reenviar o arquivo, o
    texto já extraído é reaproveitado.
    """
    rubrica = db.query(models.Rubrica).get(rubrica_id)
    if not rubrica or rubrica.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Rubrica não encontrada.")
    if not rubrica.conteudo_extraido:
        raise HTTPException(status_code=422, detail="Esta rubrica não tem texto extraído para estruturar.")

    try:
        estrutura = estruturar_rubrica(rubrica.conteudo_extraido)
    except IAIndisponivelError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    rubrica.criterios_json = json.dumps(estrutura, ensure_ascii=False)
    db.commit()
    db.refresh(rubrica)
    return rubrica


@router.post("/ficha-modelo/{ficha_id}/reidentificar-campos", response_model=schemas.FichaModeloOut)
def reidentificar_campos(
    ficha_id: int,
    db: Session = Depends(get_db),
    professor_atual: models.Professor = Depends(get_professor_atual),
):
    """Equivalente ao endpoint acima, mas para os campos da ficha modelo."""
    ficha = db.query(models.FichaModelo).get(ficha_id)
    if not ficha or ficha.professor_id != professor_atual.id:
        raise HTTPException(status_code=404, detail="Ficha modelo não encontrada.")
    if not ficha.conteudo_extraido:
        raise HTTPException(status_code=422, detail="Esta ficha não tem texto extraído para reprocessar.")

    try:
        estrutura = identificar_campos(ficha.conteudo_extraido)
    except IAIndisponivelError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    ficha.campos_json = json.dumps(estrutura, ensure_ascii=False)
    db.commit()
    db.refresh(ficha)
    return ficha
