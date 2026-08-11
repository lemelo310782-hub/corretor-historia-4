"""
Camada de abstração sobre o provedor de IA.

Usada nesta fase para interpretar/estruturar a rubrica e a ficha modelo.
Na Fase 3 será reaproveitada pelo motor de correção.

Por que essa camada existe: o restante da aplicação nunca importa o SDK
da Anthropic diretamente — só chama `gerar_json(...)`. Trocar de provedor
no futuro significa reescrever só este arquivo.
"""
import json

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, AI_PROVIDER

_cliente = None


class IAIndisponivelError(RuntimeError):
    """Lançado quando a chave de API não está configurada."""
    pass


def _get_cliente():
    global _cliente
    if _cliente is None:
        if not ANTHROPIC_API_KEY:
            raise IAIndisponivelError(
                "ANTHROPIC_API_KEY não configurada. Defina essa variável de ambiente para "
                "habilitar a interpretação automática de rubricas/fichas e, na Fase 3, a "
                "correção por IA. Sem ela, o texto continua sendo extraído normalmente — "
                "só a estruturação automática fica indisponível."
            )
        from anthropic import Anthropic
        _cliente = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _cliente


def gerar_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict:
    """
    Chama o modelo de linguagem configurado e espera uma resposta em JSON puro.

    Lança ValueError (com a resposta bruta) se o modelo não devolver JSON
    válido — melhor falhar de forma visível do que salvar lixo no banco.
    """
    if AI_PROVIDER != "anthropic":
        raise NotImplementedError(f"Provedor de IA '{AI_PROVIDER}' ainda não implementado.")

    cliente = _get_cliente()
    resposta = cliente.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    texto = "".join(bloco.text for bloco in resposta.content if bloco.type == "text").strip()
    texto_limpo = texto.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"O modelo não retornou um JSON válido ({e}). Início da resposta bruta: "
            f"{texto[:300]!r}"
        )
