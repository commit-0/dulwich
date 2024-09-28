"""Classes for dealing with git am-style patches.

These patches are basically unified diffs with some extra metadata tacked
on.
"""
import email.parser
import time
from difflib import SequenceMatcher
from typing import BinaryIO, Optional, TextIO, Union
from .objects import S_ISGITLINK, Blob, Commit
from .pack import ObjectContainer
FIRST_FEW_BYTES = 8000

def write_commit_patch(f, commit, contents, progress, version=None, encoding=None):
    """Write a individual file patch.

    Args:
      commit: Commit object
      progress: Tuple with current patch number and total.

    Returns:
      tuple with filename and contents
    """
    pass

def get_summary(commit):
    """Determine the summary line for use in a filename.

    Args:
      commit: Commit
    Returns: Summary string
    """
    pass

def _format_range_unified(start, stop):
    """Convert range to the "ed" format."""
    pass

def unified_diff(a, b, fromfile='', tofile='', fromfiledate='', tofiledate='', n=3, lineterm='\n', tree_encoding='utf-8', output_encoding='utf-8'):
    """difflib.unified_diff that can detect "No newline at end of file" as
    original "git diff" does.

    Based on the same function in Python2.7 difflib.py
    """
    pass

def is_binary(content):
    """See if the first few bytes contain any null characters.

    Args:
      content: Bytestring to check for binary content
    """
    pass

def write_object_diff(f, store: ObjectContainer, old_file, new_file, diff_binary=False):
    """Write the diff for an object.

    Args:
      f: File-like object to write to
      store: Store to retrieve objects from, if necessary
      old_file: (path, mode, hexsha) tuple
      new_file: (path, mode, hexsha) tuple
      diff_binary: Whether to diff files even if they
        are considered binary files by is_binary().

    Note: the tuple elements should be None for nonexistent files
    """
    pass

def gen_diff_header(paths, modes, shas):
    """Write a blob diff header.

    Args:
      paths: Tuple with old and new path
      modes: Tuple with old and new modes
      shas: Tuple with old and new shas
    """
    pass

def write_blob_diff(f, old_file, new_file):
    """Write blob diff.

    Args:
      f: File-like object to write to
      old_file: (path, mode, hexsha) tuple (None if nonexisting)
      new_file: (path, mode, hexsha) tuple (None if nonexisting)

    Note: The use of write_object_diff is recommended over this function.
    """
    pass

def write_tree_diff(f, store, old_tree, new_tree, diff_binary=False):
    """Write tree diff.

    Args:
      f: File-like object to write to.
      old_tree: Old tree id
      new_tree: New tree id
      diff_binary: Whether to diff files even if they
        are considered binary files by is_binary().
    """
    pass

def git_am_patch_split(f: Union[TextIO, BinaryIO], encoding: Optional[str]=None):
    """Parse a git-am-style patch and split it up into bits.

    Args:
      f: File-like object to parse
      encoding: Encoding to use when creating Git objects
    Returns: Tuple with commit object, diff contents and git version
    """
    pass

def parse_patch_message(msg, encoding=None):
    """Extract a Commit object and patch from an e-mail message.

    Args:
      msg: An email message (email.message.Message)
      encoding: Encoding to use to encode Git commits
    Returns: Tuple with commit object, diff contents and git version
    """
    pass