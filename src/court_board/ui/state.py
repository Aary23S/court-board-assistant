import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List

from court_board.io.importer import CourtBoardImporter
from court_board.classification.engine import StageClassificationEngine
from court_board.classification.collection import StageCollection
from court_board.routing.engine import RoutingEngine
from court_board.assembly.assembler import FinalBoardAssembler
from court_board.assembly.validator import FinalBoardValidator
from court_board.rendering.final_board_ods import FinalBoardODSRenderer
from court_board.rendering.stagewise_review_ods import StagewiseReviewRenderer

class AppState:
    def __init__(self):
        self.source_path: Optional[str] = None
        self.source_filename: str = ""
        self.cases = []
        self.import_validations = []
        
        self.classification_engine = StageClassificationEngine()
        self.stage_collection: Optional[StageCollection] = None
        self.classification_results = []
        
        self.routing_engine = RoutingEngine()
        self.routing_results = []
        
        self.assembled_board = None
        self.validation_report = None
        self.is_processed: bool = False

    def process_file(self, file_path: str, filename: str = ""):
        self.source_path = file_path
        self.source_filename = filename or Path(file_path).name
        
        # 1. Import
        importer = CourtBoardImporter(file_path)
        self.cases, self.import_validations = importer.load()
        
        # 2. Classification
        self.stage_collection = StageCollection(self.classification_engine.get_stages())
        self.classification_results = []
        for case in self.cases:
            class_res = self.classification_engine.classify(case)
            self.classification_results.append(class_res)
            self.stage_collection.add_result(class_res)
            
        # 3. Routing
        self.routing_results = []
        for case in self.cases:
            class_res = self.classification_engine.classify(case)
            canonical = class_res.canonical_stage
            route_res = self.routing_engine.route(case, canonical)
            self.routing_results.append(route_res)
            
        # 4. Assembly & Validation
        assembler = FinalBoardAssembler(self.routing_engine.template)
        board_date = "01.07.2026"
        if self.cases and self.cases[0].next_date:
            board_date = self.cases[0].next_date
            
        self.assembled_board = assembler.assemble(self.routing_results, board_date=board_date)
        validator = FinalBoardValidator(self.routing_engine.template)
        
        validation_passed = True
        err_msg = ""
        try:
            validator.validate(self.assembled_board, self.routing_results)
        except ValueError as ve:
            validation_passed = False
            err_msg = str(ve)

        total_entries = sum(len(sec.entries) for sec in self.assembled_board.sections)

        class Report:
            pass
        rep = Report()
        rep.entries_count_pass = validation_passed
        rep.actual_final_board_entries = total_entries
        rep.all_sections_present = len(self.assembled_board.sections) == 10
        rep.no_unexpected_entries = validation_passed
        rep.error_message = err_msg

        self.validation_report = rep
        self.is_processed = True

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def classified_count(self) -> int:
        return sum(1 for c in self.classification_results if c.classification_status == "CLASSIFIED")

    @property
    def unmapped_count(self) -> int:
        return sum(1 for c in self.classification_results if c.classification_status == "UNMAPPED")

    @property
    def routed_count(self) -> int:
        return sum(1 for r in self.routing_results if r.routing_status == "ROUTED")

    @property
    def unresolved_count(self) -> int:
        return sum(1 for r in self.routing_results if r.routing_status != "ROUTED")

    @property
    def total_destinations(self) -> int:
        return sum(len(r.destinations) for r in self.routing_results if r.routing_status == "ROUTED")

    def generate_stagewise_ods(self, output_path: str):
        if not self.stage_collection or not self.routing_results:
            raise RuntimeError("Pipeline has not been executed yet.")
        renderer = StagewiseReviewRenderer(self.stage_collection, self.routing_results)
        renderer.render(output_path)

    def generate_final_board_ods(self, output_path: str):
        if not self.assembled_board:
            raise RuntimeError("Final board has not been assembled.")
        renderer = FinalBoardODSRenderer(self.assembled_board)
        renderer.render(output_path)

    def is_libreoffice_available(self) -> bool:
        cmd = shutil.which("soffice") or shutil.which("libreoffice")
        if not cmd:
            return False
        # Verify execution
        try:
            res = subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def generate_pdf(self, ods_path: str, output_pdf_dir: str) -> Optional[str]:
        if not self.is_libreoffice_available():
            return None
        cmd = shutil.which("soffice") or shutil.which("libreoffice")
        try:
            res = subprocess.run(
                [cmd, "--headless", "--convert-to", "pdf", "--outdir", output_pdf_dir, ods_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            if res.returncode == 0:
                expected_pdf = Path(output_pdf_dir) / (Path(ods_path).stem + ".pdf")
                if expected_pdf.exists():
                    return str(expected_pdf)
            return None
        except Exception:
            return None
