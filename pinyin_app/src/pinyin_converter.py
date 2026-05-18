#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de conversión de tonos según reglas Hanyu Pinyin.
"""

import re
from typing import Optional

# Tabla de vocales con tonos (1..4). La vocal 'v' representa 'ü'.
TONES_MAP = {
    ('a', 1): 'ā', ('a', 2): 'á', ('a', 3): 'ǎ', ('a', 4): 'à',
    ('e', 1): 'ē', ('e', 2): 'é', ('e', 3): 'ě', ('e', 4): 'è',
    ('i', 1): 'ī', ('i', 2): 'í', ('i', 3): 'ǐ', ('i', 4): 'ì',
    ('o', 1): 'ō', ('o', 2): 'ó', ('o', 3): 'ǒ', ('o', 4): 'ò',
    ('u', 1): 'ū', ('u', 2): 'ú', ('u', 3): 'ǔ', ('u', 4): 'ù',
    ('v', 1): 'ǖ', ('v', 2): 'ǘ', ('v', 3): 'ǚ', ('v', 4): 'ǜ',  # ü
}

# Para preservar mayúsculas: convertir la vocal resultante si la original era mayúscula
def _apply_case(original_char: str, new_char: str) -> str:
    """Si original_char es mayúscula, devuelve new_char en mayúscula (si existe)."""
    if original_char.isupper():
        return new_char.upper()
    return new_char


def get_tone_target_index(syllable: str) -> Optional[int]:
    """
    Devuelve la posición (0-index) de la vocal que debe llevar el tono.
    Implementa las reglas oficiales de pinyin.
    """
    lower = syllable.lower()
    # 1. Buscar 'a'
    if 'a' in lower:
        return lower.index('a')
    # 2. Buscar 'o'
    if 'o' in lower:
        return lower.index('o')
    # 3. Buscar 'e'
    if 'e' in lower:
        return lower.index('e')
    # 4. Manejar 'iu' -> marca sobre 'u'
    if 'iu' in lower:
        idx = lower.find('iu')
        return idx + 1
    # 5. Manejar 'ui' -> marca sobre 'i'
    if 'ui' in lower:
        idx = lower.find('ui')
        return idx + 1
    # 6. Última vocal (i, u, v) de derecha a izquierda
    for i in range(len(lower)-1, -1, -1):
        if lower[i] in 'iuvü':
            return i
    return None  # No se encontró vocal


def apply_tone(syllable: str, tone_number: int) -> str:
    """
    Aplica el tono (1-5) a una sílaba pinyin (sin número).
    Devuelve la sílaba con la marca de tono o la misma sílaba si tone=5.
    Si no se puede aplicar, devuelve cadena vacía.
    """
    if tone_number < 1 or tone_number > 5:
        return ""
    if tone_number == 5:
        # Tono neutro: no se añade marca, la sílaba queda igual
        return syllable
    # Buscar la vocal que debe llevar el tono
    idx = get_tone_target_index(syllable)
    if idx is None:
        return ""   # No hay vocal válida
    original_vowel = syllable[idx]
    # Normalizar 'ü' (v) y minúscula para buscar en la tabla
    vowel_key = original_vowel.lower()
    if vowel_key == 'ü':
        vowel_key = 'v'
    if vowel_key == 'ü':
        vowel_key = 'v'
    if vowel_key == 'v':
        lookup_key = 'v'
    else:
        lookup_key = vowel_key
    # Obtener carácter con tono
    tone_char = TONES_MAP.get((lookup_key, tone_number))
    if tone_char is None:
        return ""
    # Preservar mayúscula/minúscula
    tone_char = _apply_case(original_vowel, tone_char)
    # Reconstruir la sílaba
    return syllable[:idx] + tone_char + syllable[idx+1:]


def convert_pinyin_token(token: str) -> str:
    """
    Convierte un token del tipo 'ni3' en 'nǐ'.
    El token puede contener letras [a-z v V] seguido de un dígito 1-5.
    Devuelve el token convertido o el original si no coincide.
    """
    # Patrón: letras (incluyendo v) + dígito 1-5 al final
    match = re.fullmatch(r'([a-zA-ZvVüÜ]+)([1-5])', token)
    if not match:
        return token
    syllable, tone_digit = match.groups()
    tone = int(tone_digit)
    converted = apply_tone(syllable, tone)
    if converted and converted != syllable:
        return converted
    return token  # fallback

# Opcional: validación de sílaba plausible (para evitar conversiones no deseadas)
PINYIN_VOWELS = set('aeiouvüAEIOUVÜ')

def has_vowel(s: str) -> bool:
    return any(ch in PINYIN_VOWELS for ch in s)
