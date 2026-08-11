"""
Pequeno helper para não repetir em cada router a lógica de "puxar o nome do
aluno via relacionamento" ao montar a resposta de uma Correção.
"""
from app import models, schemas


def serializar_correcao(correcao: models.Correcao) -> schemas.CorrecaoOut:
    saida = schemas.CorrecaoOut.model_validate(correcao)
    if correcao.aluno is not None:
        saida.aluno_nome = correcao.aluno.nome
    return saida


def serializar_correcoes(correcoes: list) -> list[schemas.CorrecaoOut]:
    return [serializar_correcao(c) for c in correcoes]
