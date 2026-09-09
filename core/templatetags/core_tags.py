from django import template
import re

register = template.Library()


@register.filter
def cnpj_format(value):
    if not value:
        return ""
    v = re.sub(r"[^0-9a-zA-Z]", "", str(value))
    if len(v) == 14:
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
    return value


@register.filter
def cep_format(value):
    if not value:
        return ""
    v = re.sub(r"[^0-9a-zA-Z]", "", str(value))
    if len(v) == 8:
        return f"{v[:5]}-{v[5:]}"
    return value


# a smart title case filter that handles pt-BR words and keeps them lowercase, also keep a list of full uppercase words that should remain uppercase (like acronyms)
@register.filter
def smart_title(value):
    trivial_words = {
        # Articles
        "o",
        "a",
        "os",
        "as",
        "um",
        "uma",
        "uns",
        "umas",
        # Prepositions & Contractions
        "de",
        "di",
        "do",
        "da",
        "dos",
        "das",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "por",
        "pelo",
        "pela",
        "pelos",
        "pelas",
        "para",
        "pra",
        "pro",
        "com",
        "sem",
        "sob",
        "sobre",
        # Conjunctions
        "e",
        "ou",
        "mas",
        "nem",
        "que",
        "como",
    }
    uppercase_words = {
        "CPF",
        "CNPJ",
        "MEI",
        "LTDA",
        "S/A",
        "EIRELI",
        "IPTU",
        "IPVA",
        "ISS",
        "ICMS",
        "PIS",
        "COFINS",
    }
    if not value:
        return ""
    words = value.split()
    result = []
    for i, word in enumerate(words):
        if word.upper() in uppercase_words:
            result.append(word.upper())
        elif i == 0 or i == len(words) - 1 or word.lower() not in trivial_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return " ".join(result)


# a filter that receives a logradouro type and returns its abbreviation, if it is a known type, otherwise returns the original value
@register.filter
def logradouro_type_abbr(value):
    lower_value = value.lower() if value else ""
    abbr_map = {
        "avenida": "Av.",
        "rua": "R.",
        "travessa": "Tv.",
        "praça": "Pç.",
        "alameda": "Al.",
        "rodovia": "Rod.",
        "estrada": "Est.",
        "largo": "Lg.",
        "viela": "Vl.",
        "beco": "Bc.",
        "parque": "Pq.",
        "jardim": "Jd.",
    }
    return abbr_map.get(lower_value, value)
