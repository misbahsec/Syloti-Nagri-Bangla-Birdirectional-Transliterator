# transliterator.py
import re
import unicodedata

class SylhetiTransliterator:
    """
    Bidirectional transliterator between Bengali (Bangla) and Syloti Nagri script.
    Supports both bn->syl and syl->bn directions.
    """
    def __init__(self):
        # ---------- Forward mapping: Bengali -> Syloti (complex clusters) ----------
        self.juktoborno_map = [
            ('অ্যা', 'ꠄ'),
            ('ত্ম', 'ত্ত'),
            ('\u09DF\u09BF', '\u0987'),
            ('\u09DF\u09C0', '\u0987'),
            ('ক্ষ্ম', 'ꠇ꠆ꠇ'), ('ত্ত্ব', 'ꠔ꠆ꠔ'), ('চ্ছ্ব', 'ꠌ꠆ꠍ'), ('জ্জ্ব', 'ꠎ꠆ꠎ'),('জ্ব', 'ꠎ'),
            ('্র', '꠆ꠞ'), ('র্', 'ꠞ꠆'),('ঞ্জ', 'ꠘ꠆ꠎ'),('ঙ্গ', 'ꠋꠉ'), ('শ্ব','ꠡ'),('ঞ্চ', 'ꠘ꠆ꠌ'),
            ('ক্ক', 'ꠇ꠆ꠇ'), ('ক্ট', 'ꠇ꠆ꠐ'), ('ক্ত', 'ꠇ꠆ꠔ'), ('ক্ম', 'ꠇ꠆ꠝ'), ('ক্ল', 'ꠇ꠆ꠟ'),
            ('ক্ষ', 'ꠇ꠆ꠇ'), ('গ্ধ', 'ꠉ꠆ꠗ'), ('গ্ন', 'ꠉ꠆ꠘ'), ('গ্ম', 'ꠉ꠆ꠝ'), ('গ্ল', 'ꠉ꠆ꠟ'),
            ('ঘ্ন', 'ꠊ꠆ꠘ'), ('চ্চ', 'ꠌ꠆ꠌ'), ('চ্ছ', 'ꠌ꠆ꠍ'), ('জ্জ', 'ꠎ꠆ꠎ'), ('জ্ঝ', 'ꠎ꠆ꠏ'),
            ('জ্ঞ', 'ꠉ꠆ꠉ'), ('জ্ব', 'ꠎ'), ('ট্ট', 'ꠐ꠆ꠐ'), ('ট্ব', 'ꠐ꠆'), ('ট্ম', 'ꠐ꠆ꠝ'),
            ('ড্ড', 'ꠒ꠆ꠒ'), ('ণ্ট', 'ꠘ꠆ꠐ'), ('ণ্ঠ', 'ꠘ꠆ꠑ'), ('ণ্ড', 'ꠘ꠆ꠒ'), ('ত্ত', 'ꠔ꠆ꠔ'),
            ('ত্থ', 'ꠔ꠆ꠕ'), ('ত্ন', 'ꠔ꠆ꠘ'), ('ত্র', 'ꠔ꠆ꠞ'), ('ত্ব', 'ꠔ꠆ꠔ'),
            ('দ্দ', 'ꠖ꠆ꠖ'), ('দ্ধ', 'ꠖ꠆ꠗ'), ('দ্ব', 'ꠖ'), ('দ্ভি', 'ꠖ꠆ꠜꠤ'), ('দ্ভ', 'ꠖ꠆ꠜ'),
            ('দ্ম', 'ꠖ꠆ꠝ'), ('ধ্ন', 'ꠗ꠆ꠘ'), ('ধ্ব', 'ꠗ'), ('ন্ত', 'ꠘ꠆ꠔ'), ('ন্থ', 'ꠘ꠆ꠕ'),
            ('ন্দ', 'ꠘ꠆ꠖ'), ('ন্দ্ব', 'ꠘ꠆ꠖ'), ('ন্ধ', 'ꠘ꠆ꠗ'), ('ন্ন', 'ꠘ꠆ꠘ'), ('ন্ম', 'ꠘ꠆ꠝ'),
            ('প্ট', 'ꠙ꠆ꠐ'), ('প্ত', 'ꠙ꠆ꠔ'), ('প্ন', 'ꠙ꠆ꠘ'), ('প্প', 'ꠙ꠆ꠙ'), ('প্স', 'ꠙ꠆ꠡ'),
            ('ব্দ', 'ꠛ꠆ꠖ'), ('ব্ধ', 'ꠛ꠆ꠗ'), ('ব্ব', 'ꠛ꠆ꠛ'), ('ম্ন', 'ꠝ꠆ꠘ'), ('ম্প', 'ꠝ꠆ꠙ'),
            ('ম্ফ', 'ꠝ꠆ꠚ'), ('ম্ব', 'ꠝ꠆ꠛ'), ('ম্ভ', 'ꠝ꠆ꠜ'), ('ম্ম', 'ꠝ꠆ꠝ'), ('শ্চ', 'ꠡ꠆ꠌ'),
            ('শ্ছ', 'ꠡ꠆ꠍ'), ('শ্ন', 'ꠡ꠆ꠘ'), ('শ্ম', 'ꠡ꠆ꠝ'), ('শ্র', 'ꠡ꠆ꠞ'), ('শ্ল', 'ꠡ꠆ꠟ'),
            ('ষ্ক', 'ꠡ꠆ꠇ'), ('ষ্ক্র', 'ꠡ꠆ꠇ꠆ꠞ'), ('ষ্ট', 'ꠡ꠆ꠐ'), ('ষ্ঠ', 'ꠡ꠆ꠑ'), ('ষ্ণ', 'ꠡ꠆ꠘ'),
            ('ষ্প', 'ꠡ꠆ꠙ'), ('ষ্ফ', 'ꠡ꠆ꠚ'), ('স্ক', 'ꠡ꠆ꠇ'), ('স্খ', 'ꠡ꠆ꠈ'), ('স্ট', 'ꠡ꠆ꠐ'),
            ('স্ত', 'ꠡ꠆ꠔ'), ('স্থ', 'ꠡ꠆ꠕ'), ('স্ন', 'ꠡ꠆ꠘ'), ('স্প', 'ꠡ꠆ꠙ'), ('স্ফ', 'ꠡ꠆ꠚ'),
            ('স্ব', 'ꠡ'), ('স্ল', 'ꠡ꠆ꠟ'), ('হ্ণ', 'ꠢ꠆ꠘ'), ('হ্ন', 'ꠢ꠆ꠘ'), ('হ্ম', 'ꠢ꠆ꠝ'),
            ('হ্ল', 'ꠢ꠆ꠟ'), ('ৎ', 'ꠔ꠆'), ('ং', 'ꠋ'), ('ঁ', ''),('্যা', 'ꠦ')
        ]

        # Basic character mapping (Bengali -> Syloti)
        self.char_map = {
            'অ': 'ꠅ', 'আ': 'ꠀ', 'ই': 'ꠁ', 'ঈ': 'ꠁ', 'উ': 'ꠃ', 'ঊ': 'ꠃ', 'ঋ': 'ꠞꠤ',
            'এ': 'ꠄ', 'ঐ': 'ꠅꠁ', 'ও': 'ꠅ', 'ঔ': 'ꠅꠃ', 'া': 'ꠣ', 'ি': 'ꠤ', 'ী': 'ꠤ',
            'ু': 'ꠥ', 'ূ': 'ꠥ', 'ৃ': '꠆ꠞꠤ', 'ে': 'ꠦ', 'ৈ': 'ꠂ', 'ো': 'ꠧ', 'ৌ': 'ꠧꠃ',
            'ক': 'ꠇ', 'খ': 'ꠈ', 'গ': 'ꠉ', 'ঘ': 'ꠊ', 'ঙ': 'ꠋ', 'চ': 'ꠌ', 'ছ': 'ꠍ',
            'জ': 'ꠎ', 'ঝ': 'ꠏ', 'ঞ': '', 'ট': 'ꠐ', 'ঠ': 'ꠑ', 'ড': 'ꠒ', 'ঢ': 'ꠓ',
            'ণ': 'ꠘ', 'ত': 'ꠔ', 'থ': 'ꠕ', 'দ': 'ꠖ', 'ধ': 'ꠗ', 'ন': 'ꠘ', 'প': 'ꠙ',
            'ফ': 'ꠚ', 'ব': 'ꠛ', 'ভ': 'ꠜ', 'ম': 'ꠝ', 'য': 'ꠎ', 'র': 'ꠞ', 'ল': 'ꠟ',
            'শ': 'ꠡ', 'ষ': 'ꠡ', 'স': 'ꠡ', 'হ': 'ꠢ', 'ড়': 'ꠠ', 'ঢ়': 'ꠠ',
            'য়': 'ꠄ', '্': '꠆', '।': '।','়': ''
        }

        # Reverse (Syloti -> Bengali) tables are hand-built, NOT auto-inverted.
        self._build_reverse_maps()

    # ---------- Forward conversion: Bengali -> Syloti ----------
    def convert_bn_to_syl(self, text):
        """
        Convert a Bengali (Bangla) string to Syloti Nagri script.
        """
        if not isinstance(text, str):
            return ""
        text = unicodedata.normalize('NFC', text)

        # Pre-processing rules (as per original code)
        text = text.replace('\u094D\u09AF', '্য')
        text = text.replace('\u09AF\u09BC', '\u09DF')
        text = text.replace('ৃ', '꠆রি')

        words = text.split()
        phonetic_results = []
        for word in words:
            word = unicodedata.normalize('NFC', word)
            word = word.replace('\u09AF\u09BC', '\u09DF')
            word = word.replace('\u09C0\u09DF', 'ꠤꠅ')
            word = word.replace('্ল্যা', 'লে')
            word = word.replace('্র্যা', '্রে')

            # Duplicate consonant before '্ব' (except ম)
            word = re.sub(
                r'(?<=.)((?!\u09AE)[\u0995-\u09B9])\u09CD\u09AC',
                lambda m: m.group(1) + chr(0x09CD) + m.group(1),
                word
            )

            word = word.replace('\u09DF\u09BE', '\u0986')
            word = word.replace('\u09DF\u09C7', '\u098F')
            word = re.sub(r'^([\u0995-\u09B9])্য', r'\1ে', word)

            # Handle '্যফলা' (ya-phala) with vowel context
            def ya_phala_doubling(match):
                con = match.group(1)
                pos = match.start()
                prev = word[pos-1] if pos > 0 else ""
                if prev in ['ি', 'ই', 'ঈ']:
                    return f"{con}\u09CD{con}"
                return f"ই{con}\u09CD{con}"
            word = re.sub(r'([\u0995-\u09B9])্য', ya_phala_doubling, word)

            # Various 'য়' rules
            word = re.sub(r'\u09DF(?=[।\.,;!?\s]|$)', '\u098F', word)
            word = re.sub(r'\u09DF(?=[\u0995-\u09B9\u0982](?!\u09BE-\u09CC\u094D]))', '\u098F\u0993', word)
            word = re.sub(r'\u09DF(?=[ক-হ])', '\u098F', word)

            # Special clusters
            word = re.sub(r'^ক্ষ', 'খ', word)
            word = re.sub(r'^জ্ঞ', 'গিআ', word)

            phonetic_results.append(word)

        temp_text = " ".join(phonetic_results)

        # Apply complex cluster mapping (longest first; order in list matters)
        for bangla, syloti in self.juktoborno_map:
            temp_text = temp_text.replace(bangla, syloti)

        # Apply basic character mapping
        final_output = ""
        for char in temp_text:
            final_output += self.char_map.get(char, char)

        return final_output


    # ------------------------------------------------------------------ #
    # Reverse tables
    # ------------------------------------------------------------------ #
    def _build_reverse_maps(self):
        """
        Build Syloti -> Bengali tables.

        The forward map is lossy and phonetic (দ্ব/স্ব/ধ্ব/জ্ব all collapse to a
        single letter, ঈ/ই both become ꠁ, শ/ষ/স all become ꠡ, '্যা' becomes ꠦ...).
        Mechanically inverting it therefore produces nonsense like দ্বীআ for দিআ
        or ল্যাখো for লেখো. These tables instead pick the single most natural
        Bengali spelling for each Syloti glyph and let context + a small word
        list handle the rest.
        """

        # 1. Single characters. One canonical Bengali form per Syloti glyph.
        self.reverse_char_map = {
            'ꠀ': 'আ', 'ꠁ': 'ই', 'ꠂ': 'ৈ', 'ꠃ': 'উ', 'ꠄ': 'এ',
            'ꠇ': 'ক', 'ꠈ': 'খ', 'ꠉ': 'গ', 'ꠊ': 'ঘ', 'ꠋ': 'ং',
            'ꠌ': 'চ', 'ꠍ': 'ছ', 'ꠎ': 'জ', 'ꠏ': 'ঝ',
            'ꠐ': 'ট', 'ꠑ': 'ঠ', 'ꠓ': 'ঢ',
            'ꠔ': 'ত', 'ꠕ': 'থ', 'ꠖ': 'দ', 'ꠗ': 'ধ', 'ꠘ': 'ন',
            'ꠙ': 'প', 'ꠚ': 'ফ', 'ꠛ': 'ব', 'ꠜ': 'ভ', 'ꠝ': 'ম',
            'ꠞ': 'র', 'ꠟ': 'ল', 'ꠠ': 'ড়', 'ꠡ': 'স', 'ꠢ': 'হ',
            'ꠣ': 'া', 'ꠤ': 'ি', 'ꠥ': 'ু', 'ꠦ': 'ে', 'ꠧ': 'ো',
            '꠆': '্', '।': '।',
        }
        # 'ꠅ' and 'ꠒ' are resolved by position, see _apply_contextual_rules.

        # 2. Conjuncts whose natural Bengali spelling is not just
        #    letter + hasant + letter. Applied longest-first, before step 1.
        self.reverse_cluster_map = {
            'ꠧꠃ': 'ৌ',
            'ꠡ꠆ꠐ': 'ষ্ট', 'ꠡ꠆ꠑ': 'ষ্ঠ', 'ꠡ꠆ꠌ': 'শ্চ', 'ꠡ꠆ꠍ': 'শ্ছ',
            'ꠡ꠆ꠞ': 'শ্র', 'ꠡ꠆ꠝ': 'শ্ম',
            'ꠘ꠆ꠐ': 'ন্ট', 'ꠘ꠆ꠑ': 'ন্ঠ', 'ꠘ꠆ꠒ': 'ন্ড',
            'ꠘ꠆ꠎ': 'ঞ্জ', 'ꠘ꠆ꠌ': 'ঞ্চ',
        }

        # 3. Whole words the rules cannot get right, because the distinction
        #    (শ/স/ষ, জ/য, ই/ঈ, উ/ঊ, ন/ণ, ্র/ৃ, dropped ঁ) is erased going
        #    forward. Extend freely - keys are Syloti, values Bengali.
        self.reverse_word_map = {
            'ꠙ꠆ꠞꠎꠥꠇ꠆ꠔꠤ': 'প্রযুক্তি',
            'ꠛ꠆ꠞꠤꠡ꠆ꠐꠤ': 'বৃষ্টি',
            'ꠌꠦꠡ꠆ꠐꠣ': 'চেষ্টা',
            'ꠢꠥꠡꠤꠀꠞꠤ': 'হুশিআরি',
            'ꠈꠥꠡꠤ': 'খুশি',
            'ꠛꠦꠡꠤ': 'বেশি',
            'ꠡꠢꠞ': 'শহর',
            'ꠡꠛ꠆ꠖ': 'শব্দ',
            'ꠈꠣꠌꠣ': 'খাঁচা',
            'ꠇꠣꠞꠘ': 'কারণ',
            'ꠎꠤꠛꠘ': 'জীবন',
            'ꠛꠣꠒꠤ': 'বাড়ি',
            'ꠖꠥꠞ': 'দূর',
            'ꠎꠣꠅꠀ': 'যাওআ',
            'ꠎꠔ꠆ꠘ': 'যত্ন',
            'ꠎꠤꠉ꠆ꠘꠣꠡꠣ': 'জিগ্নাসা',
        }
        # Suffixes stripped before a word-map lookup, so প্রযুক্তি also covers
        # প্রযুক্তির / প্রযুক্তিত / প্রযুক্তিএ etc.
        self.reverse_suffixes = ('ꠞꠦ', 'ꠞ', 'ꠔ', 'ꠦ', 'ꠧ', 'ꠞꠣ', 'ꠉꠥꠘ', 'ꠁꠘ', 'ꠞꠔꠣꠝ')

        # Anything that is neither Syloti nor a letter is treated as a boundary.
        self._syl_word_re = re.compile(r'[\uA800-\uA82F\u0980-\u09FF]+')

    # ------------------------------------------------------------------ #
    # Reverse conversion: Syloti -> Bengali
    # ------------------------------------------------------------------ #
    @staticmethod
    def _apply_contextual_rules(word):
        """
        Position-sensitive glyphs, resolved before any table lookup.

        ꠅ  -> অ word-initially, ও elsewhere   (ꠅꠅꠀꠞ -> অওআর)
        ꠒ  -> ড word-initially or inside a conjunct, ড় elsewhere
              (ꠒꠣꠇꠦꠞ -> ডাকের, ꠝꠥꠒꠣꠔ -> মুড়াত, ꠑꠣꠘ꠆ꠒꠣ -> ঠান্ডা)
        """
        out = []
        for i, ch in enumerate(word):
            prev = word[i - 1] if i else ''
            nxt = word[i + 1] if i + 1 < len(word) else ''
            if ch == 'ꠅ':
                out.append('অ' if i == 0 else 'ও')
            elif ch == 'ꠒ':
                if i == 0 or prev == '꠆' or nxt == '꠆':
                    out.append('ড')
                else:
                    out.append('ড়')
            else:
                out.append(ch)
        return ''.join(out)

    def _reverse_word(self, word):
        """Convert one Syloti word to Bengali."""
        # a. exact word override
        if word in self.reverse_word_map:
            return self.reverse_word_map[word]

        # b. override on the stem, keeping the inflectional suffix
        for suf in sorted(self.reverse_suffixes, key=len, reverse=True):
            if word.endswith(suf):
                stem = word[: -len(suf)]
                if stem in self.reverse_word_map:
                    return self.reverse_word_map[stem] + self._reverse_word(suf)

        # c. contextual glyphs
        word = self._apply_contextual_rules(word)

        # d. conjunct table (longest first)
        for syl in sorted(self.reverse_cluster_map, key=len, reverse=True):
            if syl in word:
                word = word.replace(syl, self.reverse_cluster_map[syl])

        # e. single characters; unknown characters pass through untouched
        return ''.join(self.reverse_char_map.get(ch, ch) for ch in word)

    def convert_syl_to_bn(self, text):
        """Convert a Syloti Nagri string back to Bengali (Bangla) script."""
        if not isinstance(text, str):
            return ""
        text = unicodedata.normalize('NFC', text)
        return self._syl_word_re.sub(lambda m: self._reverse_word(m.group(0)), text)

    # ------------------------------------------------------------------ #
    # Unified interface
    # ------------------------------------------------------------------ #
    def convert(self, text, direction='bn_to_syl'):
        """direction: 'bn_to_syl' (default) or 'syl_to_bn'."""
        if direction == 'syl_to_bn':
            return self.convert_syl_to_bn(text)
        return self.convert_bn_to_syl(text)


# Backwards-compatible alias for the original class name.
SylhetiTranslitator = SylhetiTransliterator

SUPPORTED_DIRECTIONS = ("bn_to_syl", "syl_to_bn")

_engine = SylhetiTransliterator()


def get_engine():
    """Return the shared SylhetiTransliterator instance."""
    return _engine


def transliterate(text, direction="bn_to_syl"):
    """Convert `text` in the given `direction`. Raises ValueError on bad input."""
    if direction not in SUPPORTED_DIRECTIONS:
        raise ValueError(
            f"Unknown direction {direction!r}; expected one of {SUPPORTED_DIRECTIONS}"
        )
    return _engine.convert(text, direction=direction)
