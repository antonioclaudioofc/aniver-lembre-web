def pagination_range(current, total, window=2):
    if total <= 1:
        return []

    pages = {1, total}
    for p in range(current - window, current + window + 1):
        if 1 <= p <= total:
            pages.add(p)

    result = []
    prev = None
    for p in sorted(pages):
        if prev is not None and p - prev > 1:
            result.append(None)
        result.append(p)
        prev = p
    return result
