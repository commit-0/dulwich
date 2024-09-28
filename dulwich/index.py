"""Parser for the git index file format."""
import os
import stat
import struct
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, BinaryIO, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Union
from .file import GitFile
from .object_store import iter_tree_contents
from .objects import S_IFGITLINK, S_ISGITLINK, Blob, ObjectID, Tree, hex_to_sha, sha_to_hex
from .pack import ObjectContainer, SHA1Reader, SHA1Writer
FLAG_STAGEMASK = 12288
FLAG_STAGESHIFT = 12
FLAG_NAMEMASK = 4095
FLAG_VALID = 32768
FLAG_EXTENDED = 16384
EXTENDED_FLAG_SKIP_WORKTREE = 16384
EXTENDED_FLAG_INTEND_TO_ADD = 8192
DEFAULT_VERSION = 2

class Stage(Enum):
    NORMAL = 0
    MERGE_CONFLICT_ANCESTOR = 1
    MERGE_CONFLICT_THIS = 2
    MERGE_CONFLICT_OTHER = 3

@dataclass
class SerializedIndexEntry:
    name: bytes
    ctime: Union[int, float, Tuple[int, int]]
    mtime: Union[int, float, Tuple[int, int]]
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha: bytes
    flags: int
    extended_flags: int

@dataclass
class IndexEntry:
    ctime: Union[int, float, Tuple[int, int]]
    mtime: Union[int, float, Tuple[int, int]]
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha: bytes

class ConflictedIndexEntry:
    """Index entry that represents a conflict."""
    ancestor: Optional[IndexEntry]
    this: Optional[IndexEntry]
    other: Optional[IndexEntry]

    def __init__(self, ancestor: Optional[IndexEntry]=None, this: Optional[IndexEntry]=None, other: Optional[IndexEntry]=None) -> None:
        self.ancestor = ancestor
        self.this = this
        self.other = other

class UnmergedEntries(Exception):
    """Unmerged entries exist in the index."""

def pathsplit(path: bytes) -> Tuple[bytes, bytes]:
    """Split a /-delimited path into a directory part and a basename.

    Args:
      path: The path to split.

    Returns:
      Tuple with directory name and basename
    """
    pass

def pathjoin(*args):
    """Join a /-delimited path."""
    pass

def read_cache_time(f):
    """Read a cache time.

    Args:
      f: File-like object to read from
    Returns:
      Tuple with seconds and nanoseconds
    """
    pass

def write_cache_time(f, t):
    """Write a cache time.

    Args:
      f: File-like object to write to
      t: Time to write (as int, float or tuple with secs and nsecs)
    """
    pass

def read_cache_entry(f, version: int) -> SerializedIndexEntry:
    """Read an entry from a cache file.

    Args:
      f: File-like object to read from
    """
    pass

def write_cache_entry(f, entry: SerializedIndexEntry, version: int) -> None:
    """Write an index entry to a file.

    Args:
      f: File object
      entry: IndexEntry to write, tuple with:
    """
    pass

class UnsupportedIndexFormat(Exception):
    """An unsupported index format was encountered."""

    def __init__(self, version) -> None:
        self.index_format_version = version

def read_index(f: BinaryIO) -> Iterator[SerializedIndexEntry]:
    """Read an index file, yielding the individual entries."""
    pass

def read_index_dict(f) -> Dict[bytes, Union[IndexEntry, ConflictedIndexEntry]]:
    """Read an index file and return it as a dictionary.
       Dict Key is tuple of path and stage number, as
            path alone is not unique
    Args:
      f: File object to read fromls.
    """
    pass

def write_index(f: BinaryIO, entries: List[SerializedIndexEntry], version: Optional[int]=None):
    """Write an index file.

    Args:
      f: File-like object to write to
      version: Version number to write
      entries: Iterable over the entries to write
    """
    pass

def write_index_dict(f: BinaryIO, entries: Dict[bytes, Union[IndexEntry, ConflictedIndexEntry]], version: Optional[int]=None) -> None:
    """Write an index file based on the contents of a dictionary.
    being careful to sort by path and then by stage.
    """
    pass

def cleanup_mode(mode: int) -> int:
    """Cleanup a mode value.

    This will return a mode that can be stored in a tree object.

    Args:
      mode: Mode to clean up.

    Returns:
      mode
    """
    pass

class Index:
    """A Git Index file."""
    _byname: Dict[bytes, Union[IndexEntry, ConflictedIndexEntry]]

    def __init__(self, filename: Union[bytes, str], read=True) -> None:
        """Create an index object associated with the given filename.

        Args:
          filename: Path to the index file
          read: Whether to initialize the index from the given file, should it exist.
        """
        self._filename = filename
        self._version = None
        self.clear()
        if read:
            self.read()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._filename!r})'

    def write(self) -> None:
        """Write current contents of index to disk."""
        pass

    def read(self):
        """Read current contents of index from disk."""
        pass

    def __len__(self) -> int:
        """Number of entries in this index file."""
        return len(self._byname)

    def __getitem__(self, key: bytes) -> Union[IndexEntry, ConflictedIndexEntry]:
        """Retrieve entry by relative path and stage.

        Returns: Either a IndexEntry or a ConflictedIndexEntry
        Raises KeyError: if the entry does not exist
        """
        return self._byname[key]

    def __iter__(self) -> Iterator[bytes]:
        """Iterate over the paths and stages in this index."""
        return iter(self._byname)

    def __contains__(self, key):
        return key in self._byname

    def get_sha1(self, path: bytes) -> bytes:
        """Return the (git object) SHA1 for the object at a path."""
        pass

    def get_mode(self, path: bytes) -> int:
        """Return the POSIX file mode for the object at a path."""
        pass

    def iterobjects(self) -> Iterable[Tuple[bytes, bytes, int]]:
        """Iterate over path, sha, mode tuples for use with commit_tree."""
        pass

    def clear(self):
        """Remove all contents from this index."""
        pass

    def __setitem__(self, name: bytes, value: Union[IndexEntry, ConflictedIndexEntry]) -> None:
        assert isinstance(name, bytes)
        self._byname[name] = value

    def __delitem__(self, name: bytes) -> None:
        del self._byname[name]

    def changes_from_tree(self, object_store, tree: ObjectID, want_unchanged: bool=False):
        """Find the differences between the contents of this index and a tree.

        Args:
          object_store: Object store to use for retrieving tree contents
          tree: SHA1 of the root tree
          want_unchanged: Whether unchanged files should be reported
        Returns: Iterator over tuples with (oldpath, newpath), (oldmode,
            newmode), (oldsha, newsha)
        """
        pass

    def commit(self, object_store):
        """Create a new tree from an index.

        Args:
          object_store: Object store to save the tree in
        Returns:
          Root tree SHA
        """
        pass

def commit_tree(object_store: ObjectContainer, blobs: Iterable[Tuple[bytes, bytes, int]]) -> bytes:
    """Commit a new tree.

    Args:
      object_store: Object store to add trees to
      blobs: Iterable over blob path, sha, mode entries
    Returns:
      SHA1 of the created tree.
    """
    pass

def commit_index(object_store: ObjectContainer, index: Index) -> bytes:
    """Create a new tree from an index.

    Args:
      object_store: Object store to save the tree in
      index: Index file
    Note: This function is deprecated, use index.commit() instead.
    Returns: Root tree sha.
    """
    pass

def changes_from_tree(names: Iterable[bytes], lookup_entry: Callable[[bytes], Tuple[bytes, int]], object_store: ObjectContainer, tree: Optional[bytes], want_unchanged=False) -> Iterable[Tuple[Tuple[Optional[bytes], Optional[bytes]], Tuple[Optional[int], Optional[int]], Tuple[Optional[bytes], Optional[bytes]]]]:
    """Find the differences between the contents of a tree and
    a working copy.

    Args:
      names: Iterable of names in the working copy
      lookup_entry: Function to lookup an entry in the working copy
      object_store: Object store to use for retrieving tree contents
      tree: SHA1 of the root tree, or None for an empty tree
      want_unchanged: Whether unchanged files should be reported
    Returns: Iterator over tuples with (oldpath, newpath), (oldmode, newmode),
        (oldsha, newsha)
    """
    pass

def index_entry_from_stat(stat_val, hex_sha: bytes, mode: Optional[int]=None):
    """Create a new index entry from a stat value.

    Args:
      stat_val: POSIX stat_result instance
      hex_sha: Hex sha of the object
    """
    pass
if sys.platform == 'win32':

    class WindowsSymlinkPermissionError(PermissionError):

        def __init__(self, errno, msg, filename) -> None:
            super(PermissionError, self).__init__(errno, f'Unable to create symlink; do you have developer mode enabled? {msg}', filename)
else:
    symlink = os.symlink

def build_file_from_blob(blob: Blob, mode: int, target_path: bytes, *, honor_filemode=True, tree_encoding='utf-8', symlink_fn=None):
    """Build a file or symlink on disk based on a Git object.

    Args:
      blob: The git object
      mode: File mode
      target_path: Path to write to
      honor_filemode: An optional flag to honor core.filemode setting in
        config file, default is core.filemode=True, change executable bit
      symlink: Function to use for creating symlinks
    Returns: stat object for the file
    """
    pass
INVALID_DOTNAMES = (b'.git', b'.', b'..', b'')

def validate_path(path: bytes, element_validator=validate_path_element_default) -> bool:
    """Default path validator that just checks for .git/."""
    pass

def build_index_from_tree(root_path: Union[str, bytes], index_path: Union[str, bytes], object_store: ObjectContainer, tree_id: bytes, honor_filemode: bool=True, validate_path_element=validate_path_element_default, symlink_fn=None):
    """Generate and materialize index from a tree.

    Args:
      tree_id: Tree to materialize
      root_path: Target dir for materialized index files
      index_path: Target path for generated index
      object_store: Non-empty object store holding tree contents
      honor_filemode: An optional flag to honor core.filemode setting in
        config file, default is core.filemode=True, change executable bit
      validate_path_element: Function to validate path elements to check
        out; default just refuses .git and .. directories.

    Note: existing index is wiped and contents are not merged
        in a working dir. Suitable only for fresh clones.
    """
    pass

def blob_from_path_and_mode(fs_path: bytes, mode: int, tree_encoding='utf-8'):
    """Create a blob from a path and a stat object.

    Args:
      fs_path: Full file system path to file
      mode: File mode
    Returns: A `Blob` object
    """
    pass

def blob_from_path_and_stat(fs_path: bytes, st, tree_encoding='utf-8'):
    """Create a blob from a path and a stat object.

    Args:
      fs_path: Full file system path to file
      st: A stat object
    Returns: A `Blob` object
    """
    pass

def read_submodule_head(path: Union[str, bytes]) -> Optional[bytes]:
    """Read the head commit of a submodule.

    Args:
      path: path to the submodule
    Returns: HEAD sha, None if not a valid head/repository
    """
    pass

def _has_directory_changed(tree_path: bytes, entry):
    """Check if a directory has changed after getting an error.

    When handling an error trying to create a blob from a path, call this
    function. It will check if the path is a directory. If it's a directory
    and a submodule, check the submodule head to see if it's has changed. If
    not, consider the file as changed as Git tracked a file and not a
    directory.

    Return true if the given path should be considered as changed and False
    otherwise or if the path is not a directory.
    """
    pass

def get_unstaged_changes(index: Index, root_path: Union[str, bytes], filter_blob_callback=None):
    """Walk through an index and check for differences against working tree.

    Args:
      index: index to check
      root_path: path in which to find files
    Returns: iterator over paths with unstaged changes
    """
    pass
os_sep_bytes = os.sep.encode('ascii')

def _tree_to_fs_path(root_path: bytes, tree_path: bytes):
    """Convert a git tree path to a file system path.

    Args:
      root_path: Root filesystem path
      tree_path: Git tree path as bytes

    Returns: File system path.
    """
    pass

def _fs_to_tree_path(fs_path: Union[str, bytes]) -> bytes:
    """Convert a file system path to a git tree path.

    Args:
      fs_path: File system path.

    Returns:  Git tree path as bytes
    """
    pass

def index_entry_from_path(path: bytes, object_store: Optional[ObjectContainer]=None) -> Optional[IndexEntry]:
    """Create an index from a filesystem path.

    This returns an index value for files, symlinks
    and tree references. for directories and
    non-existent files it returns None

    Args:
      path: Path to create an index entry for
      object_store: Optional object store to
        save new blobs in
    Returns: An index entry; None for directories
    """
    pass

def iter_fresh_entries(paths: Iterable[bytes], root_path: bytes, object_store: Optional[ObjectContainer]=None) -> Iterator[Tuple[bytes, Optional[IndexEntry]]]:
    """Iterate over current versions of index entries on disk.

    Args:
      paths: Paths to iterate over
      root_path: Root path to access from
      object_store: Optional store to save new blobs in
    Returns: Iterator over path, index_entry
    """
    pass

def iter_fresh_objects(paths: Iterable[bytes], root_path: bytes, include_deleted=False, object_store=None) -> Iterator[Tuple[bytes, Optional[bytes], Optional[int]]]:
    """Iterate over versions of objects on disk referenced by index.

    Args:
      root_path: Root path to access from
      include_deleted: Include deleted entries with sha and
        mode set to None
      object_store: Optional object store to report new items to
    Returns: Iterator over path, sha, mode
    """
    pass

def refresh_index(index: Index, root_path: bytes):
    """Refresh the contents of an index.

    This is the equivalent to running 'git commit -a'.

    Args:
      index: Index to update
      root_path: Root filesystem path
    """
    pass

class locked_index:
    """Lock the index while making modifications.

    Works as a context manager.
    """

    def __init__(self, path: Union[bytes, str]) -> None:
        self._path = path

    def __enter__(self):
        self._file = GitFile(self._path, 'wb')
        self._index = Index(self._path)
        return self._index

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self._file.abort()
            return
        try:
            f = SHA1Writer(self._file)
            write_index_dict(f, self._index._byname)
        except BaseException:
            self._file.abort()
        else:
            f.close()