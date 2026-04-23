from rag.vectordb import query_similar


def retrieve_for_symbol(symbol: str, language: str = "") -> list[dict]:
    query = f"{language} {symbol} function class implementation".strip()
    return query_similar(query)


def retrieve_context(analysis: dict) -> dict[str, list[dict]]:
    public_api = analysis.get("public_api", [])
    language = analysis.get("language", "")
    context: dict[str, list[dict]] = {}
    for symbol in public_api[:15]:
        context[symbol] = retrieve_for_symbol(symbol, language)
    return context