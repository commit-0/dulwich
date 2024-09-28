"""Utilities for diffing files and trees."""
import stat
from collections import defaultdict, namedtuple
from io import BytesIO
from itertools import chain
from typing import Dict, List, Optional
from .object_store import BaseObjectStore
from .objects import S_ISGITLINK, ObjectID, ShaFile, Tree, TreeEntry
CHANGE_ADD = 'add'
CHANGE_MODIFY = 'modify'
CHANGE_DELETE = 'delete'
CHANGE_RENAME = 'rename'
CHANGE_COPY = 'copy'
CHANGE_UNCHANGED = 'unchanged'
RENAME_CHANGE_TYPES = (CHANGE_RENAME, CHANGE_COPY)
_NULL_ENTRY = TreeEntry(None, None, None)
_MAX_SCORE = 100
RENAME_THRESHOLD = 60
MAX_FILES = 200
REWRITE_THRESHOLD = None

class TreeChange(namedtuple('TreeChange', ['type', 'old', 'new'])):
    """Named tuple a single change between two trees."""

def _merge_entries(path, tree1, tree2):
    """Merge the entries of two trees.

    Args:
      path: A path to prepend to all tree entry names.
      tree1: The first Tree object to iterate, or None.
      tree2: The second Tree object to iterate, or None.

    Returns:
      A list of pairs of TreeEntry objects for each pair of entries in
        the trees. If an entry exists in one tree but not the other, the other
        entry will have all attributes set to None. If neither entry's path is
        None, they are guaranteed to match.
    """
    pass

def walk_trees(store, tree1_id, tree2_id, prune_identical=False):
    """Recursively walk all the entries of two trees.

    Iteration is depth-first pre-order, as in e.g. os.walk.

    Args:
      store: An ObjectStore for looking up objects.
      tree1_id: The SHA of the first Tree object to iterate, or None.
      tree2_id: The SHA of the second Tree object to iterate, or None.
      prune_identical: If True, identical subtrees will not be walked.

    Returns:
      Iterator over Pairs of TreeEntry objects for each pair of entries
        in the trees and their subtrees recursively. If an entry exists in one
        tree but not the other, the other entry will have all attributes set
        to None. If neither entry's path is None, they are guaranteed to
        match.
    """
    pass

def tree_changes(store, tree1_id, tree2_id, want_unchanged=False, rename_detector=None, include_trees=False, change_type_same=False):
    """Find the differences between the contents of two trees.

    Args:
      store: An ObjectStore for looking up objects.
      tree1_id: The SHA of the source tree.
      tree2_id: The SHA of the target tree.
      want_unchanged: If True, include TreeChanges for unmodified entries
        as well.
      include_trees: Whether to include trees
      rename_detector: RenameDetector object for detecting renames.
      change_type_same: Whether to report change types in the same
        entry or as delete+add.

    Returns:
      Iterator over TreeChange instances for each change between the
        source and target tree.
    """
    pass

def tree_changes_for_merge(store: BaseObjectStore, parent_tree_ids: List[ObjectID], tree_id: ObjectID, rename_detector=None):
    """Get the tree changes for a merge tree relative to all its parents.

    Args:
      store: An ObjectStore for looking up objects.
      parent_tree_ids: An iterable of the SHAs of the parent trees.
      tree_id: The SHA of the merge tree.
      rename_detector: RenameDetector object for detecting renames.

    Returns:
      Iterator over lists of TreeChange objects, one per conflicted path
      in the merge.

      Each list contains one element per parent, with the TreeChange for that
      path relative to that parent. An element may be None if it never
      existed in one parent and was deleted in two others.

      A path is only included in the output if it is a conflict, i.e. its SHA
      in the merge tree is not found in any of the parents, or in the case of
      deletes, if not all of the old SHAs match.
    """
    pass
_BLOCK_SIZE = 64

def _count_blocks(obj: ShaFile) -> Dict[int, int]:
    """Count the blocks in an object.

    Splits the data into blocks either on lines or <=64-byte chunks of lines.

    Args:
      obj: The object to count blocks for.

    Returns:
      A dict of block hashcode -> total bytes occurring.
    """
    pass

def _common_bytes(blocks1, blocks2):
    """Count the number of common bytes in two block count dicts.

    Args:
      blocks1: The first dict of block hashcode -> total bytes.
      blocks2: The second dict of block hashcode -> total bytes.

    Returns:
      The number of bytes in common between blocks1 and blocks2. This is
      only approximate due to possible hash collisions.
    """
    pass

def _similarity_score(obj1, obj2, block_cache=None):
    """Compute a similarity score for two objects.

    Args:
      obj1: The first object to score.
      obj2: The second object to score.
      block_cache: An optional dict of SHA to block counts to cache
        results between calls.

    Returns:
      The similarity score between the two objects, defined as the
        number of bytes in common between the two objects divided by the
        maximum size, scaled to the range 0-100.
    """
    pass

class RenameDetector:
    """Object for handling rename detection between two trees."""

    def __init__(self, store, rename_threshold=RENAME_THRESHOLD, max_files=MAX_FILES, rewrite_threshold=REWRITE_THRESHOLD, find_copies_harder=False) -> None:
        """Initialize the rename detector.

        Args:
          store: An ObjectStore for looking up objects.
          rename_threshold: The threshold similarity score for considering
            an add/delete pair to be a rename/copy; see _similarity_score.
          max_files: The maximum number of adds and deletes to consider,
            or None for no limit. The detector is guaranteed to compare no more
            than max_files ** 2 add/delete pairs. This limit is provided
            because rename detection can be quadratic in the project size. If
            the limit is exceeded, no content rename detection is attempted.
          rewrite_threshold: The threshold similarity score below which a
            modify should be considered a delete/add, or None to not break
            modifies; see _similarity_score.
          find_copies_harder: If True, consider unmodified files when
            detecting copies.
        """
        self._store = store
        self._rename_threshold = rename_threshold
        self._rewrite_threshold = rewrite_threshold
        self._max_files = max_files
        self._find_copies_harder = find_copies_harder
        self._want_unchanged = False

    def changes_with_renames(self, tree1_id, tree2_id, want_unchanged=False, include_trees=False):
        """Iterate TreeChanges between two tree SHAs, with rename detection."""
        pass
_is_tree_py = _is_tree
_merge_entries_py = _merge_entries
_count_blocks_py = _count_blocks
try:
    from dulwich._diff_tree import _count_blocks, _is_tree, _merge_entries
except ImportError:
    pass