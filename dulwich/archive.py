"""Generates tarballs for Git trees."""
import posixpath
import stat
import struct
import tarfile
from contextlib import closing
from io import BytesIO
from os import SEEK_END

class ChunkedBytesIO:
    """Turn a list of bytestrings into a file-like object.

    This is similar to creating a `BytesIO` from a concatenation of the
    bytestring list, but saves memory by NOT creating one giant bytestring
    first::

        BytesIO(b''.join(list_of_bytestrings)) =~= ChunkedBytesIO(
            list_of_bytestrings)
    """

    def __init__(self, contents) -> None:
        self.contents = contents
        self.pos = (0, 0)

def tar_stream(store, tree, mtime, prefix=b'', format=''):
    """Generate a tar stream for the contents of a Git tree.

    Returns a generator that lazily assembles a .tar.gz archive, yielding it in
    pieces (bytestrings). To obtain the complete .tar.gz binary file, simply
    concatenate these chunks.

    Args:
      store: Object store to retrieve objects from
      tree: Tree object for the tree root
      mtime: UNIX timestamp that is assigned as the modification time for
        all files, and the gzip header modification time if format='gz'
      format: Optional compression format for tarball
    Returns:
      Bytestrings
    """
    pass

def _walk_tree(store, tree, root=b''):
    """Recursively walk a dulwich Tree, yielding tuples of
    (absolute path, TreeEntry) along the way.
    """
    pass