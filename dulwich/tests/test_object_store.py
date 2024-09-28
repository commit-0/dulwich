"""Tests for the object store interface."""
from unittest import skipUnless
from dulwich.index import commit_tree
from dulwich.object_store import iter_tree_contents, peel_sha
from dulwich.objects import Blob, TreeEntry
from dulwich.protocol import DEPTH_INFINITE
from .utils import make_object, make_tag
try:
    from unittest.mock import patch
except ImportError:
    patch = None
testobject = make_object(Blob, data=b'yummy data')

class ObjectStoreTests:

    def test_store_resilience(self):
        """Test if updating an existing stored object doesn't erase the
        object from the store.
        """
        pass

class PackBasedObjectStoreTests(ObjectStoreTests):
    pass