from re import sub, compile

ni = compile('[a-zA-Z]{2}(?:\s*\d\s*){6}[a-zA-Z]?')
phone = compile('(((\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3})|((\+44\s?\d{3}|\(?0\d{3}\)?)\s?\d{3}\s?\d{4})|((\+44\s?\d{2}|\(?0\d{2}\)?)\s?\d{4}\s?\d{4}))(\s?\#(\d{4}|\d{3}))?')
number_plates = compile('((?:[a-zA-Z]{2}\s?[0-9]{2}\s?[a-zA-Z]{3})|(?:[a-zA-Z]{3}\s?\d{4}))')
credit_cards = compile('(?:\d[ -]*?){13,16}')

def pii_remover(
        x, 
        replace = '[PII Removed]', 
        ni = ni,
        phone = phone,
        number_plates = number_plates,
        credit_cards = credit_cards
        ):

    '''
    Find most common forms of PII and replace with [PII Removed]
    Order is important in terms of what is searched for first.
    '''

    if credit_cards:
        x = sub(credit_cards, replace, x)

    if phone:
        x = sub(phone, replace, x)

    if ni:
        x = sub(ni, replace, x)

    if number_plates:
        x = sub(number_plates, replace, x)

    return x
