from re import sub, compile

ni = compile('[a-zA-Z]{2}(?:\s*\d\s*){6}[a-zA-Z]?')
phone = compile('(((\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3})|((\+44\s?\d{3}|\(?0\d{3}\)?)\s?\d{3}\s?\d{4})|((\+44\s?\d{2}|\(?0\d{2}\)?)\s?\d{4}\s?\d{4}))(\s?\#(\d{4}|\d{3}))?')


def pii_remover(
        x, 
        replace = '[PII Removed]', 
        ni = ni,
        phone = phone
        ):

    
    if phone:
        x = sub(phone, replace, x)

    if ni:
        x = sub(ni, replace, x)
    print(x)
    
    return x
