import React, { useEffect, useState } from 'react'
import { BookOpen, Landmark, ClipboardList, BarChart3, Send, Loader2, Wand2, FileSpreadsheet, LogOut } from 'lucide-react'
import UploadArea from './components/UploadArea.jsx'
import Dashboard from './components/Dashboard.jsx'
import ResultadosCorrecao from './components/ResultadosCorrecao.jsx'
import Login from './components/Login.jsx'
import api, { baixarArquivo } from './api.js'
import { obterProfessorAtual, obterToken, limparToken } from './auth.js'

const ACEITOS = '.pdf,.docx,.png,.jpg,.jpeg'

export default function App() {
  const [verificandoSessao, setVerificandoSessao] = useState(true)
  const [professor, setProfessor] = useState(null)

  useEffect(() => {
    async function verificar() {
      if (obterToken()) {
        const dados = await obterProfessorAtual()
        setProfessor(dados)
      }
      setVerificandoSessao(false)
    }
    verificar()
  }, [])

  if (verificandoSessao) {
    return <div className="min-h-screen flex items-center justify-center text-academic-700">Carregando...</div>
  }

  if (!professor) {
    return <Login onAutenticado={async () => setProfessor(await obterProfessorAtual())} />
  }

  return <PainelProfessor professor={professor} onSair={() => { limparToken(); setProfessor(null) }} />
}

function PainelProfessor({ professor, onSair }) {
  const [tituloRubrica, setTituloRubrica] = useState('')
  const [arquivoRubrica, setArquivoRubrica] = useState(null)

  const [tituloFicha, setTituloFicha] = useState('')
  const [arquivoFicha, setArquivoFicha] = useState(null)

  const [atividadeId, setAtividadeId] = useState('')
  const [arquivosAlunos, setArquivosAlunos] = useState([])

  const [enviando, setEnviando] = useState(false)
  const [mensagem, setMensagem] = useState(null)

  const [atividadeIdPainel, setAtividadeIdPainel] = useState('')
  const [dadosDashboard, setDadosDashboard] = useState(null)
  const [correcoes, setCorrecoes] = useState([])
  const [corrigindo, setCorrigindo] = useState(false)

  const carregarPainel = async (id) => {
    try {
      const [{ data: dashboard }, { data: listaCorrecoes }] = await Promise.all([
        api.get(`/dashboard/atividade/${id}`),
        api.get(`/atividades/${id}/correcoes`),
      ])
      setDadosDashboard(dashboard)
      setCorrecoes(listaCorrecoes)
    } catch (err) {
      setMensagem({ tipo: 'erro', texto: err?.response?.data?.detail ?? 'Falha ao carregar o painel.' })
    }
  }

  const corrigirTudo = async () => {
    if (!atividadeIdPainel) {
      setMensagem({ tipo: 'erro', texto: 'Informe o ID da atividade para corrigir.' })
      return
    }
    setCorrigindo(true)
    try {
      const { data } = await api.post(`/atividades/${atividadeIdPainel}/corrigir-tudo`)
      setMensagem({
        tipo: data.falha.length > 0 ? 'erro' : 'sucesso',
        texto: `${data.sucesso.length} ficha(s) corrigida(s) com sucesso` +
          (data.falha.length > 0 ? `, ${data.falha.length} com erro (veja detalhes na lista abaixo).` : '.'),
      })
      await carregarPainel(atividadeIdPainel)
    } catch (err) {
      setMensagem({ tipo: 'erro', texto: err?.response?.data?.detail ?? 'Falha ao corrigir as fichas.' })
    } finally {
      setCorrigindo(false)
    }
  }

  const enviarRubrica = async () => {
    if (!tituloRubrica || !arquivoRubrica) {
      setMensagem({ tipo: 'erro', texto: 'Informe um título e selecione o arquivo da rubrica.' })
      return
    }
    setEnviando(true)
    try {
      const form = new FormData()
      form.append('arquivo', arquivoRubrica)
      await api.post(`/upload/rubrica?titulo=${encodeURIComponent(tituloRubrica)}`, form)
      setMensagem({ tipo: 'sucesso', texto: 'Rubrica enviada com sucesso.' })
    } catch (err) {
      setMensagem({ tipo: 'erro', texto: err?.response?.data?.detail ?? 'Falha ao enviar a rubrica.' })
    } finally {
      setEnviando(false)
    }
  }

  const enviarFichaModelo = async () => {
    if (!tituloFicha || !arquivoFicha) {
      setMensagem({ tipo: 'erro', texto: 'Informe um título e selecione o arquivo da ficha modelo.' })
      return
    }
    setEnviando(true)
    try {
      const form = new FormData()
      form.append('arquivo', arquivoFicha)
      await api.post(`/upload/ficha-modelo?titulo=${encodeURIComponent(tituloFicha)}`, form)
      setMensagem({ tipo: 'sucesso', texto: 'Ficha modelo enviada com sucesso.' })
    } catch (err) {
      setMensagem({ tipo: 'erro', texto: err?.response?.data?.detail ?? 'Falha ao enviar a ficha modelo.' })
    } finally {
      setEnviando(false)
    }
  }

  const enviarFichasAlunos = async () => {
    if (!atividadeId || arquivosAlunos.length === 0) {
      setMensagem({ tipo: 'erro', texto: 'Informe o ID da atividade e selecione as fichas dos alunos.' })
      return
    }
    setEnviando(true)
    try {
      const form = new FormData()
      arquivosAlunos.forEach((arquivo) => form.append('arquivos', arquivo))
      const { data } = await api.post(`/upload/fichas-alunos/${atividadeId}`, form)
      setMensagem({ tipo: 'sucesso', texto: `${data.total} ficha(s) recebida(s) para a atividade ${atividadeId}.` })
    } catch (err) {
      setMensagem({ tipo: 'erro', texto: err?.response?.data?.detail ?? 'Falha ao enviar as fichas dos alunos.' })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="min-h-screen">
      <header className="bg-academic-950 text-white">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Landmark className="w-7 h-7 text-academic-100" />
            <div>
              <h1 className="font-serif text-xl font-semibold leading-tight">Historiador IA</h1>
              <p className="text-xs text-academic-100/70">Corretor de Fichas de Fontes Históricas</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-academic-100/80 hidden sm:inline">{professor.nome}</span>
            <button
              onClick={onSair}
              className="flex items-center gap-1.5 text-sm text-academic-100/80 hover:text-white"
            >
              <LogOut className="w-4 h-4" /> Sair
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 flex flex-col gap-8">
        {mensagem && (
          <div
            className={`rounded-lg px-4 py-3 text-sm ${
              mensagem.tipo === 'sucesso'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {mensagem.texto}
          </div>
        )}

        <section>
          <h2 className="font-serif text-lg font-semibold text-academic-900 mb-3 flex items-center gap-2">
            <BookOpen className="w-5 h-5" /> 1. Documentos base
          </h2>
          <div className="grid md:grid-cols-2 gap-5">
            <div className="flex flex-col gap-3">
              <UploadArea
                titulo="Rubrica de avaliação"
                descricao="Critérios que a IA usará para corrigir as fichas."
                icone={ClipboardList}
                aceitos={ACEITOS}
                onArquivos={(lista) => setArquivoRubrica(lista[0] ?? null)}
              />
              <input
                type="text"
                placeholder="Título da rubrica (ex: Rubrica OPCVL - Revolução Industrial)"
                value={tituloRubrica}
                onChange={(e) => setTituloRubrica(e.target.value)}
                className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
              />
              <button
                onClick={enviarRubrica}
                disabled={enviando}
                className="self-start flex items-center gap-2 bg-academic-700 hover:bg-academic-800 text-white text-sm font-medium px-4 py-2 rounded-md disabled:opacity-60"
              >
                {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Enviar rubrica
              </button>
            </div>

            <div className="flex flex-col gap-3">
              <UploadArea
                titulo="Ficha modelo (em branco)"
                descricao="O modelo que os alunos preencheram."
                icone={BookOpen}
                aceitos={ACEITOS}
                onArquivos={(lista) => setArquivoFicha(lista[0] ?? null)}
              />
              <input
                type="text"
                placeholder="Título da ficha (ex: Ficha OPCVL - Fontes Históricas)"
                value={tituloFicha}
                onChange={(e) => setTituloFicha(e.target.value)}
                className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
              />
              <button
                onClick={enviarFichaModelo}
                disabled={enviando}
                className="self-start flex items-center gap-2 bg-academic-700 hover:bg-academic-800 text-white text-sm font-medium px-4 py-2 rounded-md disabled:opacity-60"
              >
                {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Enviar ficha modelo
              </button>
            </div>
          </div>
        </section>

        <section>
          <h2 className="font-serif text-lg font-semibold text-academic-900 mb-3 flex items-center gap-2">
            <ClipboardList className="w-5 h-5" /> 2. Fichas dos alunos
          </h2>
          <p className="text-sm text-academic-700/70 mb-3">
            Crie a atividade pela API (<code className="bg-academic-50 px-1 rounded">POST /api/atividades</code>)
            vinculando a turma, a rubrica e a ficha modelo enviadas acima. Depois, informe o ID gerado aqui para
            enviar as fichas preenchidas pelos alunos.
          </p>
          <div className="flex flex-col gap-3 max-w-md">
            <input
              type="number"
              placeholder="ID da atividade"
              value={atividadeId}
              onChange={(e) => setAtividadeId(e.target.value)}
              className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
            />
            <UploadArea
              titulo="Fichas preenchidas"
              descricao="Selecione um ou vários arquivos, um por aluno."
              icone={ClipboardList}
              multiplo
              aceitos={ACEITOS}
              onArquivos={setArquivosAlunos}
            />
            <button
              onClick={enviarFichasAlunos}
              disabled={enviando}
              className="self-start flex items-center gap-2 bg-academic-700 hover:bg-academic-800 text-white text-sm font-medium px-4 py-2 rounded-md disabled:opacity-60"
            >
              {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Enviar fichas dos alunos
            </button>
          </div>
        </section>

        <section>
          <h2 className="font-serif text-lg font-semibold text-academic-900 mb-3 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" /> 3. Corrigir e ver resultados
          </h2>
          <div className="flex flex-col gap-3">
            <div className="flex gap-2 max-w-md">
              <input
                type="number"
                placeholder="ID da atividade"
                value={atividadeIdPainel}
                onChange={(e) => setAtividadeIdPainel(e.target.value)}
                className="flex-1 rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
              />
              <button
                onClick={corrigirTudo}
                disabled={corrigindo}
                className="flex items-center gap-2 bg-academic-700 hover:bg-academic-800 text-white text-sm font-medium px-4 py-2 rounded-md disabled:opacity-60 whitespace-nowrap"
              >
                {corrigindo ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                Corrigir tudo
              </button>
              <button
                onClick={() => atividadeIdPainel && carregarPainel(atividadeIdPainel)}
                className="text-sm text-academic-700 hover:text-academic-900 px-3 py-2 whitespace-nowrap"
              >
                Atualizar
              </button>
              {correcoes.some((c) => c.status === 'concluida') && (
                <button
                  onClick={() => baixarArquivo(`/atividades/${atividadeIdPainel}/exportar-excel`, `relatorio_turma_${atividadeIdPainel}.xlsx`)}
                  className="flex items-center gap-2 border border-academic-700 text-academic-700 hover:bg-academic-50 text-sm font-medium px-4 py-2 rounded-md whitespace-nowrap"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  Excel da turma
                </button>
              )}
            </div>
            <p className="text-xs text-academic-700/60">
              "Corrigir tudo" aplica a rubrica sobre todas as fichas pendentes desta atividade e
              atualiza o painel abaixo automaticamente. Requer <code className="bg-academic-50 px-1 rounded">ANTHROPIC_API_KEY</code> configurada no backend.
            </p>

            <Dashboard dados={dadosDashboard} correcoes={correcoes} />
            <ResultadosCorrecao correcoes={correcoes} />
          </div>
        </section>
      </main>

      <footer className="text-center text-xs text-academic-700/50 py-6">
        Historiador IA — projeto completo: upload, extração/OCR, correção por IA, exportação e autenticação.
      </footer>
    </div>
  )
}
