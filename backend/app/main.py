"""
Historiador IA — Corretor de Fichas de Fontes Históricas
Ponto de entrada da API (FastAPI).

Projeto completo (Fases 1 a 5):
Fase 1: arquitetura, banco de dados, cadastro, upload com validação.
Fase 2: extração de texto (PDF/DOCX) + OCR (Tesseract) para documentos
        escaneados; estruturação da rubrica e da ficha modelo via IA;
        identificação automática do aluno por nome.
Fase 3: motor de correção — aplica a rubrica estruturada sobre o texto de
        cada ficha, critério por critério, gera nota final, feedback e
        pontos fortes/a melhorar.
Fase 4: exportação — PDF individual da correção de cada aluno e relatório
        da turma inteira em Excel; gráficos reais no dashboard.
Fase 5 (este arquivo passa a exigir): autenticação — cadastro/login de
        professor com senha em hash (bcrypt) e token JWT; toda rota que
        expõe dados de turmas/rubricas/fichas/correções agora exige um
        token válido E verifica que o recurso pertence ao professor
        autenticado (isolamento entre contas).
        Endpoints: POST /api/auth/registrar, POST /api/auth/login,
        GET /api/auth/eu.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import turmas, upload, atividades, dashboard, correcoes, exports, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Historiador IA - Corretor de Fichas de Fontes Históricas",
    description="Ferramenta para professores de História corrigirem fichas "
                "de análise de fontes com base em uma rubrica.",
    version="1.0.0",
)

# CORS: em dev usa localhost; em produção defina CORS_ORIGINS no ambiente
# com a(s) URL(s) do frontend publicado, separadas por vírgula, ex:
# CORS_ORIGINS="https://historiador-ia.vercel.app"
_cors_env = os.getenv("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(turmas.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(atividades.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(correcoes.router, prefix="/api")
app.include_router(exports.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "fase": 5}
