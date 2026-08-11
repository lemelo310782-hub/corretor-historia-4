import React, { useCallback, useRef, useState } from 'react'
import { UploadCloud, FileCheck2, X } from 'lucide-react'

/**
 * Área de upload reutilizável.
 *
 * props:
 * - titulo: string
 * - descricao: string
 * - icone: componente lucide-react
 * - multiplo: bool — permite selecionar vários arquivos
 * - aceitos: string — atributo `accept` do input (ex: ".pdf,.docx,.png,.jpg")
 * - onArquivos: (FileList) => void
 */
export default function UploadArea({ titulo, descricao, icone: Icone, multiplo = false, aceitos, onArquivos }) {
  const inputRef = useRef(null)
  const [arrastando, setArrastando] = useState(false)
  const [arquivos, setArquivos] = useState([])

  const processarArquivos = useCallback(
    (lista) => {
      const novos = Array.from(lista)
      setArquivos(multiplo ? [...arquivos, ...novos] : novos)
      onArquivos?.(multiplo ? [...arquivos, ...novos] : novos)
    },
    [arquivos, multiplo, onArquivos]
  )

  const removerArquivo = (index) => {
    const restantes = arquivos.filter((_, i) => i !== index)
    setArquivos(restantes)
    onArquivos?.(restantes)
  }

  return (
    <div className="bg-white rounded-xl border border-academic-100 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        {Icone && <Icone className="w-5 h-5 text-academic-700" />}
        <h3 className="font-serif text-lg font-semibold text-academic-900">{titulo}</h3>
      </div>
      {descricao && <p className="text-sm text-academic-700/80">{descricao}</p>}

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setArrastando(true)
        }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => {
          e.preventDefault()
          setArrastando(false)
          if (e.dataTransfer.files?.length) processarArquivos(e.dataTransfer.files)
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed transition-colors
          flex flex-col items-center justify-center text-center gap-2 py-8 px-4
          ${arrastando ? 'border-academic-600 bg-academic-50' : 'border-academic-100 hover:border-academic-600/60'}`}
      >
        <UploadCloud className="w-8 h-8 text-academic-600" />
        <p className="text-sm text-academic-900 font-medium">
          Arraste o arquivo aqui ou clique para selecionar
        </p>
        <p className="text-xs text-academic-700/60">PDF, DOCX, PNG ou JPG</p>
        <input
          ref={inputRef}
          type="file"
          multiple={multiplo}
          accept={aceitos}
          className="hidden"
          onChange={(e) => e.target.files?.length && processarArquivos(e.target.files)}
        />
      </div>

      {arquivos.length > 0 && (
        <ul className="flex flex-col gap-1.5 mt-1">
          {arquivos.map((arquivo, index) => (
            <li
              key={`${arquivo.name}-${index}`}
              className="flex items-center justify-between text-sm bg-academic-50 rounded-md px-3 py-1.5"
            >
              <span className="flex items-center gap-2 truncate">
                <FileCheck2 className="w-4 h-4 text-academic-600 shrink-0" />
                <span className="truncate">{arquivo.name}</span>
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  removerArquivo(index)
                }}
                className="text-academic-700/50 hover:text-red-600 shrink-0"
                aria-label={`Remover ${arquivo.name}`}
              >
                <X className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
