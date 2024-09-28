"""Utility functions common to Dulwich tests."""
import datetime
import os
import shutil
import tempfile
import time
import types
import warnings
from unittest import SkipTest
from dulwich.index import commit_tree
from dulwich.objects import Commit, FixedSha, Tag, object_class
from dulwich.pack import DELTA_TYPES, OFS_DELTA, REF_DELTA, SHA1Writer, create_delta, obj_sha, write_pack_header, write_pack_object
from dulwich.repo import Repo
F = 33188

def open_repo(name, temp_dir=None):
    """Open a copy of a repo in a temporary directory.

    Use this function for accessing repos in dulwich/tests/data/repos to avoid
    accidentally or intentionally modifying those repos in place. Use
    tear_down_repo to delete any temp files created.

    Args:
      name: The name of the repository, relative to
        dulwich/tests/data/repos
      temp_dir: temporary directory to initialize to. If not provided, a
        temporary directory will be created.
    Returns: An initialized Repo object that lives in a temporary directory.
    """
    pass

def tear_down_repo(repo):
    """Tear down a test repository."""
    pass

def make_object(cls, **attrs):
    """Make an object for testing and assign some members.

    This method creates a new subclass to allow arbitrary attribute
    reassignment, which is not otherwise possible with objects having
    __slots__.

    Args:
      attrs: dict of attributes to set on the new object.
    Returns: A newly initialized object of type cls.
    """
    pass

def make_commit(**attrs):
    """Make a Commit object with a default set of members.

    Args:
      attrs: dict of attributes to overwrite from the default values.
    Returns: A newly initialized Commit object.
    """
    pass

def make_tag(target, **attrs):
    """Make a Tag object with a default set of values.

    Args:
      target: object to be tagged (Commit, Blob, Tree, etc)
      attrs: dict of attributes to overwrite from the default values.
    Returns: A newly initialized Tag object.
    """
    pass

def functest_builder(method, func):
    """Generate a test method that tests the given function."""
    pass

def ext_functest_builder(method, func):
    """Generate a test method that tests the given extension function.

    This is intended to generate test methods that test both a pure-Python
    version and an extension version using common test code. The extension test
    will raise SkipTest if the extension is not found.

    Sample usage:

    class MyTest(TestCase);
        def _do_some_test(self, func_impl):
            self.assertEqual('foo', func_impl())

        test_foo = functest_builder(_do_some_test, foo_py)
        test_foo_extension = ext_functest_builder(_do_some_test, _foo_c)

    Args:
      method: The method to run. It must must two parameters, self and the
        function implementation to test.
      func: The function implementation to pass to method.
    """
    pass

def build_pack(f, objects_spec, store=None):
    """Write test pack data from a concise spec.

    Args:
      f: A file-like object to write the pack to.
      objects_spec: A list of (type_num, obj). For non-delta types, obj
        is the string of that object's data.
        For delta types, obj is a tuple of (base, data), where:

        * base can be either an index in objects_spec of the base for that
        * delta; or for a ref delta, a SHA, in which case the resulting pack
        * will be thin and the base will be an external ref.
        * data is a string of the full, non-deltified data for that object.

        Note that offsets/refs and deltas are computed within this function.
      store: An optional ObjectStore for looking up external refs.
    Returns: A list of tuples in the order specified by objects_spec:
        (offset, type num, data, sha, CRC32)
    """
    pass

def build_commit_graph(object_store, commit_spec, trees=None, attrs=None):
    """Build a commit graph from a concise specification.

    Sample usage:
    >>> c1, c2, c3 = build_commit_graph(store, [[1], [2, 1], [3, 1, 2]])
    >>> store[store[c3].parents[0]] == c1
    True
    >>> store[store[c3].parents[1]] == c2
    True

    If not otherwise specified, commits will refer to the empty tree and have
    commit times increasing in the same order as the commit spec.

    Args:
      object_store: An ObjectStore to commit objects to.
      commit_spec: An iterable of iterables of ints defining the commit
        graph. Each entry defines one commit, and entries must be in
        topological order. The first element of each entry is a commit number,
        and the remaining elements are its parents. The commit numbers are only
        meaningful for the call to make_commits; since real commit objects are
        created, they will get created with real, opaque SHAs.
      trees: An optional dict of commit number -> tree spec for building
        trees for commits. The tree spec is an iterable of (path, blob, mode)
        or (path, blob) entries; if mode is omitted, it defaults to the normal
        file mode (0100644).
      attrs: A dict of commit number -> (dict of attribute -> value) for
        assigning additional values to the commits.
    Returns: The list of commit objects created.

    Raises:
      ValueError: If an undefined commit identifier is listed as a parent.
    """
    pass

def setup_warning_catcher():
    """Wrap warnings.showwarning with code that records warnings."""
    pass