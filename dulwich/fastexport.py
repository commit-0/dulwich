"""Fast export/import functionality."""
import stat
from typing import Dict, Tuple
from fastimport import commands, parser, processor
from fastimport import errors as fastimport_errors
from .index import commit_tree
from .object_store import iter_tree_contents
from .objects import ZERO_SHA, Blob, Commit, Tag

class GitFastExporter:
    """Generate a fast-export output stream for Git objects."""

    def __init__(self, outf, store) -> None:
        self.outf = outf
        self.store = store
        self.markers: Dict[bytes, bytes] = {}
        self._marker_idx = 0

class GitImportProcessor(processor.ImportProcessor):
    """An import processor that imports into a Git repository using Dulwich."""

    def __init__(self, repo, params=None, verbose=False, outf=None) -> None:
        processor.ImportProcessor.__init__(self, params, verbose)
        self.repo = repo
        self.last_commit = ZERO_SHA
        self.markers: Dict[bytes, bytes] = {}
        self._contents: Dict[bytes, Tuple[int, bytes]] = {}

    def blob_handler(self, cmd):
        """Process a BlobCommand."""
        pass

    def checkpoint_handler(self, cmd):
        """Process a CheckpointCommand."""
        pass

    def commit_handler(self, cmd):
        """Process a CommitCommand."""
        pass

    def progress_handler(self, cmd):
        """Process a ProgressCommand."""
        pass

    def reset_handler(self, cmd):
        """Process a ResetCommand."""
        pass

    def tag_handler(self, cmd):
        """Process a TagCommand."""
        pass

    def feature_handler(self, cmd):
        """Process a FeatureCommand."""
        pass