"""
Configurações centrais da aplicação Historiador IA.

Todas as configurações sensíveis (chaves de API, segredos) devem vir
de variáveis de ambiente, nunca hardcoded no código.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Em produção (ex: Render), monte um disco persistente e aponte DATA_DIR
# para ele, para que o banco SQLite e os arquivos enviados sobrevivam a
# reinícios/deploys. Localmente, sem essa variável, tudo fica dentro do
# próprio projeto como antes.
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))

# --- Banco de dados ---
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'historiador_ia.db'}")

# --- Diretórios de upload ---
UPLOAD_DIR = DATA_DIR / "uploads"
RUBRICAS_DIR = UPLOAD_DIR / "rubricas"
FICHAS_MODELO_DIR = UPLOAD_DIR / "fichas_modelo"
FICHAS_ALUNOS_DIR = UPLOAD_DIR / "fichas_alunos"
EXPORTS_DIR = DATA_DIR / "exports"

for d in (RUBRICAS_DIR, FICHAS_MODELO_DIR, FICHAS_ALUNOS_DIR, EXPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Upload ---
MAX_UPLOAD_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}

# --- IA (modelo trocável) ---
# O provedor pode ser trocado sem alterar o resto da aplicação —
# ver app/services/ai_provider.py.
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# --- OCR (Fase 2) ---
# "por" = português. Requer o pacote de idioma do Tesseract instalado
# (ver README para instruções de instalação por sistema operacional).
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "por")
MIN_CHARS_TEXTO_NATIVO = 30  # abaixo disso, um PDF é tratado como escaneado

# --- Segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas de sessão
