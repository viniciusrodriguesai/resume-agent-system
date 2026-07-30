from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentResult:
    """Standard result produced by every agent."""

    agent_name: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class BaseAgent:
    """Simple base class shared by all project agents."""

    name = "Base Agent"

    def run(self, *args, **kwargs) -> AgentResult:
        raise NotImplementedError("Each agent must implement the run() method.")
