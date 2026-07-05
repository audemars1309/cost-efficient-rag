# wraps anthropic or openai depending on LLM_PROVIDER
from src.config import CFG


def _call_anthropic(system: str, user: str, max_tokens: int = 1024):
    import anthropic
    client = anthropic.Anthropic(api_key=CFG.anthropic_api_key)
    resp = client.messages.create(
        model=CFG.llm_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    return text, usage


def _call_openai(system: str, user: str, max_tokens: int = 1024):
    from openai import OpenAI
    client = OpenAI(api_key=CFG.openai_api_key)
    resp = client.chat.completions.create(
        model=CFG.llm_model,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    text = resp.choices[0].message.content
    usage = {
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
    }
    return text, usage


def complete(system: str, user: str, max_tokens: int = 1024):
    if CFG.llm_provider == "anthropic":
        return _call_anthropic(system, user, max_tokens)
    elif CFG.llm_provider == "openai":
        return _call_openai(system, user, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {CFG.llm_provider}")
