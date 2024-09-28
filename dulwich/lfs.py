import hashlib
import os
import tempfile

class LFSStore:
    """Stores objects on disk, indexed by SHA256."""

    def __init__(self, path) -> None:
        self.path = path

    def open_object(self, sha):
        """Open an object by sha."""
        pass

    def write_object(self, chunks):
        """Write an object.

        Returns: object SHA
        """
        pass