def collapse_deduplicate_symbols_json(records: list[dict]) -> list[dict]:
    """
    Deduplicate a list of symbol dicts based on 'symbol'.
    Keeps the last occurrence of each symbol.
    """
    unique_map = {}
    for r in records:
        symbol = r.get("symbol")
        if not symbol:
            continue  # skip empty symbols
        unique_map[symbol] = r  # last occurrence wins
    return list(unique_map.values())
