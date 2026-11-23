"""
Base analyzer abstract class following the Strategy Pattern.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class BaseAnalyzer(ABC):
    def __init__(self, language_name: str):
        self.language_name = language_name

    @abstractmethod
    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        pass
