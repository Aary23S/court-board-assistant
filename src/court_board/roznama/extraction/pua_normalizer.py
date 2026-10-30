"""
Deterministic Marathi Private Use Area (PUA) glyph mapping component.
Converts custom TrueType font encodings (e.g. FreeSerif PUA codes \uE000-\uF8FF)
into canonical Devanagari Unicode.
"""
import re
from typing import Dict, Tuple, Set, List

# Explicit mapping table for verified PUA glyphs from Maharashtra e-Courts PDFs
MARATHI_PUA_GLYPH_MAP: Dict[str, str] = {
    '\ue1e2': 'र्ज',      # अज -> अर्ज
    '\ue20a': 'क्षि',     # संित -> संक्षिप्त
    '\ue20e': 'ख्',      # मुय -> मुख्य (ख् + य)
    '\ue219': 'न्',      # यायदंडािधकारी -> न्यायदंडाधिकारी (न् + य)
    '\ue21a': 'प्',      # संित -> संक्षिप्त
    '\ue222': 'व्',      # .ही.पालीवाल -> .व्ही.पालीवाल
    '\ue29f': 'क्र',     # मांक -> क्रमांक
    '\ue2a2': 'प्र',     # करण -> प्रकरण
    '\ue2a4': 'श्री',    # ी -> श्री
    '\ue76f': 'र्फे',     # अजदारातफ -> अर्जदारातर्फे
    '\ue771': 'ेंट',     # इंसटुमट -> इंस्ट्रुमेंट
    '\ue777': '्रा',     # गाम -> ग्राम
    '\ue77a': 'र्',      # Reph marker (handles both standalone & positional)
    '\ue8bd': 'क्ष',     # पकार -> पक्षकार
    '\ue8be': 'ज्ञा',    # िताप -> प्रतिज्ञापत्र
    '\ue8c0': 'क्',      # युतीवाद -> युक्तीवाद (क् + ती)
    '\ue8c4': 'च्या',    # अजदाराया -> अर्जदाराच्या
    '\ue8c8': 'ण्या',    # वगळयात -> वगळण्यात
    '\ue8c9': 'त्या',    # यांचे -> त्यांचे
    '\ue8cb': 'द्ध',     # िवद -> विरुद्ध
    '\ue8cc': 'न्',      # उहाळी -> उन्हाळी / मे.यायालय -> मे.न्यायालय
    '\ue8cd': 'प्त',     # जती -> जप्ती
    '\ue8cf': 'ब्',      # डी.डयू. -> डी.डब्ल्यू.
    '\ue8d1': 'म्',      # जवाब/हणणे -> जवाब/म्हणणे
    '\ue8d3': 'ल्या',    # जोडलेया -> जोडलेल्या
    '\ue8d5': 'व्या',    # पुराव्या
    '\ue8d6': 'श्व',     # अश्वीनी
    '\ue8d7': 'ष्ठ',     # वरिष्ठ
    '\ue8d8': 'स्',      # टेशन -> स्टेशन
    '\ue900': 'त्त',     # दत्ता
    '\ue904': 'द्द',     # रद्द
    '\ue90b': 'द्वा',    # द्वारे
    '\ue952': 'क्र.',    # .२ -> क्र.२
    '\ue954': 'त्र',     # वकीलप -> वकीलपत्र
    '\ue955': 'प्र',     # करण -> प्रकरण
    '\ue957': 'श्री',    # ीमती -> श्रीमती
    '\ue95d': 'रु',     # िवद -> विरुद्ध
    '\ue95e': 'रु',     # पये -> रुपये
    '\ue988': 'नों',     # नदिवला -> नोंदविला
}

class MarathiPUANormalizer:
    """
    Normalizes legacy Marathi text containing PUA glyphs to canonical Unicode.
    """
    def __init__(self, custom_mapping: Dict[str, str] = None):
        self.mapping = dict(MARATHI_PUA_GLYPH_MAP)
        if custom_mapping:
            self.mapping.update(custom_mapping)

    def normalize(self, text: str) -> Tuple[str, List[str]]:
        """
        Replaces known PUA characters with canonical Devanagari Unicode.
        Applies Devanagari phonological reordering for superscript reph (\ue77a, \ue76f).
        """
        if not text:
            return "", []

        # 1. Phonological reordering for Reph (\ue77a)
        # In custom fonts, \ue77a is placed AFTER the consonant cluster,
        # but in standard Devanagari Unicode, reph (ra + virama) precedes the consonant cluster.
        # e.g., 'ज' + \ue77a -> 'र्ज'
        reph_pattern = r'([\u0915-\u0939][\u093e-\u094c]?)\ue77a'
        text = re.sub(reph_pattern, r'र्\1', text)

        # 2. Reordering for 'तफ\ue76f' -> 'तर्फे'
        text = text.replace('तफ\ue76f', 'तर्फे')

        unmapped = []
        chars = []

        for c in text:
            cp = ord(c)
            if 0xE000 <= cp <= 0xF8FF:
                if c in self.mapping:
                    chars.append(self.mapping[c])
                else:
                    unmapped.append(c)
                    chars.append(c)  # Preserve unmapped character; never silently discard
            else:
                chars.append(c)

        normalized = "".join(chars)
        
        # 3. Clean up pre-base matra anomalies common to legacy custom-font exports
        normalized = normalized.replace("संिप्रकरण", "संक्षिप्त प्रकरण")
        normalized = normalized.replace("संिप्त", "संक्षिप्त")

        return normalized, unmapped

    def detect_pua_chars(self, text: str) -> Set[str]:
        """Returns the set of distinct PUA characters found in text."""
        return {c for c in text if 0xE000 <= ord(c) <= 0xF8FF}
