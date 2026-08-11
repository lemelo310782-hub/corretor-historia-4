"""
Estrutura o texto bruto de uma rubrica em uma lista de critérios com seus
níveis de pontuação — o formato que o motor de correção (Fase 3) vai
consumir diretamente, seguindo o fluxo pedido:

    Critério da rubrica → Resposta do aluno → Comparação →
    Nível alcançado → Pontuação → Feedback

Importante: esta etapa SÓ estrutura o que já está escrito na rubrica.
Ela não avalia nada — não tem contato com respostas de aluno. Isso mantém
o princípio central do projeto: a IA de correção (Fase 3) não pode inventar
critérios, só aplicar os que o professor definiu aqui.
"""
from app.services.ai_provider import gerar_json

SYSTEM_PROMPT = """Você estrutura rubricas de avaliação de História em JSON.

Leia o texto de uma rubrica de avaliação (fornecida por um professor de História) e extraia
CADA critério com seus níveis de pontuação, exatamente como estão descritos no texto.

Regras:
- Não invente critérios, níveis ou descrições que não estejam no texto original.
- Se um critério não tiver níveis intermediários explícitos, inclua apenas os níveis que existem.
- Se a pontuação total do documento não estiver clara, some a pontuação máxima de cada critério.
- Preserve a redação original das descrições (não parafraseie o conteúdo pedagógico).

Responda APENAS com um JSON neste formato exato, sem nenhum texto antes ou depois:
{
  "criterios": [
    {
      "nome": "nome curto do critério, ex: Contextualização histórica",
      "pontuacao_maxima": 4,
      "niveis": [
        {"pontos": 4, "descricao": "descrição do nível máximo"},
        {"pontos": 2, "descricao": "descrição do nível intermediário"},
        {"pontos": 0, "descricao": "descrição do nível mínimo"}
      ]
    }
  ],
  "pontuacao_total_maxima": 10
}"""


def estruturar_rubrica(texto_rubrica: str) -> dict:
    """
    Retorna um dict no formato acima. Lança ValueError se o texto estiver
    vazio ou se o modelo não conseguir estruturar (ex: texto não parece
    ser uma rubrica).
    """
    if not texto_rubrica or not texto_rubrica.strip():
        raise ValueError("Texto da rubrica está vazio — não há o que estruturar.")

    resultado = gerar_json(system_prompt=SYSTEM_PROMPT, user_prompt=f"Texto da rubrica:\n\n{texto_rubrica}")

    if not resultado.get("criterios"):
        raise ValueError(
            "A IA não conseguiu identificar critérios de avaliação neste texto. "
            "Confira se o arquivo enviado é realmente a rubrica (e não a ficha em branco)."
        )
    return resultado
