from abc import ABC, abstractmethod
from typing import List
import socket
from ..schema import Model

class BaseGenerator(ABC):
    def find_available_port(self, start_port=8000, max_port=8100) -> int:
        """Find an available port starting from start_port."""
        for port in range(start_port, max_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        return start_port

    @abstractmethod
    def generate(self, models: List[Model], output_dir: str) -> None:
        """Generate framework-specific code from normalized models."""
        pass
