from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

@dataclass
class AgentResult:
    agent_name: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.0
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaseAgent:
    name = "Base Agent"

    def run(self, *args: Any, **kwargs: Any) -> AgentResult:
        raise NotImplementedError
