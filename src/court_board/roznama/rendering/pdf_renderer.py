"""
PDF Renderer implementation using Headless Chrome / Edge with HTML+CSS.
Provides high-fidelity OpenType Devanagari shaping and exact court-approved target layout fidelity.
"""
from pathlib import Path
from typing import List, Optional, Union
import subprocess
import tempfile
import shutil

from ..domain.models import RoznamaRecord, RoznamaHeader
from .html_builder import RoznamaHTMLBuilder
from .font_manager import FontManager
from .presentation_model import RoznamaPresentationModel

class RoznamaPDFRenderer:
    """
    Renders transformed Roznama records or presentation model into a printable PDF.
    """
    def __init__(
        self,
        font_manager: Optional[FontManager] = None,
        html_builder: Optional[RoznamaHTMLBuilder] = None
    ):
        self.font_manager = font_manager or FontManager()
        self.html_builder = html_builder or RoznamaHTMLBuilder(self.font_manager)
        self.browser_path = self._locate_browser()

    def _locate_browser(self) -> Optional[Path]:
        """Locates Chrome, Chromium, or Edge binary for headless rendering."""
        # 1. Check system PATH
        for binary in ["google-chrome", "chrome", "chromium", "chromium-browser", "msedge"]:
            p = shutil.which(binary)
            if p:
                return Path(p)

        # 2. Check standard Windows installation paths
        win_candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ]
        for candidate in win_candidates:
            if candidate.exists():
                return candidate

        return None

    def render(
        self,
        records: Union[List[RoznamaRecord], RoznamaPresentationModel],
        output_path: Path,
        header: Optional[RoznamaHeader] = None
    ) -> Path:
        """
        Renders records or RoznamaPresentationModel into a PDF file at output_path.
        """
        if not self.browser_path:
            raise RuntimeError(
                "Headless Chromium/Chrome/Edge executable could not be found. "
                "Please install Google Chrome or Microsoft Edge."
            )

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Build printable HTML
        if isinstance(records, RoznamaPresentationModel):
            html_content = self.html_builder.build_html_from_presentation(records)
        else:
            html_content = self.html_builder.build_html(records, header)

        # 2. Write temporary HTML file
        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tf:
            tf.write(html_content)
            temp_html = Path(tf.name)

        try:
            # 3. Invoke headless print-to-pdf
            cmd = [
                str(self.browser_path),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-crash-reporter",
                "--no-pdf-header-footer",
                f"--print-to-pdf={str(out_path)}",
                str(temp_html)
            ]

            res = subprocess.run(cmd, capture_output=True, timeout=30)
            if not out_path.exists() or out_path.stat().st_size == 0:
                # Try with msedge if chrome had an issue
                edge_path = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
                if edge_path.exists() and edge_path != self.browser_path:
                    cmd[0] = str(edge_path)
                    res = subprocess.run(cmd, capture_output=True, timeout=30)

            if not out_path.exists() or out_path.stat().st_size == 0:
                raise RuntimeError(
                    f"PDF generation failed. Browser output: {res.stderr.decode('utf-8', errors='ignore')}"
                )

            return out_path
        finally:
            if temp_html.exists():
                temp_html.unlink()
