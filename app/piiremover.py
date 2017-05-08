from re import sub


def pii_remover(
        x, 
        replace='[PII Removed]', 
        ni='[a-zA-Z]{2}(?:\s*\d\s*){6}[a-zA-Z]?'
        ):

    x = sub(ni, replace, x)
    return x
