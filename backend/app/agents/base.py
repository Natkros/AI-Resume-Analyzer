"""Phase 9: minimal agent framework.

Agents are used ONLY where a deterministic function is not sufficient
(Phase 26 principle). Most steps in this pipeline ARE deterministic
(parsing, taxonomy, matching, scoring, ATS) and are wrapped here as thin
agents purely so the Supervisor can orchestrate one uniform pipeline and
produce a single consolidated report — not because they need agentic
reasoning. Only the recommendation/optimization/interview/roadmap agents
actually call an LLM.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    """Shared state passed between agents in a pipeline run. Each agent reads
    what it needs and writes its output under its own key, so later agents
    (and the final report) can inspect any prior agent's result."""

    data: dict[str, Any] = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class Agent(ABC):
    name: str = "agent"

    @abstractmethod
    def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError

    def run_safely(self, ctx: AgentContext) -> AgentContext:
        try:
            return self.run(ctx)
        except Exception as exc:  # an agent failing should not crash the whole pipeline
            ctx.errors.append({"agent": self.name, "error": str(exc)})
            return ctx
