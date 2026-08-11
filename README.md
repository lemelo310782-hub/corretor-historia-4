# Historiador IA — Corretor de Fichas de Fontes Históricas

Ferramenta para professores de História corrigirem fichas de análise de fontes
(metodologia OPCVL ou outra) com base em uma rubrica de avaliação definida
pelo professor.

## Status: projeto completo (Fases 1 a 5)

O que já funciona:

- ✅ Arquitetura completa (backend FastAPI + frontend React/Tailwind)
- ✅ Banco de dados (SQLite) com todas as entidades: Professor, Turma, Aluno,
  Rubrica, Ficha Modelo, Atividade, Correção, Critério Avaliado
- ✅ **Autenticação real**: cadastro de professor com senha em hash bcrypt,
  login que emite um token JWT, e toda rota que expõe dados (turmas,
  rubricas, fichas, atividades, correções, exportações) exige token válido
  **e** verifica que o recurso pertence ao professor autenticado — um
  professor nunca vê ou manipula dados de outro, mesmo trocando IDs na URL
- ✅ Cadastro de turmas e alunos (sempre escopado ao professor logado)
- ✅ Upload de rubrica, ficha modelo e fichas dos alunos (com validação de
  formato/tamanho e nomes de arquivo sanitizados contra path traversal/XSS)
- ✅ Extração de texto de PDF nativo e DOCX
- ✅ OCR automático (Tesseract, em português) para PDFs escaneados e imagens
- ✅ Estruturação da rubrica em critérios/níveis de pontuação via IA
- ✅ Identificação dos campos da ficha modelo via IA
- ✅ Identificação automática do aluno a partir do texto da ficha preenchida
- ✅ Motor de correção por IA, critério por critério, com pontuação sempre
  limitada ao intervalo válido e nota reescalada para o valor da atividade
- ✅ Correção individual e em lote, com reprocessamento de rubrica/ficha sem
  precisar reenviar o arquivo
- ✅ Exportação em PDF da correção individual (nome, nota, tabela de
  critérios, feedback) e relatório da turma em Excel (uma linha por aluno,
  uma coluna por critério)
- ✅ Gráficos reais no dashboard: média por critério, distribuição de notas,
  principais dificuldades da turma
- ✅ Interface completa: tela de login/cadastro, upload (drag & drop),
  correção em lote, resultados por aluno (com download de PDF individual) e
  download do Excel da turma
- ✅ Tratamento de erro robusto em toda a cadeia: upload, extração,
  correção, exportação e autenticação. Nenhuma falha individual derruba o
  processamento dos demais arquivos/fichas

Este é o fim do escopo original que você pediu. Possíveis evoluções
futuras — não pedidas originalmente, mas naturais para um produto em
produção — incluem: refresh token / logout em todos os dispositivos,
recuperação de senha por e-mail, múltiplos professores por turma
(coordenação), e migração de SQLite para PostgreSQL para uso multi-escola
(a troca é só na `DATABASE_URL`, o SQLAlchemy já abstrai o resto).

---

## Estrutura de pastas

```
historiador-ia/
├── backend/
│   ├── app/
│   │   ├── main.py          # ponto de entrada FastAPI
│   │   ├── config.py        # configurações (pastas, limites, chaves, OCR)
│   │   ├── database.py      # conexão SQLAlchemy
│   │   ├── models.py        # entidades do banco (ORM)
│   │   ├── schemas.py       # contratos de entrada/saída da API
│   │   ├── dependencies.py    # dependência compartilhada: professor autenticado (JWT)
│   │   ├── routers/
│   │   │   ├── auth.py       # cadastro (bcrypt) e login (emite JWT)
│   │   │   ├── turmas.py     # turmas e alunos do professor logado
│   │   │   ├── upload.py     # upload + extração + estruturação por IA + reprocessamento
│   │   │   ├── atividades.py
│   │   │   ├── correcoes.py  # motor de correção (individual e em lote)
│   │   │   ├── exports.py    # exportação de PDF individual e Excel da turma
│   │   │   └── dashboard.py
│   │   └── services/
│   │       ├── auth.py               # hash de senha (bcrypt) + emissão/validação de JWT
│   │       ├── extraction.py         # extração de texto de PDF/DOCX + OCR
│   │       ├── ai_provider.py        # abstração sobre o provedor de IA
│   │       ├── rubrica_parser.py     # estrutura a rubrica em critérios (IA)
│   │       ├── ficha_parser.py       # identifica campos da ficha modelo (IA)
│   │       ├── identificacao.py      # casa nome do aluno na ficha com a turma
│   │       ├── correction_engine.py  # motor de correção critério a critério (IA)
│   │       ├── pdf_export.py         # gera o PDF individual da correção
│   │       ├── excel_export.py       # gera o relatório da turma em Excel
│   │       └── serializers.py        # helpers de serialização (aluno_nome etc.)
│   ├── uploads/               # arquivos enviados (criado automaticamente)
│   ├── exports/                # PDFs/Excel gerados aqui
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── auth.js            # login, cadastro, gerenciamento de token
    │   ├── api.js             # cliente axios (anexa token automaticamente) + download de arquivos
    │   └── components/
    │       ├── Login.jsx               # tela de login/cadastro
    │       ├── UploadArea.jsx
    │       ├── Dashboard.jsx           # estatísticas + gráficos (recharts)
    │       └── ResultadosCorrecao.jsx  # lista de correções por aluno, expansível, com PDF
    └── package.json
```

---

## Como executar localmente

### 1. Dependências de sistema (OCR)

O OCR de PDFs escaneados e imagens depende de dois programas instalados no
sistema operacional — **não são pacotes Python, são binários**:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-por poppler-utils
```

**macOS (Homebrew):**
```bash
brew install tesseract tesseract-lang poppler
```

**Windows:**
- Tesseract: instale o executável em https://github.com/UB-Mannheim/tesseract/wiki
  (marque o pacote de idioma "Portuguese" no instalador) e adicione ao PATH.
- Poppler: baixe os binários em https://github.com/oschwartz10612/poppler-windows/releases
  e adicione a pasta `bin` ao PATH.

Sem isso instalado, o upload de PDF nativo e DOCX continua funcionando
normalmente — só o OCR de documentos escaneados/imagens vai falhar com uma
mensagem clara pedindo para instalar o Poppler/Tesseract.

### 2. Backend (API)

Pré-requisito: Python 3.10+

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Para habilitar a estruturação automática da rubrica e da ficha (por IA),
defina sua chave da Anthropic antes de subir o servidor:

```bash
export ANTHROPIC_API_KEY="sua-chave-aqui"   # Windows: set ANTHROPIC_API_KEY=sua-chave-aqui
```

Sem essa variável, o upload continua funcionando — o texto é extraído
normalmente, só a estruturação automática dos critérios/campos fica
indisponível (a resposta da API avisa isso no campo `aviso`).

```bash
uvicorn app.main:app --reload --port 8000
```

A API sobe em **http://localhost:8000**. O banco `historiador_ia.db`
(SQLite) é criado automaticamente na primeira execução.

Documentação interativa (Swagger) gerada automaticamente pelo FastAPI:
**http://localhost:8000/docs**

### 3. Frontend (interface do professor)

Pré-requisito: Node.js 18+

```bash
cd frontend
npm install
npm run dev
```

A interface sobe em **http://localhost:5173**.

---

## Testando o fluxo completo

1. Abra a interface (localhost:5173). Na primeira vez, clique em
   "Não tem conta? Cadastre-se" e crie sua conta de professor. Depois,
   faça login — o token fica salvo no navegador até você clicar em "Sair".
2. Cadastre uma turma e os alunos (pela documentação interativa em
   http://localhost:8000/docs, clicando em "Authorize" e colando o token,
   ou via curl com o cabeçalho `Authorization: Bearer <token>`):
   ```
   POST /api/turmas          { "nome": "9º Ano B - História", "ano_letivo": "2026" }
   POST /api/alunos          { "nome": "João Pedro Silva", "turma_id": 1 }
   ```
   O nome do aluno deve ser o mais próximo possível do que ele escreve na
   ficha, para o casamento automático funcionar.
3. Na interface, envie a rubrica e a ficha modelo. A resposta já traz o
   texto extraído e, se a `ANTHROPIC_API_KEY` estiver configurada, os
   critérios estruturados em JSON.
4. Crie a atividade vinculando os três IDs:
   ```
   POST /api/atividades      { "titulo": "Análise OPCVL - Revolução Industrial", "turma_id": 1, "rubrica_id": 1, "ficha_modelo_id": 1, "pontuacao_maxima": 10 }
   ```
5. Volte à interface, informe o ID da atividade e envie as fichas dos
   alunos (PDF, DOCX, foto/scan). A resposta mostra quantas foram
   identificadas automaticamente e quantas tiveram erro de extração.
6. Na seção "3. Corrigir e ver resultados", informe o mesmo ID da
   atividade e clique em **Corrigir tudo**. Isso aplica a rubrica sobre
   cada ficha pendente, critério por critério, e atualiza o painel, os
   gráficos e a lista de resultados automaticamente.
7. Clique em cada aluno para ver a pontuação e a justificativa por
   critério, pontos fortes/a melhorar e o comentário final — e o botão
   **Baixar PDF desta correção**.
8. Use o botão **Excel da turma** para baixar o relatório completo com
   uma linha por aluno e uma coluna por critério.

Se a rubrica ou a ficha modelo tiverem sido enviadas antes de você
configurar a `ANTHROPIC_API_KEY`, não é preciso reenviar os arquivos —
use:
```
POST /api/upload/rubrica/{id}/reestruturar
POST /api/upload/ficha-modelo/{id}/reidentificar-campos
```

Todas as rotas acima (exceto `/auth/registrar` e `/auth/login`) exigem o
cabeçalho `Authorization: Bearer <token>` — o frontend já cuida disso
automaticamente depois do login.

---

## Segurança: o que já está coberto e o que fica para produção real

Coberto:
- Senhas em hash bcrypt (nunca em texto puro)
- Tokens JWT assinados com expiração (8h por padrão, configurável)
- Toda rota de dado verifica que o recurso pertence ao professor autenticado
- Nomes de arquivo sanitizados contra path traversal/XSS
- Mensagens de erro de autenticação genéricas (não revelam se um e-mail
  existe no sistema)

Fica para quando for para produção de verdade (fora do escopo pedido):
- Trocar o `SECRET_KEY` de `config.py` por um valor forte e secreto (hoje
  tem um valor de exemplo — troque via variável de ambiente `SECRET_KEY`)
- HTTPS na frente da API (hoje é tudo `http://localhost`)
- Rate limiting no endpoint de login (proteção contra força bruta)
- Refresh token / logout remoto (hoje o token só expira, não há como
  invalidar antes disso)

