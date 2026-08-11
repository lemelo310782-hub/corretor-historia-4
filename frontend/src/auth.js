import axios from 'axios'

const CHAVE_TOKEN = 'historiador_ia_token'

export function salvarToken(token) {
  localStorage.setItem(CHAVE_TOKEN, token)
}

export function obterToken() {
  return localStorage.getItem(CHAVE_TOKEN)
}

export function limparToken() {
  localStorage.removeItem(CHAVE_TOKEN)
}

export async function login(email, senha) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', senha)
  const { data } = await axios.post('http://localhost:8000/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  salvarToken(data.access_token)
  return data.access_token
}

export async function registrar(nome, email, senha, escola) {
  const { data } = await axios.post('http://localhost:8000/api/auth/registrar', {
    nome, email, senha, escola: escola || null,
  })
  return data
}

export async function obterProfessorAtual() {
  const token = obterToken()
  if (!token) return null
  try {
    const { data } = await axios.get('http://localhost:8000/api/auth/eu', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return data
  } catch {
    limparToken()
    return null
  }
}
