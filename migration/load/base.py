from abc import ABC, abstractmethod


class Load(ABC):
    """Base class for data loading."""

    @abstractmethod
    def _prepare(self):
        """Prepare data for loading."""
        pass

    @abstractmethod
    def _cleanup(self):
        """Cleanup data after loading."""
        pass

    @abstractmethod
    def run(self, datagen, cleanup=False):
        """Load entries."""
        pass
