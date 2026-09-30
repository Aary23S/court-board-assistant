from typing import List, Dict, Tuple
from ..domain.models import CaseRecord
from .models import StageClassificationResult, StageConfig

class StageCollection:
    """
    Holds the stage-wise dataset and provides access to cases by stage,
    preserving source case ordering.
    """
    def __init__(self, stages: List[StageConfig]):
        self.stages = sorted(stages, key=lambda s: s.order)
        self._stage_buckets: Dict[str, List[StageClassificationResult]] = {
            s.canonical_name: [] for s in self.stages
        }
        self.unmapped: List[StageClassificationResult] = []
        self._classified_count = 0
        self._unmapped_count = 0

    def add_result(self, result: StageClassificationResult):
        if result.classification_status == "CLASSIFIED" and result.canonical_stage:
            self._stage_buckets[result.canonical_stage].append(result)
            self._classified_count += 1
        else:
            self.unmapped.append(result)
            self._unmapped_count += 1

    def get_cases_for_stage(self, canonical_stage: str) -> List[StageClassificationResult]:
        return self._stage_buckets.get(canonical_stage, [])

    def get_all_stages(self) -> List[Tuple[StageConfig, List[StageClassificationResult]]]:
        """Returns stages in configured order along with their cases."""
        return [(s, self._stage_buckets[s.canonical_name]) for s in self.stages]

    def get_unmapped(self) -> List[StageClassificationResult]:
        return self.unmapped
        
    @property
    def classified_count(self) -> int:
        return self._classified_count
        
    @property
    def unmapped_count(self) -> int:
        return self._unmapped_count

    def verify_invariants(self, imported_record_count: int, invalid_count: int):
        """
        Accountability check to ensure no cases were silently lost or duplicated.
        """
        accounted = self.classified_count + self.unmapped_count + invalid_count
        if accounted != imported_record_count:
            raise ValueError(f"Invariant violation: Classified({self.classified_count}) + Unmapped({self.unmapped_count}) + Invalid({invalid_count}) = {accounted}, but expected {imported_record_count}")
