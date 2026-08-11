import React, { useMemo } from 'react'
import { BarChart3, Users, TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const COR_PRINCIPAL = '#2a5182'
const COR_ALERTA = '#c0392b'
const COR_GRADE = '#e8edf5'

/**
 * Painel de estatísticas com gráficos reais.
 *
 * props:
 * - dados: resultado de GET /dashboard/atividade/{id}
 *          { total_corrigidos, media_turma, criterio_mais_dificil,
 *            criterio_melhor_desempenho, media_por_criterio: {nome: pct} }
 * - correcoes: lista de GET /atividades/{id}/correcoes, usada para o
 *              histograma de distribuição de notas
 * - notaMaxima: pontuação máxima da atividade (para os buckets do histograma)
 */
export default function Dashboard({ dados, correcoes = [], notaMaxima = 10 }) {
  const semDados = !dados || dados.total_corrigidos === 0

  const dadosGraficoCriterios = useMemo(() => {
    if (!dados?.media_por_criterio) return []
    return Object.entries(dados.media_por_criterio).map(([nome, pct]) => ({ nome, pct }))
  }, [dados])

  const dadosHistograma = useMemo(() => {
    const notas = correcoes.map((c) => c.nota_final).filter((n) => n != null)
    if (notas.length === 0) return []

    const numFaixas = 5
    const tamanhoFaixa = notaMaxima / numFaixas
    const faixas = Array.from({ length: numFaixas }, (_, i) => ({
      faixa: `${(i * tamanhoFaixa).toFixed(1)}–${((i + 1) * tamanhoFaixa).toFixed(1)}`,
      total: 0,
    }))

    notas.forEach((nota) => {
      const indice = Math.min(Math.floor(nota / tamanhoFaixa), numFaixas - 1)
      faixas[indice].total += 1
    })

    return faixas
  }, [correcoes, notaMaxima])

  const principaisDificuldades = useMemo(() => {
    return dadosGraficoCriterios
      .filter((c) => c.pct < 70)
      .sort((a, b) => a.pct - b.pct)
      .slice(0, 3)
  }, [dadosGraficoCriterios])

  const cartoes = [
    { icone: Users, rotulo: 'Alunos corrigidos', valor: dados?.total_corrigidos ?? 0 },
    { icone: BarChart3, rotulo: 'Média da turma', valor: dados?.media_turma != null ? dados.media_turma.toFixed(1) : '—' },
    { icone: TrendingDown, rotulo: 'Critério com mais dificuldade', valor: dados?.criterio_mais_dificil ?? '—', pequeno: true },
    { icone: TrendingUp, rotulo: 'Critério com melhor desempenho', valor: dados?.criterio_melhor_desempenho ?? '—', pequeno: true },
  ]

  return (
    <div className="bg-white rounded-xl border border-academic-100 shadow-sm p-5">
      <h3 className="font-serif text-lg font-semibold text-academic-900 mb-4">Painel da atividade</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {cartoes.map(({ icone: Icone, rotulo, valor, pequeno }) => (
          <div key={rotulo} className="bg-academic-50 rounded-lg p-3 flex flex-col gap-1">
            <Icone className="w-4 h-4 text-academic-600" />
            <span className={`font-semibold text-academic-900 ${pequeno ? 'text-sm' : 'text-xl'}`}>{valor}</span>
            <span className="text-xs text-academic-700/70">{rotulo}</span>
          </div>
        ))}
      </div>

      {semDados ? (
        <p className="text-sm text-academic-700/60 italic">
          Nenhuma correção concluída ainda. Clique em "Corrigir tudo" acima para gerar os gráficos
          de desempenho por critério e distribuição de notas.
        </p>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm font-medium text-academic-900 mb-2">Média por critério (%)</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={dadosGraficoCriterios} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COR_GRADE} horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="nome" width={140} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                  {dadosGraficoCriterios.map((entrada, i) => (
                    <Cell key={i} fill={entrada.pct < 70 ? COR_ALERTA : COR_PRINCIPAL} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <p className="text-sm font-medium text-academic-900 mb-2">Distribuição de notas</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={dadosHistograma} margin={{ left: -16, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COR_GRADE} vertical={false} />
                <XAxis dataKey="faixa" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `${v} aluno(s)`} />
                <Bar dataKey="total" fill={COR_PRINCIPAL} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {principaisDificuldades.length > 0 && (
            <div className="md:col-span-2 bg-red-50 border border-red-100 rounded-lg p-3 flex flex-col gap-1">
              <p className="text-sm font-medium text-red-800 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" /> Principais dificuldades da turma
              </p>
              <ul className="text-sm text-red-700/90 list-disc list-inside">
                {principaisDificuldades.map((c) => (
                  <li key={c.nome}>{c.nome} — média de {c.pct}%</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
