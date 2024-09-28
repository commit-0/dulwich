"""Implementation of merge-base following the approach of git."""
from heapq import heappop, heappush
from .lru_cache import LRUCache

class WorkList:

    def __init__(self):
        self.pq = []

def find_merge_base(repo, commit_ids):
    """Find lowest common ancestors of commit_ids[0] and *any* of commits_ids[1:].

    Args:
      repo: Repository object
      commit_ids: list of commit ids
    Returns:
      list of lowest common ancestor commit_ids
    """
    pass

def find_octopus_base(repo, commit_ids):
    """Find lowest common ancestors of *all* provided commit_ids.

    Args:
      repo: Repository
      commit_ids:  list of commit ids
    Returns:
      list of lowest common ancestor commit_ids
    """
    pass

def can_fast_forward(repo, c1, c2):
    """Is it possible to fast-forward from c1 to c2?

    Args:
      repo: Repository to retrieve objects from
      c1: Commit id for first commit
      c2: Commit id for second commit
    """
    pass