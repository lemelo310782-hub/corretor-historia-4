import axios from 'axios'
import { obterToken, limparToken } from './auth.js'

// Em dev, sem VITE_API_URL definida, usa o backend local.
// Em produção (Vercel), defina VITE_API_URL="https://SEU-BACKEND.onrender.com/api"
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

// Anexa o token em toda requisição, quando existir.
api.interceptors.request.use((config) => {
  const token = obterToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Se o token expirou ou é inválido, limpa a sessão local e recarrega para
// mostrar a tela de login novamente — evita ficar preso numa tela quebrada.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      limparToken()
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export default api

/**
 * Baixa um arquivo de uma rota protegida (PDF/Excel) usando o token já
 * anexado pelo interceptor acima. Um <a href> comum não funcionaria aqui
 * porque o navegador não envia o cabeçalho Authorization em navegação
 * direta — por isso buscamos como blob e disparamos o download manualmente.
 */
export async function baixarArquivo(caminho, nomeSugerido) {
  const resposta = await api.get(caminho, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([resposta.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = nomeSugerido
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
