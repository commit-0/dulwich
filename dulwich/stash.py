"""Stash handling."""
import os
from .file import GitFile
from .index import commit_tree, iter_fresh_objects
from .reflog import drop_reflog_entry, read_reflog
DEFAULT_STASH_REF = b'refs/stash'

class Stash:
    """A Git stash.

    Note that this doesn't currently update the working tree.
    """

    def __init__(self, repo, ref=DEFAULT_STASH_REF) -> None:
        self._ref = ref
        self._repo = repo

    @classmethod
    def from_repo(cls, repo):
        """Create a new stash from a Repo object."""
        pass

    def drop(self, index):
        """Drop entry with specified index."""
        pass

    def push(self, committer=None, author=None, message=None):
        """Create a new stash.

        Args:
          committer: Optional committer name to use
          author: Optional author name to use
          message: Optional commit message
        """
        pass

    def __getitem__(self, index):
        return list(self.stashes())[index]

    def __len__(self) -> int:
        return len(list(self.stashes()))