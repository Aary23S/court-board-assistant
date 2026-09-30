import argparse
import sys
from collections import Counter
from pathlib import Path
from ..io.importer import CourtBoardImporter
from ..classification.engine import StageClassificationEngine
from ..classification.collection import StageCollection
from ..rendering.stagewise_ods import StageWiseRenderer
from ..validation.business_rule_validator import BusinessRuleValidator

def main():
    parser = argparse.ArgumentParser(description="Court Board Assistant CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect an ODS/XLSX file")
    inspect_parser.add_argument("file", type=str, help="Path to the source file")

    # Stages command
    stages_parser = subparsers.add_parser("stages", help="Classify cases into canonical stages and output stagewise ODS")
    stages_parser.add_argument("file", type=str, help="Path to the source file")

    # Rules command
    rules_parser = subparsers.add_parser("rules", help="Generate Business Rule Report")

    args = parser.parse_args()

    if args.command == "inspect":
        importer = CourtBoardImporter(args.file)
        records, validations = importer.load()
        
        valid = [v for v in validations if v.status == "VALID"]
        warnings = [v for v in validations if v.status == "WARNING"]
        errors = [v for v in validations if v.status == "ERROR"]
        
        print(f"Source file: {args.file}")
        print(f"Cases found: {len(records)}")
        print(f"Valid: {len(valid)}")
        print(f"Warnings: {len(warnings)}")
        print(f"Errors: {len(errors)}")
        print("\nNext Purpose values:")
        
        purposes = Counter([r.next_purpose for r in records])
        for p, count in purposes.most_common():
            print(f"{p}: {count}")
            
        if errors:
            print("\nErrors:")
            for e in errors[:10]:
                print(f"Row {e.source_row_index} [{e.column}]: {e.message}")
            if len(errors) > 10:
                print(f"... and {len(errors) - 10} more.")

    elif args.command == "stages":
        # 1. Import
        importer = CourtBoardImporter(args.file)
        records, validations = importer.load()
        invalid_count = len([v for v in validations if v.status == "ERROR"])
        
        # 2. Setup Engine & Collection
        engine = StageClassificationEngine()
        collection = StageCollection(engine.get_stages())
        
        # 3. Classify
        for record in records:
            result = engine.classify(record)
            collection.add_result(result)
            
        # 4. Verify invariants
        collection.verify_invariants(len(records), invalid_count)
        
        # 5. Render
        output_name = Path(args.file).stem + "_stagewise.ods"
        output_path = f"output/{output_name}"
        renderer = StageWiseRenderer(collection)
        renderer.render(output_path)
        
        # 6. Report
        print(f"Source:\n{Path(args.file).name}\n")
        print(f"Total cases:\n{len(records)}\n")
        print(f"Classified:\n{collection.classified_count}\n")
        print(f"Unmapped:\n{collection.unmapped_count}\n")
        
        print("Stages:\n")
        for stage, cases in collection.get_all_stages():
            if len(cases) > 0:
                print(f"{stage.canonical_name:<30} {len(cases)}")
                
        print(f"\nOutput:\n{output_path}\n")
        
        unmapped = collection.get_unmapped()
        if unmapped:
            print("UNMAPPED NEXT PURPOSES\n")
            
            # Group by normalized value
            unmapped_groups = {}
            for res in unmapped:
                key = res.original_next_purpose
                if key not in unmapped_groups:
                    unmapped_groups[key] = []
                unmapped_groups[key].append(res.source_case.cases)
                
            for original_val, case_nums in unmapped_groups.items():
                print(f'"{original_val}" — {len(case_nums)} cases')
                print(f"  Cases: {', '.join(case_nums)}\n")

    elif args.command == "rules":
        validator = BusinessRuleValidator()
        
        try:
            validator.validate()
        except ValueError as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)
            
        report = validator.get_stage_status_report()
        
        total = len(validator.canonical_stages)
        approved = len(report["APPROVED"])
        unresolved = len(report["UNRESOLVED"])
        ambiguous = len(report["AMBIGUOUS"])
        disabled = len(report["DISABLED"])
        
        print(f"Canonical stages:\n{total}\n")
        print(f"Approved:\n{approved}\n")
        print(f"Unresolved:\n{unresolved}\n")
        print(f"Ambiguous:\n{ambiguous}\n")
        print(f"Disabled:\n{disabled}\n")
        
        print("APPROVED RULES\n")
        print(f"{'Stage':<30} {'Board Section':<20} {'Ready'}")
        print("-" * 60)
        for r in sorted(report["APPROVED"], key=lambda x: x.stage):
            print(f"{r.stage:<30} {r.board_section or '':<20} {r.ready_behavior or ''}")
            
        print("\nUNRESOLVED\n")
        for r in sorted(report["UNRESOLVED"], key=lambda x: x.stage):
            print(r.stage)
            
        if report["AMBIGUOUS"]:
            print("\nAMBIGUOUS\n")
            for r in sorted(report["AMBIGUOUS"], key=lambda x: x.stage):
                print(r.stage)
                
        if report["DISABLED"]:
            print("\nDISABLED\n")
            for r in sorted(report["DISABLED"], key=lambda x: x.stage):
                print(r.stage)

if __name__ == "__main__":
    main()
