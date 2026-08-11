"""
Tenta identificar de qual aluno é uma ficha preenchida, a partir do texto
extraído — sem usar IA aqui: é um problema simples de regex + comparação
de string, e reservar a IA só para o que realmente precisa dela mantém o
sistema mais rápido, barato e previsível.

Isso é best-effort: se não achar um único match claro, devolve None e o
professor associa manualmente na interface (a ser refinado na Fase 3, se
a taxa de acerto automático não for boa o suficiente).
"""
import re
import unicodedata

PADRAO_NOME = re.compile(
    r"(?:nome\s+do\s+aluno|nome\s+completo|nome)\s*[:\-]\s*(.+)", re.IGNORECASE
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def extrair_nome_candidato(texto_ficha: str) -> str | None:
    """Procura um padrão 'Nome: ...' nas primeiras linhas do texto extraído."""
    primeiras_linhas = "\n".join(texto_ficha.splitlines()[:15])
    match = PADRAO_NOME.search(primeiras_linhas)
    if not match:
        return None

    candidato = match.group(1).strip()
    # corta se pegou a linha inteira e emendou o próximo campo (ex: "Maria Turma: 9B")
    candidato = re.split(r"\s{2,}|\t|(?=Turma[:\-])|(?=Data[:\-])", candidato)[0].strip()
    return candidato or None


def casar_aluno(nome_candidato: str, alunos_da_turma: list) -> "object | None":
    """
    Tenta casar o nome candidato com um único aluno já cadastrado na turma.
    Retorna o objeto Aluno em caso de match único e inequívoco, senão None.
    """
    if not nome_candidato:
        return None

    alvo = _normalizar(nome_candidato)
    correspondencias = [
        aluno for aluno in alunos_da_turma
        if _normalizar(aluno.nome) == alvo or alvo in _normalizar(aluno.nome) or _normalizar(aluno.nome) in alvo
    ]

    if len(correspondencias) == 1:
        return correspondencias[0]
    return None
