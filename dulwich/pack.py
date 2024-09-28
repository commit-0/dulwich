"""Classes for dealing with packed git objects.

A pack is a compact representation of a bunch of objects, stored
using deltas where possible.

They have two parts, the pack file, which stores the data, and an index
that tells you where the data is.

To find an object you look in all of the index files 'til you find a
match for the object name. You then use the pointer got from this as
a pointer in to the corresponding packfile.
"""
import binascii
from collections import defaultdict, deque
from contextlib import suppress
from io import BytesIO, UnsupportedOperation
try:
    from cdifflib import CSequenceMatcher as SequenceMatcher
except ModuleNotFoundError:
    from difflib import SequenceMatcher
import os
import struct
import sys
import warnings
import zlib
from hashlib import sha1
from itertools import chain
from os import SEEK_CUR, SEEK_END
from struct import unpack_from
from typing import BinaryIO, Callable, Deque, Dict, Generic, Iterable, Iterator, List, Optional, Protocol, Sequence, Set, Tuple, TypeVar, Union
try:
    import mmap
except ImportError:
    has_mmap = False
else:
    has_mmap = True
if sys.platform == 'Plan9':
    has_mmap = False
from .errors import ApplyDeltaError, ChecksumMismatch
from .file import GitFile
from .lru_cache import LRUSizeCache
from .objects import ObjectID, ShaFile, hex_to_sha, object_header, sha_to_hex
OFS_DELTA = 6
REF_DELTA = 7
DELTA_TYPES = (OFS_DELTA, REF_DELTA)
DEFAULT_PACK_DELTA_WINDOW_SIZE = 10
PACK_SPOOL_FILE_MAX_SIZE = 16 * 1024 * 1024
OldUnpackedObject = Union[Tuple[Union[bytes, int], List[bytes]], List[bytes]]
ResolveExtRefFn = Callable[[bytes], Tuple[int, OldUnpackedObject]]
ProgressFn = Callable[[int, str], None]
PackHint = Tuple[int, Optional[bytes]]

class UnresolvedDeltas(Exception):
    """Delta objects could not be resolved."""

    def __init__(self, shas):
        self.shas = shas

class ObjectContainer(Protocol):

    def add_object(self, obj: ShaFile) -> None:
        """Add a single object to this object store."""
        pass

    def add_objects(self, objects: Sequence[Tuple[ShaFile, Optional[str]]], progress: Optional[Callable[[str], None]]=None) -> None:
        """Add a set of objects to this object store.

        Args:
          objects: Iterable over a list of (object, path) tuples
        """
        pass

    def __contains__(self, sha1: bytes) -> bool:
        """Check if a hex sha is present."""

    def __getitem__(self, sha1: bytes) -> ShaFile:
        """Retrieve an object."""

class PackedObjectContainer(ObjectContainer):

    def get_unpacked_object(self, sha1: bytes, *, include_comp: bool=False) -> 'UnpackedObject':
        """Get a raw unresolved object."""
        pass

class UnpackedObjectStream:

    def __iter__(self) -> Iterator['UnpackedObject']:
        raise NotImplementedError(self.__iter__)

    def __len__(self) -> int:
        raise NotImplementedError(self.__len__)

def take_msb_bytes(read: Callable[[int], bytes], crc32: Optional[int]=None) -> Tuple[List[int], Optional[int]]:
    """Read bytes marked with most significant bit.

    Args:
      read: Read function
    """
    pass

class PackFileDisappeared(Exception):

    def __init__(self, obj) -> None:
        self.obj = obj

class UnpackedObject:
    """Class encapsulating an object unpacked from a pack file.

    These objects should only be created from within unpack_object. Most
    members start out as empty and are filled in at various points by
    read_zlib_chunks, unpack_object, DeltaChainIterator, etc.

    End users of this object should take care that the function they're getting
    this object from is guaranteed to set the members they need.
    """
    __slots__ = ['offset', '_sha', 'obj_type_num', 'obj_chunks', 'pack_type_num', 'delta_base', 'comp_chunks', 'decomp_chunks', 'decomp_len', 'crc32']
    obj_type_num: Optional[int]
    obj_chunks: Optional[List[bytes]]
    delta_base: Union[None, bytes, int]
    decomp_chunks: List[bytes]
    comp_chunks: Optional[List[bytes]]

    def __init__(self, pack_type_num, *, delta_base=None, decomp_len=None, crc32=None, sha=None, decomp_chunks=None, offset=None) -> None:
        self.offset = offset
        self._sha = sha
        self.pack_type_num = pack_type_num
        self.delta_base = delta_base
        self.comp_chunks = None
        self.decomp_chunks: List[bytes] = decomp_chunks or []
        if decomp_chunks is not None and decomp_len is None:
            self.decomp_len = sum(map(len, decomp_chunks))
        else:
            self.decomp_len = decomp_len
        self.crc32 = crc32
        if pack_type_num in DELTA_TYPES:
            self.obj_type_num = None
            self.obj_chunks = None
        else:
            self.obj_type_num = pack_type_num
            self.obj_chunks = self.decomp_chunks
            self.delta_base = delta_base

    def sha(self):
        """Return the binary SHA of this object."""
        pass

    def sha_file(self):
        """Return a ShaFile from this object."""
        pass

    def _obj(self) -> OldUnpackedObject:
        """Return the decompressed chunks, or (delta base, delta chunks)."""
        pass

    def __eq__(self, other):
        if not isinstance(other, UnpackedObject):
            return False
        for slot in self.__slots__:
            if getattr(self, slot) != getattr(other, slot):
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self) -> str:
        data = [f'{s}={getattr(self, s)!r}' for s in self.__slots__]
        return '{}({})'.format(self.__class__.__name__, ', '.join(data))
_ZLIB_BUFSIZE = 4096

def read_zlib_chunks(read_some: Callable[[int], bytes], unpacked: UnpackedObject, include_comp: bool=False, buffer_size: int=_ZLIB_BUFSIZE) -> bytes:
    """Read zlib data from a buffer.

    This function requires that the buffer have additional data following the
    compressed data, which is guaranteed to be the case for git pack files.

    Args:
      read_some: Read function that returns at least one byte, but may
        return less than the requested size.
      unpacked: An UnpackedObject to write result data to. If its crc32
        attr is not None, the CRC32 of the compressed bytes will be computed
        using this starting CRC32.
        After this function, will have the following attrs set:
        * comp_chunks    (if include_comp is True)
        * decomp_chunks
        * decomp_len
        * crc32
      include_comp: If True, include compressed data in the result.
      buffer_size: Size of the read buffer.
    Returns: Leftover unused data from the decompression.

    Raises:
      zlib.error: if a decompression error occurred.
    """
    pass

def iter_sha1(iter):
    """Return the hexdigest of the SHA1 over a set of names.

    Args:
      iter: Iterator over string objects
    Returns: 40-byte hex sha1 digest
    """
    pass

def load_pack_index(path):
    """Load an index file by path.

    Args:
      path: Path to the index file
    Returns: A PackIndex loaded from the given path
    """
    pass

def load_pack_index_file(path, f):
    """Load an index file from a file-like object.

    Args:
      path: Path for the index file
      f: File-like object
    Returns: A PackIndex loaded from the given file
    """
    pass

def bisect_find_sha(start, end, sha, unpack_name):
    """Find a SHA in a data blob with sorted SHAs.

    Args:
      start: Start index of range to search
      end: End index of range to search
      sha: Sha to find
      unpack_name: Callback to retrieve SHA by index
    Returns: Index of the SHA, or None if it wasn't found
    """
    pass
PackIndexEntry = Tuple[bytes, int, Optional[int]]

class PackIndex:
    """An index in to a packfile.

    Given a sha id of an object a pack index can tell you the location in the
    packfile of that object if it has it.
    """

    def __eq__(self, other):
        if not isinstance(other, PackIndex):
            return False
        for (name1, _, _), (name2, _, _) in zip(self.iterentries(), other.iterentries()):
            if name1 != name2:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self) -> int:
        """Return the number of entries in this pack index."""
        raise NotImplementedError(self.__len__)

    def __iter__(self) -> Iterator[bytes]:
        """Iterate over the SHAs in this pack."""
        return map(sha_to_hex, self._itersha())

    def iterentries(self) -> Iterator[PackIndexEntry]:
        """Iterate over the entries in this pack index.

        Returns: iterator over tuples with object name, offset in packfile and
            crc32 checksum.
        """
        pass

    def get_pack_checksum(self) -> bytes:
        """Return the SHA1 checksum stored for the corresponding packfile.

        Returns: 20-byte binary digest
        """
        pass

    def object_offset(self, sha: bytes) -> int:
        """Return the offset in to the corresponding packfile for the object.

        Given the name of an object it will return the offset that object
        lives at within the corresponding pack file. If the pack file doesn't
        have the object then None will be returned.
        """
        pass

    def object_sha1(self, index: int) -> bytes:
        """Return the SHA1 corresponding to the index in the pack file."""
        pass

    def _object_offset(self, sha: bytes) -> int:
        """See object_offset.

        Args:
          sha: A *binary* SHA string. (20 characters long)_
        """
        pass

    def objects_sha1(self) -> bytes:
        """Return the hex SHA1 over all the shas of all objects in this pack.

        Note: This is used for the filename of the pack.
        """
        pass

    def _itersha(self) -> Iterator[bytes]:
        """Yield all the SHA1's of the objects in the index, sorted."""
        pass

class MemoryPackIndex(PackIndex):
    """Pack index that is stored entirely in memory."""

    def __init__(self, entries, pack_checksum=None) -> None:
        """Create a new MemoryPackIndex.

        Args:
          entries: Sequence of name, idx, crc32 (sorted)
          pack_checksum: Optional pack checksum
        """
        self._by_sha = {}
        self._by_offset = {}
        for name, offset, crc32 in entries:
            self._by_sha[name] = offset
            self._by_offset[offset] = name
        self._entries = entries
        self._pack_checksum = pack_checksum

    def __len__(self) -> int:
        return len(self._entries)

class FilePackIndex(PackIndex):
    """Pack index that is based on a file.

    To do the loop it opens the file, and indexes first 256 4 byte groups
    with the first byte of the sha id. The value in the four byte group indexed
    is the end of the group that shares the same starting byte. Subtract one
    from the starting byte and index again to find the start of the group.
    The values are sorted by sha id within the group, so do the math to find
    the start and end offset and then bisect in to find if the value is
    present.
    """
    _fan_out_table: List[int]

    def __init__(self, filename, file=None, contents=None, size=None) -> None:
        """Create a pack index object.

        Provide it with the name of the index file to consider, and it will map
        it whenever required.
        """
        self._filename = filename
        if file is None:
            self._file = GitFile(filename, 'rb')
        else:
            self._file = file
        if contents is None:
            self._contents, self._size = _load_file_contents(self._file, size)
        else:
            self._contents, self._size = (contents, size)

    def __eq__(self, other):
        if isinstance(other, FilePackIndex) and self._fan_out_table != other._fan_out_table:
            return False
        return super().__eq__(other)

    def __len__(self) -> int:
        """Return the number of entries in this pack index."""
        return self._fan_out_table[-1]

    def _unpack_entry(self, i: int) -> PackIndexEntry:
        """Unpack the i-th entry in the index file.

        Returns: Tuple with object name (SHA), offset in pack file and CRC32
            checksum (if known).
        """
        pass

    def _unpack_name(self, i):
        """Unpack the i-th name from the index file."""
        pass

    def _unpack_offset(self, i):
        """Unpack the i-th object offset from the index file."""
        pass

    def _unpack_crc32_checksum(self, i):
        """Unpack the crc32 checksum for the ith object from the index file."""
        pass

    def iterentries(self) -> Iterator[PackIndexEntry]:
        """Iterate over the entries in this pack index.

        Returns: iterator over tuples with object name, offset in packfile and
            crc32 checksum.
        """
        pass

    def check(self) -> None:
        """Check that the stored checksum matches the actual checksum."""
        pass

    def calculate_checksum(self) -> bytes:
        """Calculate the SHA1 checksum over this pack index.

        Returns: This is a 20-byte binary digest
        """
        pass

    def get_pack_checksum(self) -> bytes:
        """Return the SHA1 checksum stored for the corresponding packfile.

        Returns: 20-byte binary digest
        """
        pass

    def get_stored_checksum(self) -> bytes:
        """Return the SHA1 checksum stored for this index.

        Returns: 20-byte binary digest
        """
        pass

    def object_offset(self, sha: bytes) -> int:
        """Return the offset in to the corresponding packfile for the object.

        Given the name of an object it will return the offset that object
        lives at within the corresponding pack file. If the pack file doesn't
        have the object then None will be returned.
        """
        pass

    def _object_offset(self, sha: bytes) -> int:
        """See object_offset.

        Args:
          sha: A *binary* SHA string. (20 characters long)_
        """
        pass

class PackIndex1(FilePackIndex):
    """Version 1 Pack Index file."""

    def __init__(self, filename: str, file=None, contents=None, size=None) -> None:
        super().__init__(filename, file, contents, size)
        self.version = 1
        self._fan_out_table = self._read_fan_out_table(0)

class PackIndex2(FilePackIndex):
    """Version 2 Pack Index file."""

    def __init__(self, filename: str, file=None, contents=None, size=None) -> None:
        super().__init__(filename, file, contents, size)
        if self._contents[:4] != b'\xfftOc':
            raise AssertionError('Not a v2 pack index file')
        self.version, = unpack_from(b'>L', self._contents, 4)
        if self.version != 2:
            raise AssertionError('Version was %d' % self.version)
        self._fan_out_table = self._read_fan_out_table(8)
        self._name_table_offset = 8 + 256 * 4
        self._crc32_table_offset = self._name_table_offset + 20 * len(self)
        self._pack_offset_table_offset = self._crc32_table_offset + 4 * len(self)
        self._pack_offset_largetable_offset = self._pack_offset_table_offset + 4 * len(self)

def read_pack_header(read) -> Tuple[int, int]:
    """Read the header of a pack file.

    Args:
      read: Read function
    Returns: Tuple of (pack version, number of objects). If no data is
        available to read, returns (None, None).
    """
    pass

def unpack_object(read_all: Callable[[int], bytes], read_some: Optional[Callable[[int], bytes]]=None, compute_crc32=False, include_comp=False, zlib_bufsize=_ZLIB_BUFSIZE) -> Tuple[UnpackedObject, bytes]:
    """Unpack a Git object.

    Args:
      read_all: Read function that blocks until the number of requested
        bytes are read.
      read_some: Read function that returns at least one byte, but may not
        return the number of bytes requested.
      compute_crc32: If True, compute the CRC32 of the compressed data. If
        False, the returned CRC32 will be None.
      include_comp: If True, include compressed data in the result.
      zlib_bufsize: An optional buffer size for zlib operations.
    Returns: A tuple of (unpacked, unused), where unused is the unused data
        leftover from decompression, and unpacked in an UnpackedObject with
        the following attrs set:

        * obj_chunks     (for non-delta types)
        * pack_type_num
        * delta_base     (for delta types)
        * comp_chunks    (if include_comp is True)
        * decomp_chunks
        * decomp_len
        * crc32          (if compute_crc32 is True)
    """
    pass

def _compute_object_size(value):
    """Compute the size of a unresolved object for use with LRUSizeCache."""
    pass

class PackStreamReader:
    """Class to read a pack stream.

    The pack is read from a ReceivableProtocol using read() or recv() as
    appropriate.
    """

    def __init__(self, read_all, read_some=None, zlib_bufsize=_ZLIB_BUFSIZE) -> None:
        self.read_all = read_all
        if read_some is None:
            self.read_some = read_all
        else:
            self.read_some = read_some
        self.sha = sha1()
        self._offset = 0
        self._rbuf = BytesIO()
        self._trailer: Deque[bytes] = deque()
        self._zlib_bufsize = zlib_bufsize

    def _read(self, read, size):
        """Read up to size bytes using the given callback.

        As a side effect, update the verifier's hash (excluding the last 20
        bytes read).

        Args:
          read: The read callback to read from.
          size: The maximum number of bytes to read; the particular
            behavior is callback-specific.
        """
        pass

    def read(self, size):
        """Read, blocking until size bytes are read."""
        pass

    def recv(self, size):
        """Read up to size bytes, blocking until one byte is read."""
        pass

    def __len__(self) -> int:
        return self._num_objects

    def read_objects(self, compute_crc32=False) -> Iterator[UnpackedObject]:
        """Read the objects in this pack file.

        Args:
          compute_crc32: If True, compute the CRC32 of the compressed
            data. If False, the returned CRC32 will be None.
        Returns: Iterator over UnpackedObjects with the following members set:
            offset
            obj_type_num
            obj_chunks (for non-delta types)
            delta_base (for delta types)
            decomp_chunks
            decomp_len
            crc32 (if compute_crc32 is True)

        Raises:
          ChecksumMismatch: if the checksum of the pack contents does not
            match the checksum in the pack trailer.
          zlib.error: if an error occurred during zlib decompression.
          IOError: if an error occurred writing to the output file.
        """
        pass

class PackStreamCopier(PackStreamReader):
    """Class to verify a pack stream as it is being read.

    The pack is read from a ReceivableProtocol using read() or recv() as
    appropriate and written out to the given file-like object.
    """

    def __init__(self, read_all, read_some, outfile, delta_iter=None) -> None:
        """Initialize the copier.

        Args:
          read_all: Read function that blocks until the number of
            requested bytes are read.
          read_some: Read function that returns at least one byte, but may
            not return the number of bytes requested.
          outfile: File-like object to write output through.
          delta_iter: Optional DeltaChainIterator to record deltas as we
            read them.
        """
        super().__init__(read_all, read_some=read_some)
        self.outfile = outfile
        self._delta_iter = delta_iter

    def _read(self, read, size):
        """Read data from the read callback and write it to the file."""
        pass

    def verify(self, progress=None):
        """Verify a pack stream and write it to the output file.

        See PackStreamReader.iterobjects for a list of exceptions this may
        throw.
        """
        pass

def obj_sha(type, chunks):
    """Compute the SHA for a numeric type and object chunks."""
    pass

def compute_file_sha(f, start_ofs=0, end_ofs=0, buffer_size=1 << 16):
    """Hash a portion of a file into a new SHA.

    Args:
      f: A file-like object to read from that supports seek().
      start_ofs: The offset in the file to start reading at.
      end_ofs: The offset in the file to end reading at, relative to the
        end of the file.
      buffer_size: A buffer size for reading.
    Returns: A new SHA object updated with data read from the file.
    """
    pass

class PackData:
    """The data contained in a packfile.

    Pack files can be accessed both sequentially for exploding a pack, and
    directly with the help of an index to retrieve a specific object.

    The objects within are either complete or a delta against another.

    The header is variable length. If the MSB of each byte is set then it
    indicates that the subsequent byte is still part of the header.
    For the first byte the next MS bits are the type, which tells you the type
    of object, and whether it is a delta. The LS byte is the lowest bits of the
    size. For each subsequent byte the LS 7 bits are the next MS bits of the
    size, i.e. the last byte of the header contains the MS bits of the size.

    For the complete objects the data is stored as zlib deflated data.
    The size in the header is the uncompressed object size, so to uncompress
    you need to just keep feeding data to zlib until you get an object back,
    or it errors on bad data. This is done here by just giving the complete
    buffer from the start of the deflated object on. This is bad, but until I
    get mmap sorted out it will have to do.

    Currently there are no integrity checks done. Also no attempt is made to
    try and detect the delta case, or a request for an object at the wrong
    position.  It will all just throw a zlib or KeyError.
    """

    def __init__(self, filename, file=None, size=None) -> None:
        """Create a PackData object representing the pack in the given filename.

        The file must exist and stay readable until the object is disposed of.
        It must also stay the same size. It will be mapped whenever needed.

        Currently there is a restriction on the size of the pack as the python
        mmap implementation is flawed.
        """
        self._filename = filename
        self._size = size
        self._header_size = 12
        if file is None:
            self._file = GitFile(self._filename, 'rb')
        else:
            self._file = file
        version, self._num_objects = read_pack_header(self._file.read)
        self._offset_cache = LRUSizeCache[int, Tuple[int, OldUnpackedObject]](1024 * 1024 * 20, compute_size=_compute_object_size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __eq__(self, other):
        if isinstance(other, PackData):
            return self.get_stored_checksum() == other.get_stored_checksum()
        return False

    def __len__(self) -> int:
        """Returns the number of objects in this pack."""
        return self._num_objects

    def calculate_checksum(self):
        """Calculate the checksum for this pack.

        Returns: 20-byte binary SHA1 digest
        """
        pass

    def iterentries(self, progress=None, resolve_ext_ref: Optional[ResolveExtRefFn]=None):
        """Yield entries summarizing the contents of this pack.

        Args:
          progress: Progress function, called with current and total
            object count.
        Returns: iterator of tuples with (sha, offset, crc32)
        """
        pass

    def sorted_entries(self, progress: Optional[ProgressFn]=None, resolve_ext_ref: Optional[ResolveExtRefFn]=None):
        """Return entries in this pack, sorted by SHA.

        Args:
          progress: Progress function, called with current and total
            object count
        Returns: Iterator of tuples with (sha, offset, crc32)
        """
        pass

    def create_index_v1(self, filename, progress=None, resolve_ext_ref=None):
        """Create a version 1 file for this data file.

        Args:
          filename: Index filename.
          progress: Progress report function
        Returns: Checksum of index file
        """
        pass

    def create_index_v2(self, filename, progress=None, resolve_ext_ref=None):
        """Create a version 2 index file for this data file.

        Args:
          filename: Index filename.
          progress: Progress report function
        Returns: Checksum of index file
        """
        pass

    def create_index(self, filename, progress=None, version=2, resolve_ext_ref=None):
        """Create an  index file for this data file.

        Args:
          filename: Index filename.
          progress: Progress report function
        Returns: Checksum of index file
        """
        pass

    def get_stored_checksum(self):
        """Return the expected checksum stored in this pack."""
        pass

    def check(self):
        """Check the consistency of this pack."""
        pass

    def get_unpacked_object_at(self, offset: int, *, include_comp: bool=False) -> UnpackedObject:
        """Given offset in the packfile return a UnpackedObject."""
        pass

    def get_object_at(self, offset: int) -> Tuple[int, OldUnpackedObject]:
        """Given an offset in to the packfile return the object that is there.

        Using the associated index the location of an object can be looked up,
        and then the packfile can be asked directly for that object using this
        function.
        """
        pass
T = TypeVar('T')

class DeltaChainIterator(Generic[T]):
    """Abstract iterator over pack data based on delta chains.

    Each object in the pack is guaranteed to be inflated exactly once,
    regardless of how many objects reference it as a delta base. As a result,
    memory usage is proportional to the length of the longest delta chain.

    Subclasses can override _result to define the result type of the iterator.
    By default, results are UnpackedObjects with the following members set:

    * offset
    * obj_type_num
    * obj_chunks
    * pack_type_num
    * delta_base     (for delta types)
    * comp_chunks    (if _include_comp is True)
    * decomp_chunks
    * decomp_len
    * crc32          (if _compute_crc32 is True)
    """
    _compute_crc32 = False
    _include_comp = False

    def __init__(self, file_obj, *, resolve_ext_ref=None) -> None:
        self._file = file_obj
        self._resolve_ext_ref = resolve_ext_ref
        self._pending_ofs: Dict[int, List[int]] = defaultdict(list)
        self._pending_ref: Dict[bytes, List[int]] = defaultdict(list)
        self._full_ofs: List[Tuple[int, int]] = []
        self._ext_refs: List[bytes] = []

    def __iter__(self) -> Iterator[T]:
        return self._walk_all_chains()

class UnpackedObjectIterator(DeltaChainIterator[UnpackedObject]):
    """Delta chain iterator that yield unpacked objects."""

class PackIndexer(DeltaChainIterator[PackIndexEntry]):
    """Delta chain iterator that yields index entries."""
    _compute_crc32 = True

class PackInflater(DeltaChainIterator[ShaFile]):
    """Delta chain iterator that yields ShaFile objects."""

class SHA1Reader:
    """Wrapper for file-like object that remembers the SHA1 of its data."""

    def __init__(self, f) -> None:
        self.f = f
        self.sha1 = sha1(b'')

class SHA1Writer:
    """Wrapper for file-like object that remembers the SHA1 of its data."""

    def __init__(self, f) -> None:
        self.f = f
        self.length = 0
        self.sha1 = sha1(b'')

def pack_object_header(type_num, delta_base, size):
    """Create a pack object header for the given object info.

    Args:
      type_num: Numeric type of the object.
      delta_base: Delta base offset or ref, or None for whole objects.
      size: Uncompressed object size.
    Returns: A header for a packed object.
    """
    pass

def pack_object_chunks(type, object, compression_level=-1):
    """Generate chunks for a pack object.

    Args:
      type: Numeric type of the object
      object: Object to write
      compression_level: the zlib compression level
    Returns: Chunks
    """
    pass

def write_pack_object(write, type, object, sha=None, compression_level=-1):
    """Write pack object to a file.

    Args:
      write: Write function to use
      type: Numeric type of the object
      object: Object to write
      compression_level: the zlib compression level
    Returns: Tuple with offset at which the object was written, and crc32
    """
    pass

def write_pack(filename, objects: Union[Sequence[ShaFile], Sequence[Tuple[ShaFile, Optional[bytes]]]], *, deltify: Optional[bool]=None, delta_window_size: Optional[int]=None, compression_level: int=-1):
    """Write a new pack data file.

    Args:
      filename: Path to the new pack file (without .pack extension)
      container: PackedObjectContainer
      entries: Sequence of (object_id, path) tuples to write
      delta_window_size: Delta window size
      deltify: Whether to deltify pack objects
      compression_level: the zlib compression level
    Returns: Tuple with checksum of pack file and index file
    """
    pass

def pack_header_chunks(num_objects):
    """Yield chunks for a pack header."""
    pass

def write_pack_header(write, num_objects):
    """Write a pack header for the given number of objects."""
    pass

def deltify_pack_objects(objects: Union[Iterator[bytes], Iterator[Tuple[ShaFile, Optional[bytes]]]], *, window_size: Optional[int]=None, progress=None) -> Iterator[UnpackedObject]:
    """Generate deltas for pack objects.

    Args:
      objects: An iterable of (object, path) tuples to deltify.
      window_size: Window size; None for default
    Returns: Iterator over type_num, object id, delta_base, content
        delta_base is None for full text entries
    """
    pass

def pack_objects_to_data(objects: Union[Sequence[ShaFile], Sequence[Tuple[ShaFile, Optional[bytes]]]], *, deltify: Optional[bool]=None, delta_window_size: Optional[int]=None, ofs_delta: bool=True, progress=None) -> Tuple[int, Iterator[UnpackedObject]]:
    """Create pack data from objects.

    Args:
      objects: Pack objects
    Returns: Tuples with (type_num, hexdigest, delta base, object chunks)
    """
    pass

def generate_unpacked_objects(container: PackedObjectContainer, object_ids: Sequence[Tuple[ObjectID, Optional[PackHint]]], delta_window_size: Optional[int]=None, deltify: Optional[bool]=None, reuse_deltas: bool=True, ofs_delta: bool=True, other_haves: Optional[Set[bytes]]=None, progress=None) -> Iterator[UnpackedObject]:
    """Create pack data from objects.

    Args:
      objects: Pack objects
    Returns: Tuples with (type_num, hexdigest, delta base, object chunks)
    """
    pass

def write_pack_from_container(write, container: PackedObjectContainer, object_ids: Sequence[Tuple[ObjectID, Optional[PackHint]]], delta_window_size: Optional[int]=None, deltify: Optional[bool]=None, reuse_deltas: bool=True, compression_level: int=-1, other_haves: Optional[Set[bytes]]=None):
    """Write a new pack data file.

    Args:
      write: write function to use
      container: PackedObjectContainer
      entries: Sequence of (object_id, path) tuples to write
      delta_window_size: Sliding window size for searching for deltas;
                         Set to None for default window size.
      deltify: Whether to deltify objects
      compression_level: the zlib compression level to use
    Returns: Dict mapping id -> (offset, crc32 checksum), pack checksum
    """
    pass

def write_pack_objects(write, objects: Union[Sequence[ShaFile], Sequence[Tuple[ShaFile, Optional[bytes]]]], *, delta_window_size: Optional[int]=None, deltify: Optional[bool]=None, compression_level: int=-1):
    """Write a new pack data file.

    Args:
      write: write function to use
      objects: Sequence of (object, path) tuples to write
      delta_window_size: Sliding window size for searching for deltas;
                         Set to None for default window size.
      deltify: Whether to deltify objects
      compression_level: the zlib compression level to use
    Returns: Dict mapping id -> (offset, crc32 checksum), pack checksum
    """
    pass

class PackChunkGenerator:

    def __init__(self, num_records=None, records=None, progress=None, compression_level=-1, reuse_compressed=True) -> None:
        self.cs = sha1(b'')
        self.entries: Dict[Union[int, bytes], Tuple[int, int]] = {}
        self._it = self._pack_data_chunks(num_records=num_records, records=records, progress=progress, compression_level=compression_level, reuse_compressed=reuse_compressed)

    def __iter__(self):
        return self._it

    def _pack_data_chunks(self, records: Iterator[UnpackedObject], *, num_records=None, progress=None, compression_level: int=-1, reuse_compressed: bool=True) -> Iterator[bytes]:
        """Iterate pack data file chunks.

        Args:
          records: Iterator over UnpackedObject
          num_records: Number of records (defaults to len(records) if not specified)
          progress: Function to report progress to
          compression_level: the zlib compression level
        Returns: Dict mapping id -> (offset, crc32 checksum), pack checksum
        """
        pass

def write_pack_data(write, records: Iterator[UnpackedObject], *, num_records=None, progress=None, compression_level=-1):
    """Write a new pack data file.

    Args:
      write: Write function to use
      num_records: Number of records (defaults to len(records) if None)
      records: Iterator over type_num, object_id, delta_base, raw
      progress: Function to report progress to
      compression_level: the zlib compression level
    Returns: Dict mapping id -> (offset, crc32 checksum), pack checksum
    """
    pass

def write_pack_index_v1(f, entries, pack_checksum):
    """Write a new pack index file.

    Args:
      f: A file-like object to write to
      entries: List of tuples with object name (sha), offset_in_pack,
        and crc32_checksum.
      pack_checksum: Checksum of the pack file.
    Returns: The SHA of the written index file
    """
    pass
_MAX_COPY_LEN = 65535

def create_delta(base_buf, target_buf):
    """Use python difflib to work out how to transform base_buf to target_buf.

    Args:
      base_buf: Base buffer
      target_buf: Target buffer
    """
    pass

def apply_delta(src_buf, delta):
    """Based on the similar function in git's patch-delta.c.

    Args:
      src_buf: Source buffer
      delta: Delta instructions
    """
    pass

def write_pack_index_v2(f, entries: Iterable[PackIndexEntry], pack_checksum: bytes) -> bytes:
    """Write a new pack index file.

    Args:
      f: File-like object to write to
      entries: List of tuples with object name (sha), offset_in_pack, and
        crc32_checksum.
      pack_checksum: Checksum of the pack file.
    Returns: The SHA of the index file written
    """
    pass
write_pack_index = write_pack_index_v2

class Pack:
    """A Git pack object."""
    _data_load: Optional[Callable[[], PackData]]
    _idx_load: Optional[Callable[[], PackIndex]]
    _data: Optional[PackData]
    _idx: Optional[PackIndex]

    def __init__(self, basename, resolve_ext_ref: Optional[ResolveExtRefFn]=None) -> None:
        self._basename = basename
        self._data = None
        self._idx = None
        self._idx_path = self._basename + '.idx'
        self._data_path = self._basename + '.pack'
        self._data_load = lambda: PackData(self._data_path)
        self._idx_load = lambda: load_pack_index(self._idx_path)
        self.resolve_ext_ref = resolve_ext_ref

    @classmethod
    def from_lazy_objects(cls, data_fn, idx_fn):
        """Create a new pack object from callables to load pack data and
        index objects.
        """
        pass

    @classmethod
    def from_objects(cls, data, idx):
        """Create a new pack object from pack data and index objects."""
        pass

    def name(self):
        """The SHA over the SHAs of the objects in this pack."""
        pass

    @property
    def data(self) -> PackData:
        """The pack data object being used."""
        pass

    @property
    def index(self) -> PackIndex:
        """The index being used.

        Note: This may be an in-memory index
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.index == other.index

    def __len__(self) -> int:
        """Number of entries in this pack."""
        return len(self.index)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._basename!r})'

    def __iter__(self):
        """Iterate over all the sha1s of the objects in this pack."""
        return iter(self.index)

    def check_length_and_checksum(self) -> None:
        """Sanity check the length and checksum of the pack index and data."""
        pass

    def check(self) -> None:
        """Check the integrity of this pack.

        Raises:
          ChecksumMismatch: if a checksum for the index or data is wrong
        """
        pass

    def __contains__(self, sha1: bytes) -> bool:
        """Check whether this pack contains a particular SHA1."""
        try:
            self.index.object_offset(sha1)
            return True
        except KeyError:
            return False

    def __getitem__(self, sha1: bytes) -> ShaFile:
        """Retrieve the specified SHA1."""
        type, uncomp = self.get_raw(sha1)
        return ShaFile.from_raw_string(type, uncomp, sha=sha1)

    def iterobjects(self) -> Iterator[ShaFile]:
        """Iterate over the objects in this pack."""
        pass

    def keep(self, msg: Optional[bytes]=None) -> str:
        """Add a .keep file for the pack, preventing git from garbage collecting it.

        Args:
          msg: A message written inside the .keep file; can be used later
            to determine whether or not a .keep file is obsolete.
        Returns: The path of the .keep file, as a string.
        """
        pass

    def get_ref(self, sha: bytes) -> Tuple[Optional[int], int, OldUnpackedObject]:
        """Get the object for a ref SHA, only looking in this pack."""
        pass

    def resolve_object(self, offset: int, type: int, obj, get_ref=None) -> Tuple[int, Iterable[bytes]]:
        """Resolve an object, possibly resolving deltas when necessary.

        Returns: Tuple with object type and contents.
        """
        pass

    def entries(self, progress: Optional[ProgressFn]=None) -> Iterator[PackIndexEntry]:
        """Yield entries summarizing the contents of this pack.

        Args:
          progress: Progress function, called with current and total
            object count.
        Returns: iterator of tuples with (sha, offset, crc32)
        """
        pass

    def sorted_entries(self, progress: Optional[ProgressFn]=None) -> Iterator[PackIndexEntry]:
        """Return entries in this pack, sorted by SHA.

        Args:
          progress: Progress function, called with current and total
            object count
        Returns: Iterator of tuples with (sha, offset, crc32)
        """
        pass

    def get_unpacked_object(self, sha: bytes, *, include_comp: bool=False, convert_ofs_delta: bool=True) -> UnpackedObject:
        """Get the unpacked object for a sha.

        Args:
          sha: SHA of object to fetch
          include_comp: Whether to include compression data in UnpackedObject
        """
        pass

def extend_pack(f: BinaryIO, object_ids: Set[ObjectID], get_raw, *, compression_level=-1, progress=None) -> Tuple[bytes, List]:
    """Extend a pack file with more objects.

    The caller should make sure that object_ids does not contain any objects
    that are already in the pack
    """
    pass
try:
    from dulwich._pack import apply_delta, bisect_find_sha
except ImportError:
    pass