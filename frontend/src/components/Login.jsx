import React, { useState } from 'react'
import { Landmark, Loader2 } from 'lucide-react'
import { login, registrar } from '../auth.js'

export default function Login({ onAutenticado }) {
  const [modo, setModo] = useState('login') // 'login' | 'cadastro'
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [escola, setEscola] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)

  const submeter = async (e) => {
    e.preventDefault()
    setErro(null)
    setCarregando(true)
    try {
      if (modo === 'cadastro') {
        await registrar(nome, email, senha, escola)
      }
      await login(email, senha)
      onAutenticado()
    } catch (err) {
      setErro(err?.response?.data?.detail ?? 'Não foi possível autenticar. Verifique os dados e tente novamente.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-academic-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-xl border border-academic-100 shadow-sm p-6">
        <div className="flex flex-col items-center gap-2 mb-6">
          <Landmark className="w-8 h-8 text-academic-800" />
          <h1 className="font-serif text-xl font-semibold text-academic-900">Historiador IA</h1>
          <p className="text-xs text-academic-700/60 text-center">
            {modo === 'login' ? 'Entre com sua conta de professor' : 'Crie sua conta de professor'}
          </p>
        </div>

        {erro && (
          <div className="mb-4 text-sm bg-red-50 text-red-800 border border-red-200 rounded-lg px-3 py-2">
            {erro}
          </div>
        )}

        <form onSubmit={submeter} className="flex flex-col gap-3">
          {modo === 'cadastro' && (
            <>
              <input
                type="text" placeholder="Nome completo" required value={nome}
                onChange={(e) => setNome(e.target.value)}
                className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
              />
              <input
                type="text" placeholder="Escola (opcional)" value={escola}
                onChange={(e) => setEscola(e.target.value)}
                className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
              />
            </>
          )}
          <input
            type="email" placeholder="E-mail" required value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
          />
          <input
            type="password" placeholder="Senha" required value={senha}
            onChange={(e) => setSenha(e.target.value)}
            className="rounded-md border border-academic-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-academic-600/40"
          />

          <button
            type="submit"
            disabled={carregando}
            className="flex items-center justify-center gap-2 bg-academic-700 hover:bg-academic-800 text-white text-sm font-medium px-4 py-2.5 rounded-md disabled:opacity-60 mt-1"
          >
            {carregando && <Loader2 className="w-4 h-4 animate-spin" />}
            {modo === 'login' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>

        <button
          onClick={() => { setModo(modo === 'login' ? 'cadastro' : 'login'); setErro(null) }}
          className="w-full text-center text-xs text-academic-700 hover:text-academic-900 mt-4"
        >
          {modo === 'login' ? 'Não tem conta? Cadastre-se' : 'Já tem conta? Entrar'}
        </button>
      </div>
    </div>
  )
}
