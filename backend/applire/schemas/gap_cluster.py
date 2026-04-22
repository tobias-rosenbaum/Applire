from typing import Literal

from pydantic import BaseModel


class GapClusterSchema(BaseModel):
    id: str
    label: str
    category: Literal["B", "C"]
    gaps: list[str]
    jd_skills: list[str]
    jd_context: str
