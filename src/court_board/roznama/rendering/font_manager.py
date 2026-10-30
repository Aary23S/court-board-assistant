"""
Font Manager for Roznama PDF Generator.
Locates, validates, and encodes the bundled Lohit Devanagari font.
"""
from pathlib import Path
import base64

class FontManager:
    """
    Manages access and validation for bundled Lohit Devanagari font assets.
    """
    FONT_FILENAME = "Lohit-Devanagari.ttf"
    LICENSE_FILENAME = "OFL.txt"

    def __init__(self, font_dir: Path = None):
        if font_dir is None:
            self.font_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"
        else:
            self.font_dir = Path(font_dir)

    @property
    def font_path(self) -> Path:
        return self.font_dir / self.FONT_FILENAME

    @property
    def license_path(self) -> Path:
        return self.font_dir / self.LICENSE_FILENAME

    def validate_font_asset(self) -> bool:
        """
        Validates that the font file exists, is non-empty, and has expected size.
        """
        if not self.font_path.exists():
            raise FileNotFoundError(
                f"Required font '{self.FONT_FILENAME}' not found at {self.font_path}."
            )
        if self.font_path.stat().st_size < 10000:
            raise ValueError(
                f"Font file '{self.FONT_FILENAME}' at {self.font_path} is invalid or incomplete."
            )
        return True

    def get_base64_font(self) -> str:
        """
        Returns the base64-encoded font data for embedding directly in CSS @font-face.
        """
        self.validate_font_asset()
        return base64.b64encode(self.font_path.read_bytes()).decode("ascii")

