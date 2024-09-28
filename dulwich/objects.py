"""Access to base git objects."""
import binascii
import os
import posixpath
import stat
import warnings
import zlib
from collections import namedtuple
from hashlib import sha1
from io import BytesIO
from typing import TYPE_CHECKING, BinaryIO, Dict, Iterable, Iterator, List, Optional, Tuple, Type, Union
from .errors import ChecksumMismatch, FileFormatException, NotBlobError, NotCommitError, NotTagError, NotTreeError, ObjectFormatException
from .file import GitFile
if TYPE_CHECKING:
    from _hashlib import HASH
ZERO_SHA = b'0' * 40
_TREE_HEADER = b'tree'
_PARENT_HEADER = b'parent'
_AUTHOR_HEADER = b'author'
_COMMITTER_HEADER = b'committer'
_ENCODING_HEADER = b'encoding'
_MERGETAG_HEADER = b'mergetag'
_GPGSIG_HEADER = b'gpgsig'
_OBJECT_HEADER = b'object'
_TYPE_HEADER = b'type'
_TAG_HEADER = b'tag'
_TAGGER_HEADER = b'tagger'
S_IFGITLINK = 57344
MAX_TIME = 9223372036854775807
BEGIN_PGP_SIGNATURE = b'-----BEGIN PGP SIGNATURE-----'
ObjectID = bytes

class EmptyFileException(FileFormatException):
    """An unexpectedly empty file was encountered."""

def S_ISGITLINK(m):
    """Check if a mode indicates a submodule.

    Args:
      m: Mode to check
    Returns: a ``boolean``
    """
    pass

def sha_to_hex(sha):
    """Takes a string and returns the hex of the sha within."""
    pass

def hex_to_sha(hex):
    """Takes a hex sha and returns a binary sha."""
    pass

def hex_to_filename(path, hex):
    """Takes a hex sha and returns its filename relative to the given path."""
    pass

def filename_to_hex(filename):
    """Takes an object filename and returns its corresponding hex sha."""
    pass

def object_header(num_type: int, length: int) -> bytes:
    """Return an object header for the given numeric type and text length."""
    pass

def serializable_property(name: str, docstring: Optional[str]=None):
    """A property that helps tracking whether serialization is necessary."""
    pass

def object_class(type: Union[bytes, int]) -> Optional[Type['ShaFile']]:
    """Get the object class corresponding to the given type.

    Args:
      type: Either a type name string or a numeric type.
    Returns: The ShaFile subclass corresponding to the given type, or None if
        type is not a valid type name/number.
    """
    pass

def check_hexsha(hex, error_msg):
    """Check if a string is a valid hex sha string.

    Args:
      hex: Hex string to check
      error_msg: Error message to use in exception
    Raises:
      ObjectFormatException: Raised when the string is not valid
    """
    pass

def check_identity(identity: bytes, error_msg: str) -> None:
    """Check if the specified identity is valid.

    This will raise an exception if the identity is not valid.

    Args:
      identity: Identity string
      error_msg: Error message to use in exception
    """
    pass

def check_time(time_seconds):
    """Check if the specified time is not prone to overflow error.

    This will raise an exception if the time is not valid.

    Args:
      time_seconds: time in seconds

    """
    pass

def git_line(*items):
    """Formats items into a space separated line."""
    pass

class FixedSha:
    """SHA object that behaves like hashlib's but is given a fixed value."""
    __slots__ = ('_hexsha', '_sha')

    def __init__(self, hexsha) -> None:
        if getattr(hexsha, 'encode', None) is not None:
            hexsha = hexsha.encode('ascii')
        if not isinstance(hexsha, bytes):
            raise TypeError(f'Expected bytes for hexsha, got {hexsha!r}')
        self._hexsha = hexsha
        self._sha = hex_to_sha(hexsha)

    def digest(self) -> bytes:
        """Return the raw SHA digest."""
        pass

    def hexdigest(self) -> str:
        """Return the hex SHA digest."""
        pass

class ShaFile:
    """A git SHA file."""
    __slots__ = ('_chunked_text', '_sha', '_needs_serialization')
    _needs_serialization: bool
    type_name: bytes
    type_num: int
    _chunked_text: Optional[List[bytes]]
    _sha: Union[FixedSha, None, 'HASH']

    @staticmethod
    def _parse_legacy_object_header(magic, f: BinaryIO) -> 'ShaFile':
        """Parse a legacy object, creating it but not reading the file."""
        pass

    def _parse_legacy_object(self, map) -> None:
        """Parse a legacy object, setting the raw string."""
        pass

    def as_legacy_object_chunks(self, compression_level: int=-1) -> Iterator[bytes]:
        """Return chunks representing the object in the experimental format.

        Returns: List of strings
        """
        pass

    def as_legacy_object(self, compression_level: int=-1) -> bytes:
        """Return string representing the object in the experimental format."""
        pass

    def as_raw_chunks(self) -> List[bytes]:
        """Return chunks with serialization of the object.

        Returns: List of strings, not necessarily one per line
        """
        pass

    def as_raw_string(self) -> bytes:
        """Return raw string with serialization of the object.

        Returns: String object
        """
        pass

    def __bytes__(self) -> bytes:
        """Return raw string serialization of this object."""
        return self.as_raw_string()

    def __hash__(self):
        """Return unique hash for this object."""
        return hash(self.id)

    def as_pretty_string(self) -> str:
        """Return a string representing this object, fit for display."""
        pass

    def set_raw_string(self, text: bytes, sha: Optional[ObjectID]=None) -> None:
        """Set the contents of this object from a serialized string."""
        pass

    def set_raw_chunks(self, chunks: List[bytes], sha: Optional[ObjectID]=None) -> None:
        """Set the contents of this object from a list of chunks."""
        pass

    @staticmethod
    def _parse_object_header(magic, f):
        """Parse a new style object, creating it but not reading the file."""
        pass

    def _parse_object(self, map) -> None:
        """Parse a new style object, setting self._text."""
        pass

    def __init__(self) -> None:
        """Don't call this directly."""
        self._sha = None
        self._chunked_text = []
        self._needs_serialization = True

    @classmethod
    def from_path(cls, path):
        """Open a SHA file from disk."""
        pass

    @classmethod
    def from_file(cls, f):
        """Get the contents of a SHA file on disk."""
        pass

    @staticmethod
    def from_raw_string(type_num, string, sha=None):
        """Creates an object of the indicated type from the raw string given.

        Args:
          type_num: The numeric type of the object.
          string: The raw uncompressed contents.
          sha: Optional known sha for the object
        """
        pass

    @staticmethod
    def from_raw_chunks(type_num: int, chunks: List[bytes], sha: Optional[ObjectID]=None):
        """Creates an object of the indicated type from the raw chunks given.

        Args:
          type_num: The numeric type of the object.
          chunks: An iterable of the raw uncompressed contents.
          sha: Optional known sha for the object
        """
        pass

    @classmethod
    def from_string(cls, string):
        """Create a ShaFile from a string."""
        pass

    def _check_has_member(self, member, error_msg):
        """Check that the object has a given member variable.

        Args:
          member: the member variable to check for
          error_msg: the message for an error if the member is missing
        Raises:
          ObjectFormatException: with the given error_msg if member is
            missing or is None
        """
        pass

    def check(self) -> None:
        """Check this object for internal consistency.

        Raises:
          ObjectFormatException: if the object is malformed in some way
          ChecksumMismatch: if the object was created with a SHA that does
            not match its contents
        """
        pass

    def raw_length(self) -> int:
        """Returns the length of the raw string of this object."""
        pass

    def sha(self):
        """The SHA1 object that is the name of this object."""
        pass

    def copy(self):
        """Create a new copy of this SHA1 object from its raw string."""
        pass

    @property
    def id(self):
        """The hex SHA of this object."""
        pass

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.id}>'

    def __ne__(self, other):
        """Check whether this object does not match the other."""
        return not isinstance(other, ShaFile) or self.id != other.id

    def __eq__(self, other):
        """Return True if the SHAs of the two objects match."""
        return isinstance(other, ShaFile) and self.id == other.id

    def __lt__(self, other):
        """Return whether SHA of this object is less than the other."""
        if not isinstance(other, ShaFile):
            raise TypeError
        return self.id < other.id

    def __le__(self, other):
        """Check whether SHA of this object is less than or equal to the other."""
        if not isinstance(other, ShaFile):
            raise TypeError
        return self.id <= other.id

class Blob(ShaFile):
    """A Git Blob object."""
    __slots__ = ()
    type_name = b'blob'
    type_num = 3
    _chunked_text: List[bytes]

    def __init__(self) -> None:
        super().__init__()
        self._chunked_text = []
        self._needs_serialization = False
    data = property(_get_data, _set_data, doc='The text contained within the blob object.')
    chunked = property(_get_chunked, _set_chunked, doc='The text in the blob object, as chunks (not necessarily lines)')

    def check(self):
        """Check this object for internal consistency.

        Raises:
          ObjectFormatException: if the object is malformed in some way
        """
        pass

    def splitlines(self) -> List[bytes]:
        """Return list of lines in this blob.

        This preserves the original line endings.
        """
        pass

def _parse_message(chunks: Iterable[bytes]) -> Iterator[Union[Tuple[None, None], Tuple[Optional[bytes], bytes]]]:
    """Parse a message with a list of fields and a body.

    Args:
      chunks: the raw chunks of the tag or commit object.
    Returns: iterator of tuples of (field, value), one per header line, in the
        order read from the text, possibly including duplicates. Includes a
        field named None for the freeform tag/commit text.
    """
    pass

class Tag(ShaFile):
    """A Git Tag object."""
    type_name = b'tag'
    type_num = 4
    __slots__ = ('_tag_timezone_neg_utc', '_name', '_object_sha', '_object_class', '_tag_time', '_tag_timezone', '_tagger', '_message', '_signature')
    _tagger: Optional[bytes]

    def __init__(self) -> None:
        super().__init__()
        self._tagger = None
        self._tag_time = None
        self._tag_timezone = None
        self._tag_timezone_neg_utc = False
        self._signature = None

    def check(self):
        """Check this object for internal consistency.

        Raises:
          ObjectFormatException: if the object is malformed in some way
        """
        pass

    def _deserialize(self, chunks):
        """Grab the metadata attached to the tag."""
        pass

    def _get_object(self):
        """Get the object pointed to by this tag.

        Returns: tuple of (object class, sha).
        """
        pass
    object = property(_get_object, _set_object)
    name = serializable_property('name', 'The name of this tag')
    tagger = serializable_property('tagger', 'Returns the name of the person who created this tag')
    tag_time = serializable_property('tag_time', 'The creation timestamp of the tag.  As the number of seconds since the epoch')
    tag_timezone = serializable_property('tag_timezone', 'The timezone that tag_time is in.')
    message = serializable_property('message', 'the message attached to this tag')
    signature = serializable_property('signature', 'Optional detached GPG signature')

    def verify(self, keyids: Optional[Iterable[str]]=None) -> None:
        """Verify GPG signature for this tag (if it is signed).

        Args:
          keyids: Optional iterable of trusted keyids for this tag.
            If this tag is not signed by any key in keyids verification will
            fail. If not specified, this function only verifies that the tag
            has a valid signature.

        Raises:
          gpg.errors.BadSignatures: if GPG signature verification fails
          gpg.errors.MissingSignatures: if tag was not signed by a key
            specified in keyids
        """
        pass

class TreeEntry(namedtuple('TreeEntry', ['path', 'mode', 'sha'])):
    """Named tuple encapsulating a single tree entry."""

    def in_path(self, path: bytes):
        """Return a copy of this entry with the given path prepended."""
        pass

def parse_tree(text, strict=False):
    """Parse a tree text.

    Args:
      text: Serialized text to parse
    Returns: iterator of tuples of (name, mode, sha)

    Raises:
      ObjectFormatException: if the object was malformed in some way
    """
    pass

def serialize_tree(items):
    """Serialize the items in a tree to a text.

    Args:
      items: Sorted iterable over (name, mode, sha) tuples
    Returns: Serialized tree text as chunks
    """
    pass

def sorted_tree_items(entries, name_order: bool):
    """Iterate over a tree entries dictionary.

    Args:
      name_order: If True, iterate entries in order of their name. If
        False, iterate entries in tree order, that is, treat subtree entries as
        having '/' appended.
      entries: Dictionary mapping names to (mode, sha) tuples
    Returns: Iterator over (name, mode, hexsha)
    """
    pass

def key_entry(entry) -> bytes:
    """Sort key for tree entry.

    Args:
      entry: (name, value) tuple
    """
    pass

def key_entry_name_order(entry):
    """Sort key for tree entry in name order."""
    pass

def pretty_format_tree_entry(name, mode, hexsha, encoding='utf-8') -> str:
    """Pretty format tree entry.

    Args:
      name: Name of the directory entry
      mode: Mode of entry
      hexsha: Hexsha of the referenced object
    Returns: string describing the tree entry
    """
    pass

class SubmoduleEncountered(Exception):
    """A submodule was encountered while resolving a path."""

    def __init__(self, path, sha) -> None:
        self.path = path
        self.sha = sha

class Tree(ShaFile):
    """A Git tree object."""
    type_name = b'tree'
    type_num = 2
    __slots__ = '_entries'

    def __init__(self) -> None:
        super().__init__()
        self._entries: Dict[bytes, Tuple[int, bytes]] = {}

    def __contains__(self, name) -> bool:
        return name in self._entries

    def __getitem__(self, name):
        return self._entries[name]

    def __setitem__(self, name, value) -> None:
        """Set a tree entry by name.

        Args:
          name: The name of the entry, as a string.
          value: A tuple of (mode, hexsha), where mode is the mode of the
            entry as an integral type and hexsha is the hex SHA of the entry as
            a string.
        """
        mode, hexsha = value
        self._entries[name] = (mode, hexsha)
        self._needs_serialization = True

    def __delitem__(self, name) -> None:
        del self._entries[name]
        self._needs_serialization = True

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def add(self, name, mode, hexsha):
        """Add an entry to the tree.

        Args:
          mode: The mode of the entry as an integral type. Not all
            possible modes are supported by git; see check() for details.
          name: The name of the entry, as a string.
          hexsha: The hex SHA of the entry as a string.
        """
        pass

    def iteritems(self, name_order=False):
        """Iterate over entries.

        Args:
          name_order: If True, iterate in name order instead of tree
            order.
        Returns: Iterator over (name, mode, sha) tuples
        """
        pass

    def items(self):
        """Return the sorted entries in this tree.

        Returns: List with (name, mode, sha) tuples
        """
        pass

    def _deserialize(self, chunks):
        """Grab the entries in the tree."""
        pass

    def check(self):
        """Check this object for internal consistency.

        Raises:
          ObjectFormatException: if the object is malformed in some way
        """
        pass

    def lookup_path(self, lookup_obj, path):
        """Look up an object in a Git tree.

        Args:
          lookup_obj: Callback for retrieving object by SHA1
          path: Path to lookup
        Returns: A tuple of (mode, SHA) of the resulting path.
        """
        pass

def parse_timezone(text):
    """Parse a timezone text fragment (e.g. '+0100').

    Args:
      text: Text to parse.
    Returns: Tuple with timezone as seconds difference to UTC
        and a boolean indicating whether this was a UTC timezone
        prefixed with a negative sign (-0000).
    """
    pass

def format_timezone(offset, unnecessary_negative_timezone=False):
    """Format a timezone for Git serialization.

    Args:
      offset: Timezone offset as seconds difference to UTC
      unnecessary_negative_timezone: Whether to use a minus sign for
        UTC or positive timezones (-0000 and --700 rather than +0000 / +0700).
    """
    pass

def parse_time_entry(value):
    """Parse event.

    Args:
      value: Bytes representing a git commit/tag line
    Raises:
      ObjectFormatException in case of parsing error (malformed
      field date)
    Returns: Tuple of (author, time, (timezone, timezone_neg_utc))
    """
    pass

def format_time_entry(person, time, timezone_info):
    """Format an event."""
    pass

def parse_commit(chunks):
    """Parse a commit object from chunks.

    Args:
      chunks: Chunks to parse
    Returns: Tuple of (tree, parents, author_info, commit_info,
        encoding, mergetag, gpgsig, message, extra)
    """
    pass

class Commit(ShaFile):
    """A git commit object."""
    type_name = b'commit'
    type_num = 1
    __slots__ = ('_parents', '_encoding', '_extra', '_author_timezone_neg_utc', '_commit_timezone_neg_utc', '_commit_time', '_author_time', '_author_timezone', '_commit_timezone', '_author', '_committer', '_tree', '_message', '_mergetag', '_gpgsig')

    def __init__(self) -> None:
        super().__init__()
        self._parents: List[bytes] = []
        self._encoding = None
        self._mergetag: List[Tag] = []
        self._gpgsig = None
        self._extra: List[Tuple[bytes, bytes]] = []
        self._author_timezone_neg_utc = False
        self._commit_timezone_neg_utc = False

    def check(self):
        """Check this object for internal consistency.

        Raises:
          ObjectFormatException: if the object is malformed in some way
        """
        pass

    def verify(self, keyids: Optional[Iterable[str]]=None):
        """Verify GPG signature for this commit (if it is signed).

        Args:
          keyids: Optional iterable of trusted keyids for this commit.
            If this commit is not signed by any key in keyids verification will
            fail. If not specified, this function only verifies that the commit
            has a valid signature.

        Raises:
          gpg.errors.BadSignatures: if GPG signature verification fails
          gpg.errors.MissingSignatures: if commit was not signed by a key
            specified in keyids
        """
        pass
    tree = serializable_property('tree', 'Tree that is the state of this commit')

    def _get_parents(self):
        """Return a list of parents of this commit."""
        pass

    def _set_parents(self, value):
        """Set a list of parents of this commit."""
        pass
    parents = property(_get_parents, _set_parents, doc='Parents of this commit, by their SHA1.')

    def _get_extra(self):
        """Return extra settings of this commit."""
        pass
    extra = property(_get_extra, doc='Extra header fields not understood (presumably added in a newer version of git). Kept verbatim so the object can be correctly reserialized. For private commit metadata, use pseudo-headers in Commit.message, rather than this field.')
    author = serializable_property('author', 'The name of the author of the commit')
    committer = serializable_property('committer', 'The name of the committer of the commit')
    message = serializable_property('message', 'The commit message')
    commit_time = serializable_property('commit_time', 'The timestamp of the commit. As the number of seconds since the epoch.')
    commit_timezone = serializable_property('commit_timezone', 'The zone the commit time is in')
    author_time = serializable_property('author_time', 'The timestamp the commit was written. As the number of seconds since the epoch.')
    author_timezone = serializable_property('author_timezone', 'Returns the zone the author time is in.')
    encoding = serializable_property('encoding', 'Encoding of the commit message.')
    mergetag = serializable_property('mergetag', 'Associated signed tag.')
    gpgsig = serializable_property('gpgsig', 'GPG Signature.')
OBJECT_CLASSES = (Commit, Tree, Blob, Tag)
_TYPE_MAP: Dict[Union[bytes, int], Type[ShaFile]] = {}
for cls in OBJECT_CLASSES:
    _TYPE_MAP[cls.type_name] = cls
    _TYPE_MAP[cls.type_num] = cls
_parse_tree_py = parse_tree
_sorted_tree_items_py = sorted_tree_items
try:
    from dulwich._objects import parse_tree, sorted_tree_items
except ImportError:
    pass