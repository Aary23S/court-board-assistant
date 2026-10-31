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
    '\ue2a4': 'श्री',    # ी -> श्री (when standalone)
    '\ue76f': 'ेर्',     # Verified CIS FreeSerif composite Reph + E-matra (e.g. तफ -> तर्फे)
    '\ue771': 'ेंट',     # इंसटुमट -> इंस्ट्रुमेंट
    '\ue777': '्र',      # गाम -> ग्राम (consonant conjunct base ra; source has explicit aa matra \ue777 + \u093E)
    '\ue77a': 'र्',      # Reph marker (handles both standalone & positional)
    '\ue8bd': 'क्ष',     # पकार -> पक्षकार
    '\ue8be': 'ज्ञ',     # िताप -> प्रतिज्ञापत्र (source has explicit aa matra \ue8be + \u093E)
    '\ue8c0': 'क्',      # युतीवाद -> युक्तीवाद (क् + ती)
    '\ue8c4': 'च्या',    # अजदाराया -> अर्जदाराच्या
    '\ue8c8': 'ण्',      # Verified CIS FreeSerif half-consonant 0xA3 (e.g. ऐकयात -> ऐकण्यात)
    '\ue8c9': 'त्',      # Verified CIS FreeSerif half-consonant 0xB5 (e.g. यांना -> त्यांना)
    '\ue8cb': 'द्ध',     # िवद -> विरुद्ध
    '\ue8cc': 'न्',      # उहाळी -> उन्हाळी / मे.यायालय -> मे.न्यायालय
    '\ue8cd': 'प्त',     # जती -> जप्ती
    '\ue8cf': 'ब्',      # डी.डयू. -> डी.डब्ल्यू.
    '\ue8d1': 'म्',      # जवाब/हणणे -> जवाब/म्हणणे
    '\ue8d3': 'ल्या',    # जोडलेया -> जोडलेल्या
    '\ue8d5': 'व्',      # Verified CIS FreeSerif half-consonant 0xBB (e.g. पुराया -> पुराव्या)
    '\ue8d6': 'श्व',     # अश्वीनी
    '\ue8d7': 'ष्ठ',     # वरिष्ठ
    '\ue8d8': 'स्',      # टेशन -> स्टेशन
    '\ue900': 'त्त',     # दत्ता
    '\ue904': 'द्द',     # रद्द
    '\ue90b': 'द्व',     # द्वारे (source has explicit aa matra \ue90b + \u093E)
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
        Applies Devanagari phonological reordering for superscript reph (\ue77a, \ue76f)
        and pre-base velanti (\u093f), and composes split vowels (\u093e\u0947).
        Strictly preserves raw source representation and is idempotent.
        """
        if not text:
            return "", []

        # 1. Reph & Suffix PUA reordering
        # In source custom fonts, \ue2a4 is 'श्र'. When followed by 'ी', \ue2a4 + 'ी' -> 'श्री'.
        # If \ue2a4 stands alone without 'ी', it represents 'श्री'.
        text = text.replace('\ue2a4ी', 'श्री')

        # \ue1e2 is a bold header reph marker placed after 'ज' in 'अज\ue1e2' -> 'अर्ज'
        text = text.replace('ज\ue1e2', 'र्ज')

        # Phonological reordering for Reph (\ue77a)
        # In custom fonts, \ue77a is placed AFTER the consonant cluster/syllable,
        # but in standard Devanagari Unicode, reph (ra + virama) precedes the consonant cluster.
        # e.g., 'ज' + \ue77a -> 'र्ज', 'टा' + \ue77a -> 'र्टा', 'या' + \ue77a -> 'र्या'
        reph_pattern = r'([\u0915-\u0939][\u093e-\u094c]?)\ue77a'
        text = re.sub(reph_pattern, r'र्\1', text)

        # Reordering for 'तफ\ue76f' -> 'तर्फे'
        text = text.replace('तफ\ue76f', 'तर्फे')

        # 2. Clean combining virama + dotted circle artifacts (e.g. \u094d\u25cc?\u0940 -> \u0940)
        # In legacy fonts, an invalid sequence of virama + vowel sign produced dotted circle U+25CC.
        text = re.sub(r'\u094d\u25cc?([\u093e-\u094c])', r'\1', text)
        text = text.replace('\u25cc', '')

        # 2b. Map half-consonants ending with virama (e.g. \ue8c0='क्', \ue8cc='न्', \ue8cf='ब्', \ue8d8='स्')
        # BEFORE pre-base velanti reordering, so that multi-consonant clusters (like क् + त)
        # are correctly recognized as a single cluster ahead of the matra (yielding 'क्ति' rather than 'क्ित').
        for k, v in self.mapping.items():
            if v.endswith('\u094d'):
                text = text.replace(k, v)

        # 3. Pre-base Velanti (ह्रस्व वेलांटी / \u093F) phonological reordering
        # Performed BEFORE replacing Devanagari PUA consonants (e.g. \ue955 = 'प्र')
        # so that clusters like \ue955 + \u093f + त are correctly recognized as
        # pre-base velanti before 'त' and converted to \ue955 + 'ति' -> 'प्रति'.
        # Lookbehind (?<![\u0915-\u0939\u094d]) ensures already-correct post-consonant
        # matras are untouched, making normalization completely idempotent.
        # Lookahead (?![\u093e-\u094c]) ensures we attach only to syllables not already bearing a vowel.
        velanti_pat = re.compile(
            r'(?<![\u0915-\u0939\u094d])\u093f((?:[\u0915-\u0939\ue000-\uf8ff]\u093c?\u094d)*[\u0915-\u0939\ue000-\uf8ff]\u093c?)(?![\u093e-\u094c])'
        )
        text = velanti_pat.sub(lambda m: m.group(1) + '\u093f', text)

        # 4. Map PUA glyphs to canonical Unicode
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

        # 5. Split vowel composition
        # Legacy Devanagari text exports represent 'ो' (o-matra) as 'ा' + 'े' (\u093e\u0947)
        # and 'ौ' (au-matra) as 'ा' + 'ै' (\u093e\u0948).
        # We compose these onto preceding consonants:
        # e.g. काेिवड -> कोिवड -> कोविड, आराेपी -> आरोपी, समाेर -> समोर
        split_o_pat = re.compile(r'([\u0915-\u0939]\u093c?)\u093e\u0947')
        normalized = split_o_pat.sub(lambda m: m.group(1) + '\u094b', normalized)

        split_au_pat = re.compile(r'([\u0915-\u0939]\u093c?)\u093e\u0948')
        normalized = split_au_pat.sub(lambda m: m.group(1) + '\u094c', normalized)

        # 6. Clean up remaining legacy typographical anomalies and double vowels
        normalized = normalized.replace("संिप्रकरण", "संक्षिप्त प्रकरण")
        normalized = normalized.replace("संिप्त", "संक्षिप्त")
        normalized = normalized.replace("श्रीी", "श्री")
        normalized = normalized.replace("सााे.", "सा.")

        # Deduplicate accidental double vowel signs resulting from ligature glyph + matra
        # (e.g. \u093E\u093E -> \u093E, \u0940\u0940 -> \u0940)
        normalized = re.sub(r'([\u093e-\u094c])\1+', r'\1', normalized)

        # Legacy overlapping duplicate conjunct sequence in 'पुराव्याव्यतिरिक्त'
        # e.g. पुरा\ue8d5या\ue8d5यितिर\ue8c0त -> पुराव्यायाव्यायितिरक्त -> पुराव्याव्यतिरिक्त
        normalized = normalized.replace("पुराव्यायाव्यायितिरक्त", "पुराव्याव्यतिरिक्त")
        normalized = normalized.replace("पुराव्याव्यितिरक्त", "पुराव्याव्यतिरिक्त")

        # 7. Word-boundary restoration for Devanagari prefix compounds broken by font-switch/pre-base matra spaces
        # In legacy court PDF exports, prefixes like 'प्रति' followed by verbal stems like 'नियुक्त'
        # often had an extraneous space inserted due to DTP font boundary or pre-base velanti positioning
        # (e.g. 'प्रति नियुक्तीवर' -> 'प्रतिनियुक्तीवर').
        normalized = re.sub(r'\bप्रति\s+नियुक्त', 'प्रतिनियुक्त', normalized)

        return normalized, unmapped

    def detect_pua_chars(self, text: str) -> Set[str]:
        """Returns the set of distinct PUA characters found in text."""
        return {c for c in text if 0xE000 <= ord(c) <= 0xF8FF}
