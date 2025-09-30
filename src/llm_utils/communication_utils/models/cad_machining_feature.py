from enum import Enum
from typing import List


class MachiningFeature(Enum):
    CHAMFER = "Chamfer"
    THROUGH_HOLE = "Through hole"
    TRIANGULAR_PASSAGE = "Triangular passage"
    RECTANGULAR_PASSAGE = "Rectangular passage"
    SIX_SIDES_PASSAGE = "6-sides passage"
    TRIANGULAR_THROUGH_SLOT = "Triangular through slot"
    RECTANGULAR_THROUGH_SLOT = "Rectangular through slot"
    CIRCULAR_THROUGH_SLOT = "Circular through slot"
    RECTANGULAR_THROUGH_STEP = "Rectangular through step"
    TWO_SIDES_THROUGH_STEP = "2-sides through step"
    SLANTED_THROUGH_STEP = "Slanted through step"
    O_RING = "Shaft"
    BLIND_HOLE = "Blind hole"
    TRIANGULAR_POCKET = "Triangular pocket"
    RECTANGULAR_POCKET = "Rectangular pocket"
    SIX_SIDES_POCKET = "6-sides pocket"
    CIRCULAR_END_POCKET = "Circular end pocket"
    RECTANGULAR_BLIND_SLOT = "Rectangular blind slot"
    VERTICAL_CIRCULAR_END_BLIND_SLOT = "Vertical circular end blind slot"
    HORIZONTAL_CIRCULAR_END_BLIND_SLOT = "Horizontal circular end blind slot"
    TRIANGULAR_BLIND_STEP = "Triangular blind step"
    CIRCULAR_BLIND_STEP = "Circular blind step"
    RECTANGULAR_BLIND_STEP = "Rectangular blind step"
    ROUND = "Round"
    STOCK = "Stock"

    @staticmethod
    def by_index(idx: int) -> "MachiningFeature":
        return list(MachiningFeature)[idx]

    def possible_values(self) -> List[str]:
        if self == MachiningFeature.O_RING:
            return [MachiningFeature.O_RING.value.lower(), "shaft"]
        else:
            return [self.value.lower()]

    @staticmethod
    def by_name(name: str) -> "MachiningFeature":
        for feature in list(MachiningFeature):
            if name.lower() in feature.possible_values():
                return feature
        raise RuntimeError()
