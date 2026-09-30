import re

class CasePrefixExtractor:
    def __init__(self):
        self.approved_prefixes = {
            "Cri.M.A.",
            "PWDVA Appln.",
            "R.C.C.",
            "S.C.C."
        }

    def extract(self, case_number: str) -> str:
        """
        Extracts the prefix from a case number.
        Normalizes whitespace and checks against approved prefixes.
        Returns the valid prefix, or "UNKNOWN_PREFIX" if invalid or unapproved.
        """
        if not case_number:
            return "UNKNOWN_PREFIX"
            
        # Common pattern: prefix / number / year
        parts = case_number.split('/')
        if not parts:
            return "UNKNOWN_PREFIX"
            
        prefix = parts[0]
        # Normalize whitespace (replace multiple spaces/newlines with single space, strip)
        prefix = re.sub(r'\s+', ' ', prefix).strip()
        
        if prefix in self.approved_prefixes:
            return prefix
            
        return "UNKNOWN_PREFIX"
