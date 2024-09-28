"""Storage of repositories on GCS."""
import posixpath
import tempfile
from ..object_store import BucketBasedObjectStore
from ..pack import PACK_SPOOL_FILE_MAX_SIZE, Pack, PackData, load_pack_index_file

class GcsObjectStore(BucketBasedObjectStore):

    def __init__(self, bucket, subpath='') -> None:
        super().__init__()
        self.bucket = bucket
        self.subpath = subpath

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.bucket!r}, subpath={self.subpath!r})'