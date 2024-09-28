"""Ref handling."""
import os
import warnings
from contextlib import suppress
from typing import Any, Dict, Optional, Set
from .errors import PackedRefsException, RefFormatError
from .file import GitFile, ensure_dir_exists
from .objects import ZERO_SHA, ObjectID, Tag, git_line, valid_hexsha
from .pack import ObjectContainer
Ref = bytes
HEADREF = b'HEAD'
SYMREF = b'ref: '
LOCAL_BRANCH_PREFIX = b'refs/heads/'
LOCAL_TAG_PREFIX = b'refs/tags/'
LOCAL_REMOTE_PREFIX = b'refs/remotes/'
BAD_REF_CHARS = set(b'\x7f ~^:?*[')
PEELED_TAG_SUFFIX = b'^{}'
ANNOTATED_TAG_SUFFIX = PEELED_TAG_SUFFIX

class SymrefLoop(Exception):
    """There is a loop between one or more symrefs."""

    def __init__(self, ref, depth) -> None:
        self.ref = ref
        self.depth = depth

def parse_symref_value(contents):
    """Parse a symref value.

    Args:
      contents: Contents to parse
    Returns: Destination
    """
    pass

def check_ref_format(refname: Ref):
    """Check if a refname is correctly formatted.

    Implements all the same rules as git-check-ref-format[1].

    [1]
    http://www.kernel.org/pub/software/scm/git/docs/git-check-ref-format.html

    Args:
      refname: The refname to check
    Returns: True if refname is valid, False otherwise
    """
    pass

class RefsContainer:
    """A container for refs."""

    def __init__(self, logger=None) -> None:
        self._logger = logger

    def set_symbolic_ref(self, name, other, committer=None, timestamp=None, timezone=None, message=None):
        """Make a ref point at another ref.

        Args:
          name: Name of the ref to set
          other: Name of the ref to point at
          message: Optional message
        """
        pass

    def get_packed_refs(self):
        """Get contents of the packed-refs file.

        Returns: Dictionary mapping ref names to SHA1s

        Note: Will return an empty dictionary when no packed-refs file is
            present.
        """
        pass

    def add_packed_refs(self, new_refs: Dict[Ref, Optional[ObjectID]]):
        """Add the given refs as packed refs.

        Args:
          new_refs: A mapping of ref names to targets; if a target is None that
            means remove the ref
        """
        pass

    def get_peeled(self, name):
        """Return the cached peeled value of a ref, if available.

        Args:
          name: Name of the ref to peel
        Returns: The peeled value of the ref. If the ref is known not point to
            a tag, this will be the SHA the ref refers to. If the ref may point
            to a tag, but no cached information is available, None is returned.
        """
        pass

    def allkeys(self):
        """All refs present in this container."""
        pass

    def __iter__(self):
        return iter(self.allkeys())

    def keys(self, base=None):
        """Refs present in this container.

        Args:
          base: An optional base to return refs under.
        Returns: An unsorted set of valid refs in this container, including
            packed refs.
        """
        pass

    def subkeys(self, base):
        """Refs present in this container under a base.

        Args:
          base: The base to return refs under.
        Returns: A set of valid refs in this container under the base; the base
            prefix is stripped from the ref names returned.
        """
        pass

    def as_dict(self, base=None):
        """Return the contents of this container as a dictionary."""
        pass

    def _check_refname(self, name):
        """Ensure a refname is valid and lives in refs or is HEAD.

        HEAD is not a valid refname according to git-check-ref-format, but this
        class needs to be able to touch HEAD. Also, check_ref_format expects
        refnames without the leading 'refs/', but this class requires that
        so it cannot touch anything outside the refs dir (or HEAD).

        Args:
          name: The name of the reference.

        Raises:
          KeyError: if a refname is not HEAD or is otherwise not valid.
        """
        pass

    def read_ref(self, refname):
        """Read a reference without following any references.

        Args:
          refname: The name of the reference
        Returns: The contents of the ref file, or None if it does
            not exist.
        """
        pass

    def read_loose_ref(self, name):
        """Read a loose reference and return its contents.

        Args:
          name: the refname to read
        Returns: The contents of the ref file, or None if it does
            not exist.
        """
        pass

    def follow(self, name):
        """Follow a reference name.

        Returns: a tuple of (refnames, sha), wheres refnames are the names of
            references in the chain
        """
        pass

    def __contains__(self, refname) -> bool:
        if self.read_ref(refname):
            return True
        return False

    def __getitem__(self, name):
        """Get the SHA1 for a reference name.

        This method follows all symbolic references.
        """
        _, sha = self.follow(name)
        if sha is None:
            raise KeyError(name)
        return sha

    def set_if_equals(self, name, old_ref, new_ref, committer=None, timestamp=None, timezone=None, message=None):
        """Set a refname to new_ref only if it currently equals old_ref.

        This method follows all symbolic references if applicable for the
        subclass, and can be used to perform an atomic compare-and-swap
        operation.

        Args:
          name: The refname to set.
          old_ref: The old sha the refname must refer to, or None to set
            unconditionally.
          new_ref: The new sha the refname will refer to.
          message: Message for reflog
        Returns: True if the set was successful, False otherwise.
        """
        pass

    def add_if_new(self, name, ref, committer=None, timestamp=None, timezone=None, message=None):
        """Add a new reference only if it does not already exist.

        Args:
          name: Ref name
          ref: Ref value
        """
        pass

    def __setitem__(self, name, ref) -> None:
        """Set a reference name to point to the given SHA1.

        This method follows all symbolic references if applicable for the
        subclass.

        Note: This method unconditionally overwrites the contents of a
            reference. To update atomically only if the reference has not
            changed, use set_if_equals().

        Args:
          name: The refname to set.
          ref: The new sha the refname will refer to.
        """
        self.set_if_equals(name, None, ref)

    def remove_if_equals(self, name, old_ref, committer=None, timestamp=None, timezone=None, message=None):
        """Remove a refname only if it currently equals old_ref.

        This method does not follow symbolic references, even if applicable for
        the subclass. It can be used to perform an atomic compare-and-delete
        operation.

        Args:
          name: The refname to delete.
          old_ref: The old sha the refname must refer to, or None to
            delete unconditionally.
          message: Message for reflog
        Returns: True if the delete was successful, False otherwise.
        """
        pass

    def __delitem__(self, name) -> None:
        """Remove a refname.

        This method does not follow symbolic references, even if applicable for
        the subclass.

        Note: This method unconditionally deletes the contents of a reference.
            To delete atomically only if the reference has not changed, use
            remove_if_equals().

        Args:
          name: The refname to delete.
        """
        self.remove_if_equals(name, None)

    def get_symrefs(self):
        """Get a dict with all symrefs in this container.

        Returns: Dictionary mapping source ref to target ref
        """
        pass

class DictRefsContainer(RefsContainer):
    """RefsContainer backed by a simple dict.

    This container does not support symbolic or packed references and is not
    threadsafe.
    """

    def __init__(self, refs, logger=None) -> None:
        super().__init__(logger=logger)
        self._refs = refs
        self._peeled: Dict[bytes, ObjectID] = {}
        self._watchers: Set[Any] = set()

    def _update(self, refs):
        """Update multiple refs; intended only for testing."""
        pass

    def _update_peeled(self, peeled):
        """Update cached peeled refs; intended only for testing."""
        pass

class InfoRefsContainer(RefsContainer):
    """Refs container that reads refs from a info/refs file."""

    def __init__(self, f) -> None:
        self._refs = {}
        self._peeled = {}
        for line in f.readlines():
            sha, name = line.rstrip(b'\n').split(b'\t')
            if name.endswith(PEELED_TAG_SUFFIX):
                name = name[:-3]
                if not check_ref_format(name):
                    raise ValueError(f'invalid ref name {name!r}')
                self._peeled[name] = sha
            else:
                if not check_ref_format(name):
                    raise ValueError(f'invalid ref name {name!r}')
                self._refs[name] = sha

class DiskRefsContainer(RefsContainer):
    """Refs container that reads refs from disk."""

    def __init__(self, path, worktree_path=None, logger=None) -> None:
        super().__init__(logger=logger)
        if getattr(path, 'encode', None) is not None:
            path = os.fsencode(path)
        self.path = path
        if worktree_path is None:
            worktree_path = path
        if getattr(worktree_path, 'encode', None) is not None:
            worktree_path = os.fsencode(worktree_path)
        self.worktree_path = worktree_path
        self._packed_refs = None
        self._peeled_refs = None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path!r})'

    def refpath(self, name):
        """Return the disk path of a ref."""
        pass

    def get_packed_refs(self):
        """Get contents of the packed-refs file.

        Returns: Dictionary mapping ref names to SHA1s

        Note: Will return an empty dictionary when no packed-refs file is
            present.
        """
        pass

    def add_packed_refs(self, new_refs: Dict[Ref, Optional[ObjectID]]):
        """Add the given refs as packed refs.

        Args:
          new_refs: A mapping of ref names to targets; if a target is None that
            means remove the ref
        """
        pass

    def get_peeled(self, name):
        """Return the cached peeled value of a ref, if available.

        Args:
          name: Name of the ref to peel
        Returns: The peeled value of the ref. If the ref is known not point to
            a tag, this will be the SHA the ref refers to. If the ref may point
            to a tag, but no cached information is available, None is returned.
        """
        pass

    def read_loose_ref(self, name):
        """Read a reference file and return its contents.

        If the reference file a symbolic reference, only read the first line of
        the file. Otherwise, only read the first 40 bytes.

        Args:
          name: the refname to read, relative to refpath
        Returns: The contents of the ref file, or None if the file does not
            exist.

        Raises:
          IOError: if any other error occurs
        """
        pass

    def set_symbolic_ref(self, name, other, committer=None, timestamp=None, timezone=None, message=None):
        """Make a ref point at another ref.

        Args:
          name: Name of the ref to set
          other: Name of the ref to point at
          message: Optional message to describe the change
        """
        pass

    def set_if_equals(self, name, old_ref, new_ref, committer=None, timestamp=None, timezone=None, message=None):
        """Set a refname to new_ref only if it currently equals old_ref.

        This method follows all symbolic references, and can be used to perform
        an atomic compare-and-swap operation.

        Args:
          name: The refname to set.
          old_ref: The old sha the refname must refer to, or None to set
            unconditionally.
          new_ref: The new sha the refname will refer to.
          message: Set message for reflog
        Returns: True if the set was successful, False otherwise.
        """
        pass

    def add_if_new(self, name: bytes, ref: bytes, committer=None, timestamp=None, timezone=None, message: Optional[bytes]=None):
        """Add a new reference only if it does not already exist.

        This method follows symrefs, and only ensures that the last ref in the
        chain does not exist.

        Args:
          name: The refname to set.
          ref: The new sha the refname will refer to.
          message: Optional message for reflog
        Returns: True if the add was successful, False otherwise.
        """
        pass

    def remove_if_equals(self, name, old_ref, committer=None, timestamp=None, timezone=None, message=None):
        """Remove a refname only if it currently equals old_ref.

        This method does not follow symbolic references. It can be used to
        perform an atomic compare-and-delete operation.

        Args:
          name: The refname to delete.
          old_ref: The old sha the refname must refer to, or None to
            delete unconditionally.
          message: Optional message
        Returns: True if the delete was successful, False otherwise.
        """
        pass

def _split_ref_line(line):
    """Split a single ref line into a tuple of SHA1 and name."""
    pass

def read_packed_refs(f):
    """Read a packed refs file.

    Args:
      f: file-like object to read from
    Returns: Iterator over tuples with SHA1s and ref names.
    """
    pass

def read_packed_refs_with_peeled(f):
    """Read a packed refs file including peeled refs.

    Assumes the "# pack-refs with: peeled" line was already read. Yields tuples
    with ref names, SHA1s, and peeled SHA1s (or None).

    Args:
      f: file-like object to read from, seek'ed to the second line
    """
    pass

def write_packed_refs(f, packed_refs, peeled_refs=None):
    """Write a packed refs file.

    Args:
      f: empty file-like object to write to
      packed_refs: dict of refname to sha of packed refs to write
      peeled_refs: dict of refname to peeled value of sha
    """
    pass

def write_info_refs(refs, store: ObjectContainer):
    """Generate info refs."""
    pass

def strip_peeled_refs(refs):
    """Remove all peeled refs."""
    pass

def _set_default_branch(refs: RefsContainer, origin: bytes, origin_head: bytes, branch: bytes, ref_message: Optional[bytes]) -> bytes:
    """Set the default branch."""
    pass