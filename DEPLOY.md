# Deploy na nuvem — Historiador IA (100% gratuito)

Guia para colocar o app no ar sem instalar Python, Node, Tesseract ou
Poppler na sua máquina, e sem pagar nada. Backend no **Render** (plano
free), banco no **Neon** (Postgres free), frontend no **Vercel** (free).

Tempo estimado: 20 minutos.

**Por que funciona de graça sem perder dados:** os arquivos originais
enviados (rubrica, ficha modelo, fichas dos alunos) só são lidos uma vez,
no upload, para extrair o texto — e esse texto já fica salvo no banco.
Nada no app depende de reler o arquivo original depois. Então o único
dado que realmente precisa sobreviver a reinícios é o **banco de dados**
— e é isso que o Neon garante, de graça. O disco do Render pode ser
efêmero sem problema nenhum.

**Única contrapartida do free:** o Render "dorme" o serviço após ~15 min
sem uso. A primeira requisição depois disso demora uns 30–50s pra
acordar (as próximas voltam ao normal). Para um professor usando o app
esporadicamente, não costuma incomodar.

---

## 0. Pré-requisito: uma conta no GitHub

Se o projeto ainda não está num repositório, crie um em
https://github.com/new (pode ser privado) e suba os arquivos pelo
próprio site do GitHub, arrastando a pasta — sem precisar instalar Git.

---

## 1. Banco de dados: Neon (Postgres gratuito)

1. Crie uma conta em https://neon.tech (dá pra logar com GitHub).
2. **Create a project** → escolha um nome, ex. `historiador-ia`.
3. Na página do projeto, copie a **Connection string** (algo como
   `postgresql://usuario:senha@ep-xxxx.neon.tech/neondb?sslmode=require`).
   Guarde — você vai usar no passo 2.3.

---

## 2. Backend no Render (plano free)

1. Crie uma conta em https://render.com (login com GitHub).
2. **New +** → **Blueprint** → conecte o repositório. O Render detecta o
   `render.yaml` na raiz e propõe o serviço `historiador-ia-backend`
   (Docker, plano free) automaticamente.
3. Preencha as variáveis marcadas `sync: false`:
   - `ANTHROPIC_API_KEY` → sua chave da Anthropic
   - `DATABASE_URL` → a connection string do Neon (passo 1.3)
   - `CORS_ORIGINS` → deixe em branco por enquanto, você volta aqui no
     passo 3 com a URL do frontend
4. **Apply**. O primeiro build demora alguns minutos (instala
   Tesseract/Poppler dentro da imagem). Ao final você terá uma URL tipo
   `https://historiador-ia-backend.onrender.com`.
5. Teste abrindo `https://SEU-BACKEND.onrender.com/api/health` — deve
   responder `{"status":"ok","fase":5}` (pode demorar ~30s se o serviço
   estava dormindo).

> Sem Blueprint? Alternativa manual: **New +** → **Web Service** → escolha
> o repo → Runtime **Docker** → Dockerfile Path `backend/Dockerfile` →
> Docker Context `backend` → plano **Free** → adicione as variáveis acima
> manualmente (sem disco).

---

## 3. Frontend na Vercel (gratuito)

1. Crie uma conta em https://vercel.com (login com GitHub).
2. **Add New** → **Project** → selecione o mesmo repositório.
3. Em **Root Directory**, aponte para `frontend`.
4. Framework preset: Vercel detecta **Vite** sozinho.
5. Em **Environment Variables**, adicione:
   - `VITE_API_URL` = `https://SEU-BACKEND.onrender.com/api`
     (com `/api` no final)
6. **Deploy**. Você terá uma URL tipo `https://historiador-ia.vercel.app`.

---

## 4. Fechar o ciclo: liberar o CORS

Volte ao Render → seu serviço → **Environment** → edite `CORS_ORIGINS`
com a URL da Vercel:

```
CORS_ORIGINS=https://historiador-ia.vercel.app
```

Salve — o Render reinicia sozinho. Pronto: abra a URL da Vercel, cadastre
seu usuário de professor e o app está no ar, de graça, sem nada
instalado no seu computador.

---

## Atualizações futuras

Qualquer `git push` no repositório dispara redeploy automático no Render
e na Vercel — nada manual.

## Se um dia quiser tirar o "sono" do backend (evitar os 30-50s de espera)

Isso já é opcional/pago: no Render, mudar o plano de `free` para
`starter` (~US$7/mês) faz o serviço nunca dormir. O `render.yaml` já
funciona nos dois planos, só trocar a linha `plan: free` por
`plan: starter`. Não é necessário para o app funcionar — só evita a
espera na primeira requisição depois de um tempo parado.
