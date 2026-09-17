# sylphonetic.py
# Roman (phonetic) -> Sylheti written in Bangla script.
#
# Sylheti Roman spelling is not standardised (vase / bhashe / vashe are the
# same word), and Roman cannot express the contrasts Bangla script keeps
# (t = ত or ট, d = দ or ড, r = র or ড়). So this module does not try to decide
# those from the letters alone. It works in two layers:
#
#   1. LEXICON (primary). Every word of a Sylheti-in-Bangla-script corpus is
#      indexed under a deliberately blurry "sound key". The user's Roman word is
#      reduced to the same key and looked up, so spelling variants collapse onto
#      one entry.
#   2. RULES (fallback). Words the lexicon has never seen are parsed with an
#      ordered longest-match table. Ambiguous letters take their most frequent
#      value; the result is a guess and is reported as one.
#
# Command line:
#   python sylphonetic.py build corpus.txt lexicon.json   # one sentence per line
#   python sylphonetic.py try "apne bala asoin ni"
import json
import os
import re
import sys
import unicodedata
from collections import Counter

# The three nukta letters. NFC turns each precomposed form into base + nukta
# (they are composition exclusions), so both shapes must be handled explicitly.
RRA, RHA, YYA = "\u09DC", "\u09DD", "\u09DF"          # ড় ঢ় য়
NUKTA = "\u09BC"
_NUKTA_FOLD = (("\u09A1" + NUKTA, RRA), ("\u09A2" + NUKTA, RHA), ("\u09AF" + NUKTA, YYA))


def _normalise_bn(text):
    """NFC, then fold ড+় / ঢ+় / য+় back to single code points."""
    text = unicodedata.normalize("NFC", text)
    for decomposed, single in _NUKTA_FOLD:
        text = text.replace(decomposed, single)
    return text


# --------------------------------------------------------------------------
# 1. Sound key: run over BOTH sides so variants meet in the middle
# --------------------------------------------------------------------------
# Merged on purpose:
#   aspiration      kh gh ch jh th dh ph bh  ->  k g c j t d p b
#   dental/retro    ত ট / দ ড / ন ণ         ->  t / d / n
#   sibilants       শ ষ স চ ছ                ->  s
#   r-family        র ড় ঢ়                    ->  r
#   vowel length    ই ঈ / উ ঊ                ->  i / u
_BN_KEY = {
    "ক": "k", "খ": "k", "গ": "g", "ঘ": "g", "ঙ": "ng",
    "চ": "s", "ছ": "s", "জ": "j", "ঝ": "j", "ঞ": "n",
    "ট": "t", "ঠ": "t", "ড": "d", "ঢ": "d", "ণ": "n",
    "ত": "t", "থ": "t", "দ": "d", "ধ": "d", "ন": "n",
    "প": "p", "ফ": "p", "ব": "b", "ভ": "b", "ম": "m",
    "য": "j", "র": "r", "ল": "l", "শ": "s", "ষ": "s", "স": "s", "হ": "h",
    RRA: "r", RHA: "r", YYA: "e", "ৎ": "t", "ং": "ng", "ঁ": "",
    "অ": "o", "আ": "a", "ই": "i", "ঈ": "i", "উ": "u", "ঊ": "u", "ঋ": "ri",
    "এ": "e", "ঐ": "oi", "ও": "o", "ঔ": "ou",
    "া": "a", "ি": "i", "ী": "i", "ু": "u", "ূ": "u", "ৃ": "ri",
    "ে": "e", "ৈ": "oi", "ো": "o", "ৌ": "ou", "্": "", NUKTA: "",
}

# Longest first. Digraphs must be tried before their first letter.
_RM_KEY = [
    ("chh", "s"), ("sh", "s"), ("ss", "s"), ("ch", "s"), ("kh", "k"), ("gh", "g"),
    ("jh", "j"), ("zh", "j"), ("th", "t"), ("dh", "d"), ("ph", "p"), ("bh", "b"),
    ("ng", "ng"), ("rh", "r"), ("oi", "oi"), ("oy", "oi"), ("ou", "ou"), ("ow", "ou"),
    ("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u"),
    ("c", "s"), ("s", "s"), ("x", "k"), ("k", "k"), ("q", "k"), ("g", "g"),
    ("j", "j"), ("z", "j"), ("t", "t"), ("d", "d"), ("n", "n"), ("p", "p"),
    ("f", "p"), ("b", "b"), ("v", "b"), ("m", "m"), ("r", "r"), ("l", "l"),
    ("h", "h"), ("y", "i"), ("w", "o"),
    ("a", "a"), ("i", "i"), ("u", "u"), ("e", "e"), ("o", "o"),
]

_DUP = re.compile(r"(.)\1+")


def _squeeze(key):
    key = _DUP.sub(r"\1", key)          # dhullok -> dhulok
    key = key.replace("o", "")           # nagri == নাগরি (nagori), kor == kore
    return key or "o"


def _relax(key):
    """Merge the vowel pairs Roman spellers confuse most (i/e, u/a)."""
    return key.replace("e", "i").replace("u", "a")


def bn_key(word):
    """Sound key for a Sylheti word already written in Bangla script."""
    # The inherent vowel is not inserted here: _squeeze deletes every "o"
    # anyway, so কর and kor already meet as "kr".
    return _squeeze("".join(_BN_KEY.get(ch, "") for ch in _normalise_bn(word)))


def rm_key(word):
    """Sound key for a Roman (phonetic) word."""
    word, out, i = word.lower(), [], 0
    while i < len(word):
        for src, dst in _RM_KEY:
            if word.startswith(src, i):
                out.append(dst)
                i += len(src)
                break
        else:
            i += 1                       # drop anything unknown
    return _squeeze("".join(out))


# --------------------------------------------------------------------------
# 2. Lexicon
# --------------------------------------------------------------------------
_WORD = re.compile(r"[\u0980-\u09FF]+")


def build_lexicon(sentences):
    """
    Index a corpus of Sylheti-in-Bangla-script sentences.

    Returns {sound_key: word}. When several words share a key the most frequent
    one wins. Exact keys and relaxed (vowel-merged) keys are counted in separate
    tables, and an exact key always beats a relaxed one, so a fuzzy match from
    one word can never overwrite another word's exact match.
    """
    exact, relaxed = {}, {}
    for sentence in sentences:
        for word in _WORD.findall(_normalise_bn(sentence)):
            key = bn_key(word)
            if not key or key == "o":
                continue
            exact.setdefault(key, Counter())[word] += 1
            loose = _relax(key)
            if loose != key:
                relaxed.setdefault(loose, Counter())[word] += 1

    lexicon = {k: b.most_common(1)[0][0] for k, b in relaxed.items()}
    lexicon.update({k: b.most_common(1)[0][0] for k, b in exact.items()})
    return lexicon


def save_lexicon(lexicon, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(lexicon, handle, ensure_ascii=False, sort_keys=True)


def load_lexicon(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def lookup(key, lexicon):
    """Exact key first, then progressively looser vowel merges."""
    for candidate in (key, key.replace("e", "i"), key.replace("u", "a"), _relax(key)):
        hit = lexicon.get(candidate)
        if hit:
            return hit
    return None


# --------------------------------------------------------------------------
# 3. Rule fallback for words the lexicon has never seen
# --------------------------------------------------------------------------
# Ambiguous Roman letters take their most common value. To force a retroflex
# inside a word, use the Avro convention: capital T D N R S (baRi -> বাড়ি).
_ONSET = [
    ("chh", "ছ"), ("ch", "চ"), ("sh", "স"), ("kh", "খ"), ("gh", "ঘ"), ("jh", "ঝ"),
    ("zh", "ঝ"), ("Th", "ঠ"), ("th", "থ"), ("Dh", "ঢ"), ("dh", "ধ"), ("ph", "ফ"),
    ("bh", "ভ"), ("ng", "ং"), ("rh", RRA), ("R", RRA), ("T", "ট"), ("D", "ড"),
    ("N", "ণ"), ("S", "শ"), ("k", "ক"), ("x", "খ"), ("q", "ক"), ("g", "গ"),
    ("c", "চ"), ("j", "জ"), ("z", "জ"), ("t", "ত"), ("d", "দ"), ("n", "ন"),
    ("p", "প"), ("f", "ফ"), ("b", "ব"), ("v", "ভ"), ("m", "ম"), ("r", "র"),
    ("l", "ল"), ("s", "স"), ("h", "হ"), ("w", "ও"),
]
_VOWEL = [
    # Sylheti in Bangla script writes these as two vowels, not ঐ/ঔ:
    # oilo -> অইলো, asoin -> আছইন, bout -> বউত, boi -> বই.
    ("oi", ("অই", "ই")), ("oy", ("অই", "ই")), ("ou", ("অউ", "উ")), ("ow", ("অউ", "উ")),
    ("aa", ("আ", "া")), ("ee", ("ই", "ি")), ("ii", ("ই", "ি")),
    ("oo", ("উ", "ু")), ("uu", ("উ", "ু")),
    ("a", ("আ", "া")), ("i", ("ই", "ি")), ("u", ("উ", "ু")),
    ("e", ("এ", "ে")), ("o", ("অ", "")),        # o after a consonant = inherent
]
# Letters that never take a hasant before the next consonant.
_NO_JOIN = {"ং", YYA, "ও"}


def _fold_case(word):
    """
    Capitals mean retroflex, but phone keyboards capitalise the first letter of
    a sentence. A Title-case word (Ami, Tumi) is treated as lower case; a capital
    anywhere else (baRi, DhaKa) is kept as a deliberate retroflex.
    """
    if len(word) > 1 and word[0].isupper() and word[1:].islower():
        return word[0].lower() + word[1:]
    return word


def rule_parse(word):
    word = _fold_case(word)
    out, i = [], 0
    prev = None            # "c" after a joinable consonant, "v" after a vowel, None at start
    while i < len(word):
        # y is a glide: য় between vowels, a vowel sign after a consonant,
        # ই at the start of a word.
        # ("oy" never reaches this branch: the vowel table consumes it first.)
        if word[i] in "yY":
            nxt_is_vowel = i + 1 < len(word) and word[i + 1].lower() in "aeiou"
            at_end = i + 1 == len(word)
            if prev == "v" and (nxt_is_vowel or at_end):
                out.append(YYA)
                prev = "y"
            elif prev == "c":
                out.append("ি")
                prev = "v"
            else:
                out.append("ই")
                prev = "v"
            i += 1
            continue

        for src, forms in _VOWEL:
            if word.startswith(src, i):
                if src == "o" and prev in ("c", "y") and i + 1 == len(word):
                    # Word-final o is written: bhalo -> ভালো, koro -> করো.
                    # Mid-word o stays the unwritten inherent vowel: kor -> কর.
                    out.append("ো")
                else:
                    out.append(forms[1] if prev in ("c", "y") else forms[0])
                i += len(src)
                prev = "v"
                break
        else:
            for src, letter in _ONSET:
                if word.startswith(src, i):
                    if prev == "c":
                        out.append("্")
                    out.append(letter)
                    i += len(src)
                    prev = "y" if letter in _NO_JOIN else "c"
                    break
            else:
                out.append(word[i])
                i += 1
                prev = None
    return "".join(out)


# --------------------------------------------------------------------------
# 4. Public entry point
# --------------------------------------------------------------------------
_LATIN_WORD = re.compile(r"[A-Za-z]+")
_BANGLA_CHAR = re.compile(r"[\u0980-\u09FF]")
_SKIP = re.compile(r"https?://|www\.|@|\d")
_SPACE = re.compile(r"(\s+)")
# {Facebook} keeps an English word as it is; the braces are removed.
_ESCAPE = re.compile(r"\{([^{}\n]*)\}")


def _outside_escapes(text):
    """Yield (is_escaped, segment) pairs in order."""
    pos = 0
    for match in _ESCAPE.finditer(text):
        if match.start() > pos:
            yield False, text[pos:match.start()]
        yield True, match.group(1)
        pos = match.end()
    if pos < len(text):
        yield False, text[pos:]


def parse(text, lexicon=None, mark_guesses=False):
    """
    Convert the Roman parts of `text` to Sylheti in Bangla script.

    Code-mixed input is fine: anything already in Bangla or Nagri script is left
    untouched, and so is any token that looks like a URL, e-mail address or
    number, and anything inside {braces}. Whitespace is preserved exactly.

    With mark_guesses=True returns (result, misses), where misses is the list of
    Roman words that were not in the lexicon and went through the rule fallback.
    """
    lexicon = lexicon or {}
    misses = []

    def one(match):
        word = match.group(0)
        hit = lookup(rm_key(word), lexicon)
        if hit:
            return hit
        misses.append(word)
        return rule_parse(word)

    pieces = []
    for escaped, segment in _outside_escapes(text):
        if escaped:
            pieces.append(segment)
            continue
        for chunk in _SPACE.split(segment):
            if not chunk or chunk.isspace() or _SKIP.search(chunk):
                pieces.append(chunk)
            else:
                pieces.append(_LATIN_WORD.sub(one, chunk))
    result = "".join(pieces)

    return (result, misses) if mark_guesses else result


def has_latin(text):
    return bool(_LATIN_WORD.search(text or ""))


def detect(text):
    """
    What kind of input this is, judged only on the parts parse() would touch.

      "bangla"   : no English letters to convert (URLs, numbers, {escapes} ignored)
      "phonetic" : English letters only
      "mixed"    : Bangla script and English letters together
    """
    has_roman = has_bangla = False
    for escaped, segment in _outside_escapes(text or ""):
        if escaped:
            continue
        for chunk in _SPACE.split(segment):
            if not chunk or chunk.isspace():
                continue
            if _BANGLA_CHAR.search(chunk):
                has_bangla = True
            if not _SKIP.search(chunk) and _LATIN_WORD.search(chunk):
                has_roman = True
    if not has_roman:
        return "bangla"
    return "mixed" if has_bangla else "phonetic"


# --------------------------------------------------------------------------
# 5. Lexicon loading for the web app
# --------------------------------------------------------------------------
# Words that are already spelled in this app's own example sentences. This is a
# floor, not a lexicon: real coverage comes from building lexicon.json out of a
# proper Sylheti corpus with `python sylphonetic.py build`.
SEED_SENTENCES = [
    "সিলেটি নাগরী অইলো বউত পুরানা হরফ।",
    "আসসালামু আলাইকুম, আফনে ভালা আছইন নি? বাড়ির হকল ভালা আছইন নি?",
]


def load_app_lexicon(base_dir):
    """
    lexicon.json in base_dir if present, otherwise the seed sentences.
    Returns (lexicon, source_label).
    """
    path = os.path.join(base_dir, "lexicon.json")
    seed = build_lexicon(SEED_SENTENCES)
    if os.path.isfile(path):
        try:
            loaded = load_lexicon(path)
            seed.update(loaded)          # the corpus wins over the seed
            return seed, "lexicon.json"
        except (OSError, ValueError):
            pass
    return seed, "seed"


def _cli(argv):
    if len(argv) == 4 and argv[1] == "build":
        with open(argv[2], encoding="utf-8") as handle:
            lexicon = build_lexicon(handle)
        save_lexicon(lexicon, argv[3])
        print(f"Wrote {len(lexicon)} keys to {argv[3]}")
        return 0
    if len(argv) >= 3 and argv[1] == "try":
        here = os.path.dirname(os.path.abspath(__file__))
        lexicon, source = load_app_lexicon(here)
        result, misses = parse(" ".join(argv[2:]), lexicon, mark_guesses=True)
        print(result)
        print(f"lexicon: {source}, guessed: {misses or 'none'}")
        return 0
    print(__doc__ or "", "\nusage:\n  python sylphonetic.py build corpus.txt lexicon.json\n"
          "  python sylphonetic.py try \"apne bala asoin ni\"")
    return 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))