"""
Gera o PDF individual de uma correção: nome do aluno, nota final, rubrica
preenchida (critério por critério, com pontuação e justificativa) e o
feedback pedagógico (pontos fortes, pontos a melhorar, comentário final).
"""
import re
import unicodedata
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from app.config import EXPORTS_DIR

COR_PRINCIPAL = colors.HexColor("#0f2038")   # azul escuro acadêmico
COR_SECUNDARIA = colors.HexColor("#2a5182")
COR_FUNDO_LINHA = colors.HexColor("#f5f7fb")
COR_BORDA = colors.HexColor("#e8edf5")


def _slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", sem_acento).strip("_").lower()[:40] or "aluno"


def _linhas_com_marcador(texto_bloco: str) -> list[str]:
    """Separa um bloco tipo '- item1\\n- item2' em uma lista de strings limpas."""
    linhas = []
    for linha in (texto_bloco or "").split("\n"):
        linha = linha.strip().lstrip("-").strip()
        if linha:
            linhas.append(linha)
    return linhas


def gerar_pdf_correcao(correcao, atividade) -> Path:
    """
    Gera o PDF em EXPORTS_DIR e retorna o caminho do arquivo.

    `correcao` precisa ter `.criterios` e `.aluno` já carregáveis (a sessão
    do SQLAlchemy que os buscou deve continuar aberta, ou os dados já
    terem sido acessados/carregados antes de fechar a sessão).
    """
    nome_aluno = correcao.aluno.nome if correcao.aluno else (correcao.nome_detectado or f"Ficha #{correcao.id}")
    caminho = EXPORTS_DIR / f"correcao_{correcao.id}_{_slug(nome_aluno)}.pdf"

    doc = SimpleDocTemplate(
        str(caminho), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("TituloHistoriadorIA", parent=styles["Title"], textColor=COR_PRINCIPAL, fontSize=18)
    estilo_subtitulo = ParagraphStyle("SubtituloHistoriadorIA", parent=styles["Normal"], textColor=COR_SECUNDARIA, fontSize=11)
    estilo_secao = ParagraphStyle("SecaoHistoriadorIA", parent=styles["Heading2"], textColor=COR_PRINCIPAL, spaceBefore=14, spaceAfter=6, fontSize=13)
    estilo_nota = ParagraphStyle("NotaHistoriadorIA", parent=styles["Normal"], fontSize=15, textColor=COR_PRINCIPAL)

    elementos = [
        Paragraph("Correção da Ficha de Análise Histórica", estilo_titulo),
        Spacer(1, 4),
        Paragraph(f"Atividade: {atividade.titulo}", estilo_subtitulo),
        Paragraph(f"Aluno: {nome_aluno}", estilo_subtitulo),
        Spacer(1, 10),
        HRFlowable(width="100%", color=COR_BORDA),
        Spacer(1, 10),
    ]

    nota_texto = (
        f"{correcao.nota_final:.1f} / {atividade.pontuacao_maxima:.1f}"
        if correcao.nota_final is not None else "—"
    )
    elementos.append(Paragraph(f"<b>Nota final: {nota_texto}</b>", estilo_nota))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Avaliação por critério", estilo_secao))
    dados_tabela = [["Critério", "Pontuação", "Justificativa"]]
    for c in correcao.criterios:
        dados_tabela.append([
            Paragraph(c.nome_criterio, styles["Normal"]),
            f"{c.pontuacao_obtida:.1f} / {c.pontuacao_maxima:.1f}",
            Paragraph(c.justificativa or "", styles["Normal"]),
        ])

    tabela = Table(dados_tabela, colWidths=[4.5 * cm, 2.2 * cm, 8.8 * cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, COR_BORDA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_FUNDO_LINHA]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 14))

    pontos_fortes = _linhas_com_marcador(correcao.pontos_fortes)
    if pontos_fortes:
        elementos.append(Paragraph("Pontos fortes", estilo_secao))
        for item in pontos_fortes:
            elementos.append(Paragraph(f"• {item}", styles["Normal"]))

    pontos_a_melhorar = _linhas_com_marcador(correcao.pontos_a_melhorar)
    if pontos_a_melhorar:
        elementos.append(Paragraph("Pontos a melhorar", estilo_secao))
        for item in pontos_a_melhorar:
            elementos.append(Paragraph(f"• {item}", styles["Normal"]))

    if correcao.comentario_final:
        elementos.append(Paragraph("Comentário final do professor", estilo_secao))
        elementos.append(Paragraph(correcao.comentario_final, styles["Normal"]))

    doc.build(elementos)
    return caminho
