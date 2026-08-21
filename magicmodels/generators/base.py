from abc import ABC, abstractmethod
from typing import List
from ..schema import Model

class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, models: List[Model], output_dir: str) -> None:
        """Generate framework-specific code from normalized models."""
        pass
