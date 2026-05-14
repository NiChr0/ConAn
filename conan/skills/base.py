# conan/skills/base.py
import os
from abc import ABC, abstractmethod
from pathlib import Path
from conan.executor import Executor
from conan.kb.loader import KBLoader
from conan.models import SkillResult, OrchestratorDispatch


class SkillBase(ABC):
    name: str
    description: str

    def __init__(self, kb_path: str | Path, db_url: str, model: str | None = None):
        self.kb_loader = KBLoader(kb_path)
        self.executor = Executor(db_url)
        self.model = model or os.getenv("CONAN_SKILL_MODEL", "gemma4:e4b")

    @abstractmethod
    def run(self, question: str, dispatch: OrchestratorDispatch) -> SkillResult:
        pass
