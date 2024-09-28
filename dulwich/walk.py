"""General implementation of walking commits and their contents."""
import collections
import heapq
from itertools import chain
from typing import Deque, Dict, List, Optional, Set, Tuple
from .diff_tree import RENAME_CHANGE_TYPES, RenameDetector, TreeChange, tree_changes, tree_changes_for_merge
from .errors import MissingCommitError
from .objects import Commit, ObjectID, Tag
ORDER_DATE = 'date'
ORDER_TOPO = 'topo'
ALL_ORDERS = (ORDER_DATE, ORDER_TOPO)
_MAX_EXTRA_COMMITS = 5

class WalkEntry:
    """Object encapsulating a single result from a walk."""

    def __init__(self, walker, commit) -> None:
        self.commit = commit
        self._store = walker.store
        self._get_parents = walker.get_parents
        self._changes: Dict[str, List[TreeChange]] = {}
        self._rename_detector = walker.rename_detector

    def changes(self, path_prefix=None):
        """Get the tree changes for this entry.

        Args:
          path_prefix: Portion of the path in the repository to
            use to filter changes. Must be a directory name. Must be
            a full, valid, path reference (no partial names or wildcards).
        Returns: For commits with up to one parent, a list of TreeChange
            objects; if the commit has no parents, these will be relative to
            the empty tree. For merge commits, a list of lists of TreeChange
            objects; see dulwich.diff.tree_changes_for_merge.
        """
        pass

    def __repr__(self) -> str:
        return f'<WalkEntry commit={self.commit.id}, changes={self.changes()!r}>'

class _CommitTimeQueue:
    """Priority queue of WalkEntry objects by commit time."""

    def __init__(self, walker: 'Walker') -> None:
        self._walker = walker
        self._store = walker.store
        self._get_parents = walker.get_parents
        self._excluded = walker.excluded
        self._pq: List[Tuple[int, Commit]] = []
        self._pq_set: Set[ObjectID] = set()
        self._seen: Set[ObjectID] = set()
        self._done: Set[ObjectID] = set()
        self._min_time = walker.since
        self._last = None
        self._extra_commits_left = _MAX_EXTRA_COMMITS
        self._is_finished = False
        for commit_id in chain(walker.include, walker.excluded):
            self._push(commit_id)
    __next__ = next

class Walker:
    """Object for performing a walk of commits in a store.

    Walker objects are initialized with a store and other options and can then
    be treated as iterators of Commit objects.
    """

    def __init__(self, store, include: List[bytes], exclude: Optional[List[bytes]]=None, order: str='date', reverse: bool=False, max_entries: Optional[int]=None, paths: Optional[List[bytes]]=None, rename_detector: Optional[RenameDetector]=None, follow: bool=False, since: Optional[int]=None, until: Optional[int]=None, get_parents=lambda commit: commit.parents, queue_cls=_CommitTimeQueue) -> None:
        """Constructor.

        Args:
          store: ObjectStore instance for looking up objects.
          include: Iterable of SHAs of commits to include along with their
            ancestors.
          exclude: Iterable of SHAs of commits to exclude along with their
            ancestors, overriding includes.
          order: ORDER_* constant specifying the order of results.
            Anything other than ORDER_DATE may result in O(n) memory usage.
          reverse: If True, reverse the order of output, requiring O(n)
            memory.
          max_entries: The maximum number of entries to yield, or None for
            no limit.
          paths: Iterable of file or subtree paths to show entries for.
          rename_detector: diff.RenameDetector object for detecting
            renames.
          follow: If True, follow path across renames/copies. Forces a
            default rename_detector.
          since: Timestamp to list commits after.
          until: Timestamp to list commits before.
          get_parents: Method to retrieve the parents of a commit
          queue_cls: A class to use for a queue of commits, supporting the
            iterator protocol. The constructor takes a single argument, the
            Walker.
        """
        if order not in ALL_ORDERS:
            raise ValueError(f'Unknown walk order {order}')
        self.store = store
        if isinstance(include, bytes):
            include = [include]
        self.include = include
        self.excluded = set(exclude or [])
        self.order = order
        self.reverse = reverse
        self.max_entries = max_entries
        self.paths = paths and set(paths) or None
        if follow and (not rename_detector):
            rename_detector = RenameDetector(store)
        self.rename_detector = rename_detector
        self.get_parents = get_parents
        self.follow = follow
        self.since = since
        self.until = until
        self._num_entries = 0
        self._queue = queue_cls(self)
        self._out_queue: Deque[WalkEntry] = collections.deque()

    def _should_return(self, entry):
        """Determine if a walk entry should be returned..

        Args:
          entry: The WalkEntry to consider.
        Returns: True if the WalkEntry should be returned by this walk, or
            False otherwise (e.g. if it doesn't match any requested paths).
        """
        pass

    def _reorder(self, results):
        """Possibly reorder a results iterator.

        Args:
          results: An iterator of WalkEntry objects, in the order returned
            from the queue_cls.
        Returns: An iterator or list of WalkEntry objects, in the order
            required by the Walker.
        """
        pass

    def __iter__(self):
        return iter(self._reorder(iter(self._next, None)))

def _topo_reorder(entries, get_parents=lambda commit: commit.parents):
    """Reorder an iterable of entries topologically.

    This works best assuming the entries are already in almost-topological
    order, e.g. in commit time order.

    Args:
      entries: An iterable of WalkEntry objects.
      get_parents: Optional function for getting the parents of a commit.
    Returns: iterator over WalkEntry objects from entries in FIFO order, except
        where a parent would be yielded before any of its children.
    """
    pass