"""
Identifica os campos (perguntas/seções) de uma ficha de análise de fonte
histórica em branco — ex: campos de um formulário OPCVL (Origem, Propósito,
Conteúdo, Valor, Limitação) mais identificação do aluno.

Isso permite, na Fase 3, segmentar o texto que o aluno escreveu por campo
e comparar cada resposta com o critério correspondente da rubrica, em vez
de jogar a ficha inteira contra a rubrica inteira de uma vez.
"""
from app.services.ai_provider import gerar_json

SYSTEM_PROMPT = """Você identifica os campos de uma ficha (formulário) de análise de fonte
histórica que está em branco, preenchida por um professor de História para os alunos usarem.

Leia o texto extraído da ficha modelo e identifique cada campo/pergunta que o aluno deve
preencher, na ordem em que aparecem.

Regras:
- Ignore campos puramente administrativos que não fazem parte da análise (ex: "Data", "Turma")
  a não ser que sejam pedidos explicitamente — inclua-os mas marque `tipo` como "identificacao".
- Para os campos de análise histórica (ex: Origem, Propósito, Conteúdo, Valor, Limitação, ou
  qualquer outra estrutura usada na ficha), marque `tipo` como "analise".
- Preserve o texto exato da pergunta/rótulo do campo.

Responda APENAS com um JSON neste formato:
{
  "campos": [
    {"nome": "Nome do aluno", "tipo": "identificacao"},
    {"nome": "Origem da fonte", "tipo": "analise"}
  ]
}"""


def identificar_campos(texto_ficha: str) -> dict:
    if not texto_ficha or not texto_ficha.strip():
        raise ValueError("Texto da ficha modelo está vazio — não há campos a identificar.")

    resultado = gerar_json(system_prompt=SYSTEM_PROMPT, user_prompt=f"Texto da ficha modelo:\n\n{texto_ficha}")

    if not resultado.get("campos"):
        raise ValueError(
            "A IA não conseguiu identificar campos nesta ficha. Confira se o arquivo enviado "
            "é realmente o modelo em branco (e não uma ficha já preenchida)."
        )
    return resultado
