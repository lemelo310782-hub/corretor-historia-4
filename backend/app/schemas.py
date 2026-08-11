"""
Schemas Pydantic — contratos de entrada/saída da API.
Mantidos separados dos modelos ORM para não vazar detalhes do banco na API.
"""
import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ---------- Professor ----------
class ProfessorBase(BaseModel):
    nome: str
    email: EmailStr
    escola: Optional[str] = None


class ProfessorCreate(ProfessorBase):
    senha: str


class ProfessorOut(ProfessorBase):
    id: int
    criado_em: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Autenticação ----------
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Turma ----------
class TurmaBase(BaseModel):
    nome: str
    ano_letivo: Optional[str] = None


class TurmaCreate(TurmaBase):
    pass


class TurmaOut(TurmaBase):
    id: int
    professor_id: int

    class Config:
        from_attributes = True


# ---------- Aluno ----------
class AlunoBase(BaseModel):
    nome: str
    numero_chamada: Optional[str] = None


class AlunoCreate(AlunoBase):
    turma_id: int


class AlunoOut(AlunoBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Rubrica ----------
class RubricaOut(BaseModel):
    id: int
    titulo: str
    arquivo_original: str
    conteudo_extraido: Optional[str] = None
    criterios_json: Optional[str] = None  # JSON serializado; o front decodifica
    criado_em: datetime.datetime
    aviso: Optional[str] = None  # ex: "IA não configurada, critérios não estruturados"

    class Config:
        from_attributes = True


# ---------- Ficha Modelo ----------
class FichaModeloOut(BaseModel):
    id: int
    titulo: str
    arquivo_original: str
    campos_json: Optional[str] = None
    criado_em: datetime.datetime
    aviso: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Atividade ----------
class AtividadeCreate(BaseModel):
    titulo: str
    turma_id: int
    rubrica_id: int
    ficha_modelo_id: int
    pontuacao_maxima: float = 10.0


class AtividadeOut(BaseModel):
    id: int
    titulo: str
    turma_id: int
    rubrica_id: int
    ficha_modelo_id: int
    pontuacao_maxima: float
    criado_em: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Critério avaliado ----------
class CriterioAvaliadoOut(BaseModel):
    nome_criterio: str
    pontuacao_obtida: float
    pontuacao_maxima: float
    justificativa: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Correção ----------
class CorrecaoOut(BaseModel):
    id: int
    aluno_id: Optional[int] = None
    aluno_nome: Optional[str] = None
    atividade_id: int
    nome_detectado: Optional[str] = None
    usou_ocr: Optional[str] = None
    erro_extracao: Optional[str] = None
    erro_correcao: Optional[str] = None
    nota_final: Optional[float] = None
    pontos_fortes: Optional[str] = None
    pontos_a_melhorar: Optional[str] = None
    comentario_final: Optional[str] = None
    status: str
    criterios: List[CriterioAvaliadoOut] = []

    class Config:
        from_attributes = True


# ---------- Dashboard ----------
class DashboardOut(BaseModel):
    total_corrigidos: int
    media_turma: Optional[float]
    criterio_mais_dificil: Optional[str]
    criterio_melhor_desempenho: Optional[str]
    media_por_criterio: dict
