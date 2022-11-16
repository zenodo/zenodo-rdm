from abc import ABC, abstractmethod


class Extract(ABC):
    """Base class for data extraction."""

    @abstractmethod
    def run(self):
        """Yield one element at a time."""
        pass
