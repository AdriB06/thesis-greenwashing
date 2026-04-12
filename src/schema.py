from typing import Literal
from pydantic import BaseModel

CategoryType = Literal[
    "Future Commitment",
    "Past Achievement",
    "Climate Risk Disclosure",
    "Quantitative Disclosure",
    "Symbolic/Vague Language",
    "Regulatory/Framework Reference",
]


class ClassificationResult(BaseModel):
    category: CategoryType
    justification: str