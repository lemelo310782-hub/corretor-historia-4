import React, { useState } from 'react'
import { ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Clock, FileDown } from 'lucide-react'
import { baixarArquivo } from '../api.js'

const ROTULO_STATUS = {
  pendente: { texto: 'Pendente', cor: 'text-academic-700/60', icone: Clock },
  processando: { texto: 'Processando...', cor: 'text-academic-600', icone: Clock },
  concluida: { texto: 'Corrigida', cor: 'text-green-700', icone: CheckCircle2 },
  erro: { texto: 'Erro', cor: 'text-red-600', icone: AlertCircle },
  revisada_professor: { texto: 'Revisada', cor: 'text-academic-700', icone: CheckCircle2 },
}

function LinhaCorrecao({ correcao }) {
  const [aberto, setAberto] = useState(false)
  const status = ROTULO_STATUS[correcao.status] ?? ROTULO_STATUS.pendente
  const Icone = status.icone

  return (
    <div className="border border-academic-100 rounded-lg overflow-hidden">
      <button
        onClick={() => setAberto(!aberto)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-academic-50 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <Icone className={`w-4 h-4 shrink-0 ${status.cor}`} />
          <span className="font-medium text-academic-900 truncate">
            {correcao.aluno_nome ?? correcao.nome_detectado ?? `Ficha #${correcao.id} (aluno não identificado)`}
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {correcao.nota_final != null && (
            <span className="text-sm font-semibold text-academic-900">{correcao.nota_final.toFixed(1)}</span>
          )}
          <span className={`text-xs ${status.cor}`}>{status.texto}</span>
          {aberto ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {aberto && (
        <div className="px-4 pb-4 pt-1 border-t border-academic-100 flex flex-col gap-3 text-sm">
          {correcao.status === 'erro' && (
            <p className="text-red-600">{correcao.erro_extracao || correcao.erro_correcao}</p>
          )}

          {correcao.criterios?.length > 0 && (
            <div className="flex flex-col gap-2">
              {correcao.criterios.map((c) => (
                <div key={c.nome_criterio} className="bg-academic-50 rounded-md p-2.5">
                  <div className="flex justify-between font-medium text-academic-900">
                    <span>{c.nome_criterio}</span>
                    <span>{c.pontuacao_obtida} / {c.pontuacao_maxima}</span>
                  </div>
                  {c.justificativa && <p className="text-academic-700/80 mt-1">{c.justificativa}</p>}
                </div>
              ))}
            </div>
          )}

          {correcao.pontos_fortes && (
            <div>
              <p className="font-medium text-academic-900">Pontos fortes</p>
              <p className="text-academic-700/80 whitespace-pre-line">{correcao.pontos_fortes}</p>
            </div>
          )}
          {correcao.pontos_a_melhorar && (
            <div>
              <p className="font-medium text-academic-900">Pontos a melhorar</p>
              <p className="text-academic-700/80 whitespace-pre-line">{correcao.pontos_a_melhorar}</p>
            </div>
          )}
          {correcao.comentario_final && (
            <div>
              <p className="font-medium text-academic-900">Comentário final</p>
              <p className="text-academic-700/80">{correcao.comentario_final}</p>
            </div>
          )}

          {correcao.status === 'concluida' && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                const nome = correcao.aluno_nome ?? correcao.nome_detectado ?? `aluno_${correcao.id}`
                baixarArquivo(`/correcoes/${correcao.id}/exportar-pdf`, `Correcao_${nome.replace(/\s+/g, '_')}.pdf`)
              }}
              className="self-start flex items-center gap-1.5 text-academic-700 hover:text-academic-900 text-sm font-medium mt-1"
            >
              <FileDown className="w-4 h-4" /> Baixar PDF desta correção
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default function ResultadosCorrecao({ correcoes }) {
  if (!correcoes || correcoes.length === 0) return null

  return (
    <div className="flex flex-col gap-2">
      {correcoes.map((correcao) => (
        <LinhaCorrecao key={correcao.id} correcao={correcao} />
      ))}
    </div>
  )
}
