from re import sub, compile

ni = compile('[a-zA-Z]{2}(?:\s*\d\s*){6}[a-zA-Z]?')
phone = compile('(((\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3})|((\+44\s?\d{3}|\(?0\d{3}\)?)\s?\d{3}\s?\d{4})|((\+44\s?\d{2}|\(?0\d{2}\)?)\s?\d{4}\s?\d{4}))(\s?\#(\d{4}|\d{3}))?')
vrp = compile('((?:[a-zA-Z]{2}\s?[0-9]{2}\s?[a-zA-Z]{3})|(?:[a-zA-Z]{3}\s?\d{4}))')
passports = compile('[0-9]{9,10}GBR[0-9]{7}[U,M,F]{1}[0-9]{7}')
dates = compile('((?:\d{1,2})(?:rd|nd|th)?([\/\.\-\ ])((?:[0-9]{1,2})|(?:\D{3})|(?:January|February|March|April|May|June|July|August|Septeber|October|November|December))(?:[\/\.\-\ ])\d{2,4})')
digits = compile('\d')

def pii_remover(
        x, 
        replace = '[PII Removed]', 
        ni = ni,
        phone = phone,
        vrp = vrp,
        passports = passports,
        dates = dates,
        digits = digits
        ):

    '''
    Find most common forms of PII and replace with [PII Removed]
    Order is important in terms of what is searched for first.
    Matches can conflict, but any remaining nmatched digits are
    replaced with X.

    Sources:

    Passports: http://regexlib.com/REDetails.aspx?regexp_id=2390
    NHS and short passport numbers will be caught be credit cards regex.

    '''

    if passports:
        x = sub(passports, replace, x)
    
    if dates:
        x = sub(dates, replace, x)
    
    if phone:
        x = sub(phone, replace, x)

    if ni:
        x = sub(ni, replace, x)

    if vrp:
        x = sub(vrp, replace, x)

    # Enforce catch-all for all remaining digits

    x = sub(digits, 'X', x)

    return x
