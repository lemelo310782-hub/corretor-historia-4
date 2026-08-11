"""
Modelos de dados (SQLAlchemy ORM).

Estrutura pensada para o fluxo real de uma escola:

Professor
  └── Turma (1:N)
        └── Atividade (1:N)      -> vinculada a uma Rubrica e a uma Ficha Modelo
              └── Aluno (N:N via matrícula na turma)
              └── Correcao (1:1 por Aluno + Atividade)
                    └── CriterioAvaliado (1:N)  -> pontuação por critério da rubrica
"""
import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, DateTime, Enum, Table
)
from sqlalchemy.orm import relationship

from app.database import Base


class StatusCorrecao(str, enum.Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    ERRO = "erro"
    REVISADA_PROFESSOR = "revisada_professor"


# Tabela associativa: quais alunos estão em quais turmas
matricula = Table(
    "matricula",
    Base.metadata,
    Column("aluno_id", Integer, ForeignKey("alunos.id"), primary_key=True),
    Column("turma_id", Integer, ForeignKey("turmas.id"), primary_key=True),
)


class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    escola = Column(String(160), nullable=True)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    turmas = relationship("Turma", back_populates="professor", cascade="all, delete-orphan")


class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)  # ex: "9º Ano B - História"
    ano_letivo = Column(String(9), nullable=True)  # ex: "2026"
    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False)

    professor = relationship("Professor", back_populates="turmas")
    atividades = relationship("Atividade", back_populates="turma", cascade="all, delete-orphan")
    alunos = relationship("Aluno", secondary=matricula, back_populates="turmas")


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    numero_chamada = Column(String(10), nullable=True)

    turmas = relationship("Turma", secondary=matricula, back_populates="alunos")
    correcoes = relationship("Correcao", back_populates="aluno")


class Rubrica(Base):
    __tablename__ = "rubricas"

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
    titulo = Column(String(160), nullable=False)
    arquivo_original = Column(String(255), nullable=False)  # caminho do PDF/DOCX/imagem enviado
    conteudo_extraido = Column(Text, nullable=True)  # texto extraído (Fase 2: OCR/parsing)
    criterios_json = Column(Text, nullable=True)  # rubrica estruturada em JSON (Fase 2)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    atividades = relationship("Atividade", back_populates="rubrica")


class FichaModelo(Base):
    __tablename__ = "fichas_modelo"

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
    titulo = Column(String(160), nullable=False)
    arquivo_original = Column(String(255), nullable=False)
    conteudo_extraido = Column(Text, nullable=True)  # texto bruto extraído do arquivo
    campos_json = Column(Text, nullable=True)  # campos identificados na ficha (via IA)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    atividades = relationship("Atividade", back_populates="ficha_modelo")


class Atividade(Base):
    __tablename__ = "atividades"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(160), nullable=False)  # ex: "Análise OPCVL - Revolução Industrial"
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    rubrica_id = Column(Integer, ForeignKey("rubricas.id"), nullable=False)
    ficha_modelo_id = Column(Integer, ForeignKey("fichas_modelo.id"), nullable=False)
    pontuacao_maxima = Column(Float, default=10.0)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    turma = relationship("Turma", back_populates="atividades")
    rubrica = relationship("Rubrica", back_populates="atividades")
    ficha_modelo = relationship("FichaModelo", back_populates="atividades")
    correcoes = relationship("Correcao", back_populates="atividade", cascade="all, delete-orphan")


class Correcao(Base):
    __tablename__ = "correcoes"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=True)  # nulo até identificação
    atividade_id = Column(Integer, ForeignKey("atividades.id"), nullable=False)
    arquivo_original = Column(String(255), nullable=False)  # PDF enviado pelo aluno
    texto_extraido = Column(Text, nullable=True)
    usou_ocr = Column(String(5), nullable=True)  # "true"/"false" — string simples, evita migração de tipo
    nome_detectado = Column(String(160), nullable=True)  # nome lido na ficha quando não há match automático
    erro_extracao = Column(Text, nullable=True)  # mensagem de erro, se a extração de texto falhou
    erro_correcao = Column(Text, nullable=True)  # mensagem de erro, se o motor de correção falhou

    nota_final = Column(Float, nullable=True)
    pontos_fortes = Column(Text, nullable=True)
    pontos_a_melhorar = Column(Text, nullable=True)
    comentario_final = Column(Text, nullable=True)

    status = Column(Enum(StatusCorrecao), default=StatusCorrecao.PENDENTE)
    corrigido_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    aluno = relationship("Aluno", back_populates="correcoes")
    atividade = relationship("Atividade", back_populates="correcoes")
    criterios = relationship("CriterioAvaliado", back_populates="correcao", cascade="all, delete-orphan")


class CriterioAvaliado(Base):
    """Pontuação individual de UM critério da rubrica dentro de UMA correção."""
    __tablename__ = "criterios_avaliados"

    id = Column(Integer, primary_key=True, index=True)
    correcao_id = Column(Integer, ForeignKey("correcoes.id"), nullable=False)
    nome_criterio = Column(String(160), nullable=False)  # ex: "Contextualização histórica"
    pontuacao_obtida = Column(Float, nullable=False)
    pontuacao_maxima = Column(Float, nullable=False)
    justificativa = Column(Text, nullable=True)  # explicação gerada pela IA

    correcao = relationship("Correcao", back_populates="criterios")
