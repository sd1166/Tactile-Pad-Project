BRAILLE_MAP = {
    # Letters
    'a': '100000',
    'b': '110000',
    'c': '100100',
    'd': '100110',
    'e': '100010',
    'f': '110100',
    'g': '110110',
    'h': '110010',
    'i': '010100',
    'j': '010110',
    'k': '101000',
    'l': '111000',
    'm': '101100',
    'n': '101110',
    'o': '101010',
    'p': '111100',
    'q': '111110',
    'r': '111010',
    's': '011100',
    't': '011110',
    'u': '101001',
    'v': '111001',
    'w': '010111',
    'x': '101101',
    'y': '101111',
    'z': '101011',

    # Space
    ' ': '000000',

    # Punctuation
    ',': '010000',   # comma
    ';': '011000',   # semicolon
    ':': '010010',   # colon
    '.': '010011',   # period / decimal point
    '!': '011010',   # exclamation
    '?': '011001',   # question mark
    "'": '001000',   # apostrophe
    '-': '001001',   # hyphen
    '/': '001100',   # slash / fraction line

    # Quotes
    '"': '011011',   # generic quote
    '“': '011011',   # open quote
    '”': '011011',   # close quote
    '‘': '001000',   # open single quote (often same as apostrophe in simple systems)
    '’': '001000',   # close single quote / apostrophe

    # Brackets / parentheses
    '(': '011011',
    ')': '011011',
    '[': '011011',
    ']': '011011',
    '{': '011011',
    '}': '011011',
}

# Digits in Braille use the same cells as a-j, but must be preceded by the number sign.
DIGIT_TO_BRAILLE = {
    '1': BRAILLE_MAP['a'],
    '2': BRAILLE_MAP['b'],
    '3': BRAILLE_MAP['c'],
    '4': BRAILLE_MAP['d'],
    '5': BRAILLE_MAP['e'],
    '6': BRAILLE_MAP['f'],
    '7': BRAILLE_MAP['g'],
    '8': BRAILLE_MAP['h'],
    '9': BRAILLE_MAP['i'],
    '0': BRAILLE_MAP['j'],
}

# Indicators
CAPITAL_SIGN = '000001'   # dot 6
NUMBER_SIGN = '001111'    # dots 3-4-5-6


def is_letter(ch: str) -> bool:
    return ch.isalpha() and ch.lower() in BRAILLE_MAP


def is_digit(ch: str) -> bool:
    return ch in DIGIT_TO_BRAILLE


def is_number_continuation_char(ch: str) -> bool:
    """
    Characters that can continue a numeric sequence without leaving numeric mode.
    Adjust this based on your preferred Braille rules.
    """
    return ch.isdigit() or ch in {'.', ',', '/', '-'}


def translate_text(text: str):
    """
    Translate plain text into Braille cell patterns.

    Output format:
    [
        {"char": "A", "pattern": "000001", "type": "indicator", "meaning": "capital"},
        {"char": "a", "pattern": "100000", "type": "letter"},
        ...
    ]
    """
    patterns = []
    numeric_mode = False

    for ch in text:
        # Space always ends numeric mode
        if ch == ' ':
            patterns.append({
                "char": ch,
                "pattern": BRAILLE_MAP[' '],
                "type": "space"
            })
            numeric_mode = False
            continue

        # Capital letters: prepend capital sign
        if is_letter(ch) and ch.isupper():
            patterns.append({
                "char": ch,
                "pattern": CAPITAL_SIGN,
                "type": "indicator",
                "meaning": "capital"
            })
            patterns.append({
                "char": ch.lower(),
                "pattern": BRAILLE_MAP[ch.lower()],
                "type": "letter"
            })
            numeric_mode = False
            continue

        # Lowercase letters
        if is_letter(ch):
            patterns.append({
                "char": ch,
                "pattern": BRAILLE_MAP[ch.lower()],
                "type": "letter"
            })
            numeric_mode = False
            continue

        # Digits: prepend number sign only when entering numeric mode
        if is_digit(ch):
            if not numeric_mode:
                patterns.append({
                    "char": '#',
                    "pattern": NUMBER_SIGN,
                    "type": "indicator",
                    "meaning": "number"
                })
                numeric_mode = True

            patterns.append({
                "char": ch,
                "pattern": DIGIT_TO_BRAILLE[ch],
                "type": "digit"
            })
            continue

        # Punctuation
        if ch in BRAILLE_MAP:
            patterns.append({
                "char": ch,
                "pattern": BRAILLE_MAP[ch],
                "type": "punctuation"
            })

            # keep or exit numeric mode depending on punctuation
            if ch not in {'.', ',', '/', '-'}:
                numeric_mode = False

            continue

        # Unknown character fallback
        patterns.append({
            "char": ch,
            "pattern": '000000',
            "type": "unknown"
        })
        numeric_mode = False

    return patterns


if __name__ == "__main__":
    sample = 'Hello, World! "Braille" 123 45.67 / (test)'
    result = translate_text(sample)

    for item in result:
        extra = f" ({item['meaning']})" if "meaning" in item else ""
        print(f"{item['char']!r}: {item['pattern']} [{item['type']}{extra}]")