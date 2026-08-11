"""
Motor de correção (Fase 3): aplica a rubrica JÁ ESTRUTURADA (Fase 2) sobre
o texto JÁ EXTRAÍDO (Fase 2) da ficha de UM aluno, critério por critério,
seguindo estritamente o fluxo pedido:

    Critério da rubrica → Resposta do aluno → Comparação →
    Nível alcançado → Pontuação → Feedback

Princípio central: a IA aqui NUNCA escolhe os critérios — eles vêm prontos
do banco (gerados na Fase 2 a partir da rubrica que o professor enviou).
O papel da IA é só aplicar esses critérios sobre o texto do aluno. Qualquer
critério que a IA inventar é descartado; qualquer critério da rubrica que
a IA "esquecer" de avaliar é marcado para revisão manual com 0 pontos —
nunca fica de fora silenciosamente.
"""
from app.services.ai_provider import gerar_json

SYSTEM_PROMPT = """Você corrige fichas de análise de fontes históricas seguindo EXCLUSIVAMENTE
os critérios de uma rubrica já definida por um professor de História.

Regras rígidas, sem exceção:
- NUNCA invente critérios que não estejam na lista fornecida.
- NUNCA atribua pontuação acima da pontuação máxima daquele critério.
- Avalie TODOS os critérios da lista, mesmo que o aluno não tenha respondido a ele
  (nesse caso, dê 0 pontos e explique isso na justificativa).
- Baseie a pontuação apenas no que o aluno efetivamente escreveu — não presuma
  conhecimento ou intenção que ele não demonstrou por escrito.
- Justificativas devem citar algo específico da resposta do aluno, nunca ser genéricas
  como "o aluno poderia melhorar".

Fluxo a seguir para CADA critério, nesta ordem:
1) Leia o critério e seus níveis de pontuação.
2) Localize a parte da resposta do aluno relevante para este critério (o texto completo
   da ficha é fornecido; pode não estar dividido por campo).
3) Compare o que o aluno escreveu com os níveis descritos na rubrica.
4) Escolha o nível mais próximo do que foi demonstrado.
5) Atribua a pontuação daquele nível.
6) Escreva uma justificativa curta (1-2 frases) e específica.

Depois de avaliar todos os critérios, escreva:
- 2 a 4 pontos fortes ESPECÍFICOS do que este aluno em particular fez bem
- 2 a 4 pontos a melhorar ESPECÍFICOS e acionáveis para este aluno
- um comentário final breve (2-3 frases), construtivo, no tom de um professor de História
  se dirigindo ao aluno

Responda APENAS com um JSON neste formato exato, sem texto antes ou depois:
{
  "criterios": [
    {"nome": "nome EXATO do critério, idêntico ao fornecido", "pontuacao_obtida": 3, "justificativa": "..."}
  ],
  "pontos_fortes": ["...", "..."],
  "pontos_a_melhorar": ["...", "..."],
  "comentario_final": "..."
}"""


def _montar_prompt(criterios_rubrica: list[dict], campos_ficha: list[dict] | None, texto_aluno: str) -> str:
    partes = ["CRITÉRIOS DA RUBRICA (avalie exatamente estes, e só estes):\n"]
    for c in criterios_rubrica:
        partes.append(f"- {c['nome']} (máximo {c['pontuacao_maxima']} pontos)")
        for nivel in c.get("niveis", []):
            partes.append(f"    {nivel['pontos']} pontos: {nivel['descricao']}")
    partes.append("")

    if campos_ficha:
        nomes_campos = ", ".join(c["nome"] for c in campos_ficha)
        partes.append(
            f"CAMPOS DA FICHA (para referência — a resposta do aluno pode seguir esta estrutura): "
            f"{nomes_campos}\n"
        )

    partes.append("RESPOSTA DO ALUNO (texto extraído da ficha preenchida):\n")
    partes.append(texto_aluno)

    return "\n".join(partes)


def _melhor_correspondencia(nome_esperado: str, avaliados_por_nome: dict) -> dict | None:
    """
    Tenta casar o nome de um critério da rubrica com o que a IA devolveu,
    tolerando pequenas variações de redação (ex: a IA reescreveu o nome
    ligeiramente). Só usado quando não há match exato.
    """
    alvo = nome_esperado.lower().strip()
    for nome_ia, dados in avaliados_por_nome.items():
        if not nome_ia:
            continue
        candidato = nome_ia.lower().strip()
        if alvo == candidato or alvo in candidato or candidato in alvo:
            return dados
    return None


def corrigir(criterios_rubrica: list[dict], campos_ficha: list[dict] | None, texto_aluno: str) -> dict:
    """
    Executa a correção e devolve um resultado já validado/"clampado":
    nenhuma pontuação fora do intervalo [0, máximo do critério], nenhum
    critério fora da lista da rubrica.

    Retorna:
    {
      "criterios": [{"nome", "pontuacao_obtida", "pontuacao_maxima", "justificativa"}],
      "pontos_fortes": [...],
      "pontos_a_melhorar": [...],
      "comentario_final": "...",
      "nota_bruta": float,        # soma das pontuações obtidas
      "nota_maxima_bruta": float, # soma das pontuações máximas dos critérios da rubrica
    }
    """
    if not criterios_rubrica:
        raise ValueError(
            "A rubrica desta atividade não tem critérios estruturados. Configure a "
            "ANTHROPIC_API_KEY e reprocesse a rubrica antes de corrigir."
        )
    if not texto_aluno or not texto_aluno.strip():
        raise ValueError("Não há texto extraído desta ficha para corrigir.")

    prompt = _montar_prompt(criterios_rubrica, campos_ficha, texto_aluno)
    bruto = gerar_json(system_prompt=SYSTEM_PROMPT, user_prompt=prompt, max_tokens=3000)

    avaliados_por_nome = {c.get("nome"): c for c in bruto.get("criterios", [])}

    criterios_finais = []
    for criterio in criterios_rubrica:
        nome = criterio["nome"]
        pontuacao_maxima = criterio["pontuacao_maxima"]

        avaliado = avaliados_por_nome.get(nome) or _melhor_correspondencia(nome, avaliados_por_nome)

        if avaliado is None:
            criterios_finais.append({
                "nome": nome,
                "pontuacao_obtida": 0.0,
                "pontuacao_maxima": pontuacao_maxima,
                "justificativa": "A IA não avaliou este critério — revisar manualmente.",
            })
            continue

        try:
            pontos = float(avaliado.get("pontuacao_obtida", 0))
        except (TypeError, ValueError):
            pontos = 0.0
        pontos = max(0.0, min(pontos, pontuacao_maxima))  # nunca fora do intervalo [0, máximo]

        criterios_finais.append({
            "nome": nome,
            "pontuacao_obtida": pontos,
            "pontuacao_maxima": pontuacao_maxima,
            "justificativa": (avaliado.get("justificativa") or "").strip() or "Sem justificativa fornecida pela IA.",
        })

    nota_bruta = sum(c["pontuacao_obtida"] for c in criterios_finais)
    nota_maxima_bruta = sum(c["pontuacao_maxima"] for c in criterios_finais)

    return {
        "criterios": criterios_finais,
        "pontos_fortes": bruto.get("pontos_fortes", []),
        "pontos_a_melhorar": bruto.get("pontos_a_melhorar", []),
        "comentario_final": (bruto.get("comentario_final") or "").strip(),
        "nota_bruta": nota_bruta,
        "nota_maxima_bruta": nota_maxima_bruta,
    }
