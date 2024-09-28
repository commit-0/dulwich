"""Git object store interfaces and implementation."""
import os
import stat
import sys
import warnings
from contextlib import suppress
from io import BytesIO
from typing import Callable, Dict, FrozenSet, Iterable, Iterator, List, Optional, Protocol, Sequence, Set, Tuple, cast
from .errors import NotTreeError
from .file import GitFile
from .objects import S_ISGITLINK, ZERO_SHA, Blob, Commit, ObjectID, ShaFile, Tag, Tree, TreeEntry, hex_to_filename, hex_to_sha, object_class, sha_to_hex, valid_hexsha
from .pack import PACK_SPOOL_FILE_MAX_SIZE, ObjectContainer, Pack, PackData, PackedObjectContainer, PackFileDisappeared, PackHint, PackIndexer, PackInflater, PackStreamCopier, UnpackedObject, extend_pack, full_unpacked_object, generate_unpacked_objects, iter_sha1, load_pack_index_file, pack_objects_to_data, write_pack_data, write_pack_index
from .protocol import DEPTH_INFINITE
from .refs import PEELED_TAG_SUFFIX, Ref
INFODIR = 'info'
PACKDIR = 'pack'
PACK_MODE = 292 if sys.platform != 'win32' else 420

class PackContainer(Protocol):

    def add_pack(self) -> Tuple[BytesIO, Callable[[], None], Callable[[], None]]:
        """Add a new pack."""
        pass

class BaseObjectStore:
    """Object store interface."""

    def contains_loose(self, sha):
        """Check if a particular object is present by SHA1 and is loose."""
        pass

    def __contains__(self, sha1: bytes) -> bool:
        """Check if a particular object is present by SHA1.

        This method makes no distinction between loose and packed objects.
        """
        return self.contains_loose(sha1)

    @property
    def packs(self):
        """Iterable of pack objects."""
        pass

    def get_raw(self, name):
        """Obtain the raw text for an object.

        Args:
          name: sha for the object.
        Returns: tuple with numeric type and object contents.
        """
        pass

    def __getitem__(self, sha1: ObjectID) -> ShaFile:
        """Obtain an object by SHA1."""
        type_num, uncomp = self.get_raw(sha1)
        return ShaFile.from_raw_string(type_num, uncomp, sha=sha1)

    def __iter__(self):
        """Iterate over the SHAs that are present in this store."""
        raise NotImplementedError(self.__iter__)

    def add_object(self, obj):
        """Add a single object to this object store."""
        pass

    def add_objects(self, objects, progress=None):
        """Add a set of objects to this object store.

        Args:
          objects: Iterable over a list of (object, path) tuples
        """
        pass

    def tree_changes(self, source, target, want_unchanged=False, include_trees=False, change_type_same=False, rename_detector=None):
        """Find the differences between the contents of two trees.

        Args:
          source: SHA1 of the source tree
          target: SHA1 of the target tree
          want_unchanged: Whether unchanged files should be reported
          include_trees: Whether to include trees
          change_type_same: Whether to report files changing
            type in the same entry.
        Returns: Iterator over tuples with
            (oldpath, newpath), (oldmode, newmode), (oldsha, newsha)
        """
        pass

    def iter_tree_contents(self, tree_id, include_trees=False):
        """Iterate the contents of a tree and all subtrees.

        Iteration is depth-first pre-order, as in e.g. os.walk.

        Args:
          tree_id: SHA1 of the tree.
          include_trees: If True, include tree objects in the iteration.
        Returns: Iterator over TreeEntry namedtuples for all the objects in a
            tree.
        """
        pass

    def find_missing_objects(self, haves, wants, shallow=None, progress=None, get_tagged=None, get_parents=lambda commit: commit.parents):
        """Find the missing objects required for a set of revisions.

        Args:
          haves: Iterable over SHAs already in common.
          wants: Iterable over SHAs of objects to fetch.
          shallow: Set of shallow commit SHA1s to skip
          progress: Simple progress function that will be called with
            updated progress strings.
          get_tagged: Function that returns a dict of pointed-to sha ->
            tag sha for including tags.
          get_parents: Optional function for getting the parents of a
            commit.
        Returns: Iterator over (sha, path) pairs.
        """
        pass

    def find_common_revisions(self, graphwalker):
        """Find which revisions this store has in common using graphwalker.

        Args:
          graphwalker: A graphwalker object.
        Returns: List of SHAs that are in common
        """
        pass

    def generate_pack_data(self, have, want, shallow=None, progress=None, ofs_delta=True) -> Tuple[int, Iterator[UnpackedObject]]:
        """Generate pack data objects for a set of wants/haves.

        Args:
          have: List of SHA1s of objects that should not be sent
          want: List of SHA1s of objects that should be sent
          shallow: Set of shallow commit SHA1s to skip
          ofs_delta: Whether OFS deltas can be included
          progress: Optional progress reporting method
        """
        pass

    def peel_sha(self, sha):
        """Peel all tags from a SHA.

        Args:
          sha: The object SHA to peel.
        Returns: The fully-peeled SHA1 of a tag object, after peeling all
            intermediate tags; if the original ref does not point to a tag,
            this will equal the original SHA1.
        """
        pass

    def _get_depth(self, head, get_parents=lambda commit: commit.parents, max_depth=None):
        """Return the current available depth for the given head.
        For commits with multiple parents, the largest possible depth will be
        returned.

        Args:
            head: commit to start from
            get_parents: optional function for getting the parents of a commit
            max_depth: maximum depth to search
        """
        pass

    def close(self):
        """Close any files opened by this object store."""
        pass

class PackBasedObjectStore(BaseObjectStore):

    def __init__(self, pack_compression_level=-1) -> None:
        self._pack_cache: Dict[str, Pack] = {}
        self.pack_compression_level = pack_compression_level

    def add_pack(self) -> Tuple[BytesIO, Callable[[], None], Callable[[], None]]:
        """Add a new pack to this object store."""
        pass

    def add_pack_data(self, count: int, unpacked_objects: Iterator[UnpackedObject], progress=None) -> None:
        """Add pack data to this object store.

        Args:
          count: Number of items to add
          pack_data: Iterator over pack data tuples
        """
        pass

    def contains_packed(self, sha):
        """Check if a particular object is present by SHA1 and is packed.

        This does not check alternates.
        """
        pass

    def __contains__(self, sha) -> bool:
        """Check if a particular object is present by SHA1.

        This method makes no distinction between loose and packed objects.
        """
        if self.contains_packed(sha) or self.contains_loose(sha):
            return True
        for alternate in self.alternates:
            if sha in alternate:
                return True
        return False

    def _add_cached_pack(self, base_name, pack):
        """Add a newly appeared pack to the cache by path."""
        pass

    def generate_pack_data(self, have, want, shallow=None, progress=None, ofs_delta=True) -> Tuple[int, Iterator[UnpackedObject]]:
        """Generate pack data objects for a set of wants/haves.

        Args:
          have: List of SHA1s of objects that should not be sent
          want: List of SHA1s of objects that should be sent
          shallow: Set of shallow commit SHA1s to skip
          ofs_delta: Whether OFS deltas can be included
          progress: Optional progress reporting method
        """
        pass

    @property
    def packs(self):
        """List with pack objects."""
        pass

    def _iter_alternate_objects(self):
        """Iterate over the SHAs of all the objects in alternate stores."""
        pass

    def _iter_loose_objects(self):
        """Iterate over the SHAs of all loose objects."""
        pass

    def pack_loose_objects(self):
        """Pack loose objects.

        Returns: Number of objects packed
        """
        pass

    def repack(self):
        """Repack the packs in this repository.

        Note that this implementation is fairly naive and currently keeps all
        objects in memory while it repacks.
        """
        pass

    def __iter__(self):
        """Iterate over the SHAs that are present in this store."""
        self._update_pack_cache()
        for pack in self._iter_cached_packs():
            try:
                yield from pack
            except PackFileDisappeared:
                pass
        yield from self._iter_loose_objects()
        yield from self._iter_alternate_objects()

    def contains_loose(self, sha):
        """Check if a particular object is present by SHA1 and is loose.

        This does not check alternates.
        """
        pass

    def get_raw(self, name):
        """Obtain the raw fulltext for an object.

        Args:
          name: sha for the object.
        Returns: tuple with numeric type and object contents.
        """
        pass

    def get_unpacked_object(self, sha1: bytes, *, include_comp: bool=False) -> UnpackedObject:
        """Obtain the unpacked object.

        Args:
          sha1: sha for the object.
        """
        pass

    def add_objects(self, objects: Sequence[Tuple[ShaFile, Optional[str]]], progress: Optional[Callable[[str], None]]=None) -> None:
        """Add a set of objects to this object store.

        Args:
          objects: Iterable over (object, path) tuples, should support
            __len__.
        Returns: Pack object of the objects written.
        """
        pass

class DiskObjectStore(PackBasedObjectStore):
    """Git-style object store that exists on disk."""

    def __init__(self, path, loose_compression_level=-1, pack_compression_level=-1) -> None:
        """Open an object store.

        Args:
          path: Path of the object store.
          loose_compression_level: zlib compression level for loose objects
          pack_compression_level: zlib compression level for pack objects
        """
        super().__init__(pack_compression_level=pack_compression_level)
        self.path = path
        self.pack_dir = os.path.join(self.path, PACKDIR)
        self._alternates = None
        self.loose_compression_level = loose_compression_level
        self.pack_compression_level = pack_compression_level

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}({self.path!r})>'

    def add_alternate_path(self, path):
        """Add an alternate path to this object store."""
        pass

    def _update_pack_cache(self):
        """Read and iterate over new pack files and cache them."""
        pass

    def _complete_pack(self, f, path, num_objects, indexer, progress=None):
        """Move a specific file containing a pack into the pack directory.

        Note: The file should be on the same file system as the
            packs directory.

        Args:
          f: Open file object for the pack.
          path: Path to the pack file.
          indexer: A PackIndexer for indexing the pack.
        """
        pass

    def add_thin_pack(self, read_all, read_some, progress=None):
        """Add a new thin pack to this object store.

        Thin packs are packs that contain deltas with parents that exist
        outside the pack. They should never be placed in the object store
        directly, and always indexed and completed as they are copied.

        Args:
          read_all: Read function that blocks until the number of
            requested bytes are read.
          read_some: Read function that returns at least one byte, but may
            not return the number of bytes requested.
        Returns: A Pack object pointing at the now-completed thin pack in the
            objects/pack directory.
        """
        pass

    def add_pack(self):
        """Add a new pack to this object store.

        Returns: Fileobject to write to, a commit function to
            call when the pack is finished and an abort
            function.
        """
        pass

    def add_object(self, obj):
        """Add a single object to this object store.

        Args:
          obj: Object to add
        """
        pass

class MemoryObjectStore(BaseObjectStore):
    """Object store that keeps all objects in memory."""

    def __init__(self) -> None:
        super().__init__()
        self._data: Dict[str, ShaFile] = {}
        self.pack_compression_level = -1

    def contains_loose(self, sha):
        """Check if a particular object is present by SHA1 and is loose."""
        pass

    def contains_packed(self, sha):
        """Check if a particular object is present by SHA1 and is packed."""
        pass

    def __iter__(self):
        """Iterate over the SHAs that are present in this store."""
        return iter(self._data.keys())

    @property
    def packs(self):
        """List with pack objects."""
        pass

    def get_raw(self, name: ObjectID):
        """Obtain the raw text for an object.

        Args:
          name: sha for the object.
        Returns: tuple with numeric type and object contents.
        """
        pass

    def __getitem__(self, name: ObjectID):
        return self._data[self._to_hexsha(name)].copy()

    def __delitem__(self, name: ObjectID) -> None:
        """Delete an object from this store, for testing only."""
        del self._data[self._to_hexsha(name)]

    def add_object(self, obj):
        """Add a single object to this object store."""
        pass

    def add_objects(self, objects, progress=None):
        """Add a set of objects to this object store.

        Args:
          objects: Iterable over a list of (object, path) tuples
        """
        pass

    def add_pack(self):
        """Add a new pack to this object store.

        Because this object store doesn't support packs, we extract and add the
        individual objects.

        Returns: Fileobject to write to and a commit function to
            call when the pack is finished.
        """
        pass

    def add_pack_data(self, count: int, unpacked_objects: Iterator[UnpackedObject], progress=None) -> None:
        """Add pack data to this object store.

        Args:
          count: Number of items to add
          pack_data: Iterator over pack data tuples
        """
        pass

    def add_thin_pack(self, read_all, read_some, progress=None):
        """Add a new thin pack to this object store.

        Thin packs are packs that contain deltas with parents that exist
        outside the pack. Because this object store doesn't support packs, we
        extract and add the individual objects.

        Args:
          read_all: Read function that blocks until the number of
            requested bytes are read.
          read_some: Read function that returns at least one byte, but may
            not return the number of bytes requested.
        """
        pass

class ObjectIterator(Protocol):
    """Interface for iterating over objects."""

def tree_lookup_path(lookup_obj, root_sha, path):
    """Look up an object in a Git tree.

    Args:
      lookup_obj: Callback for retrieving object by SHA1
      root_sha: SHA1 of the root tree
      path: Path to lookup
    Returns: A tuple of (mode, SHA) of the resulting path.
    """
    pass

def _collect_filetree_revs(obj_store: ObjectContainer, tree_sha: ObjectID, kset: Set[ObjectID]) -> None:
    """Collect SHA1s of files and directories for specified tree.

    Args:
      obj_store: Object store to get objects by SHA from
      tree_sha: tree reference to walk
      kset: set to fill with references to files and directories
    """
    pass

def _split_commits_and_tags(obj_store: ObjectContainer, lst, *, ignore_unknown=False) -> Tuple[Set[bytes], Set[bytes], Set[bytes]]:
    """Split object id list into three lists with commit, tag, and other SHAs.

    Commits referenced by tags are included into commits
    list as well. Only SHA1s known in this repository will get
    through, and unless ignore_unknown argument is True, KeyError
    is thrown for SHA1 missing in the repository

    Args:
      obj_store: Object store to get objects by SHA1 from
      lst: Collection of commit and tag SHAs
      ignore_unknown: True to skip SHA1 missing in the repository
        silently.
    Returns: A tuple of (commits, tags, others) SHA1s
    """
    pass

class MissingObjectFinder:
    """Find the objects missing from another object store.

    Args:
      object_store: Object store containing at least all objects to be
        sent
      haves: SHA1s of commits not to send (already present in target)
      wants: SHA1s of commits to send
      progress: Optional function to report progress to.
      get_tagged: Function that returns a dict of pointed-to sha -> tag
        sha for including tags.
      get_parents: Optional function for getting the parents of a commit.
      tagged: dict of pointed-to sha -> tag sha for including tags
    """

    def __init__(self, object_store, haves, wants, *, shallow=None, progress=None, get_tagged=None, get_parents=lambda commit: commit.parents) -> None:
        self.object_store = object_store
        if shallow is None:
            shallow = set()
        self._get_parents = get_parents
        have_commits, have_tags, have_others = _split_commits_and_tags(object_store, haves, ignore_unknown=True)
        want_commits, want_tags, want_others = _split_commits_and_tags(object_store, wants, ignore_unknown=False)
        all_ancestors = _collect_ancestors(object_store, have_commits, shallow=shallow, get_parents=self._get_parents)[0]
        missing_commits, common_commits = _collect_ancestors(object_store, want_commits, all_ancestors, shallow=shallow, get_parents=self._get_parents)
        self.remote_has: Set[bytes] = set()
        for h in common_commits:
            self.remote_has.add(h)
            cmt = object_store[h]
            _collect_filetree_revs(object_store, cmt.tree, self.remote_has)
        for t in have_tags:
            self.remote_has.add(t)
        self.sha_done = set(self.remote_has)
        self.objects_to_send: Set[Tuple[ObjectID, Optional[bytes], Optional[int], bool]] = {(w, None, Commit.type_num, False) for w in missing_commits}
        missing_tags = want_tags.difference(have_tags)
        self.objects_to_send.update({(w, None, Tag.type_num, False) for w in missing_tags})
        missing_others = want_others.difference(have_others)
        self.objects_to_send.update({(w, None, None, False) for w in missing_others})
        if progress is None:
            self.progress = lambda x: None
        else:
            self.progress = progress
        self._tagged = get_tagged and get_tagged() or {}

    def __next__(self) -> Tuple[bytes, Optional[PackHint]]:
        while True:
            if not self.objects_to_send:
                self.progress(('counting objects: %d, done.\n' % len(self.sha_done)).encode('ascii'))
                raise StopIteration
            sha, name, type_num, leaf = self.objects_to_send.pop()
            if sha not in self.sha_done:
                break
        if not leaf:
            o = self.object_store[sha]
            if isinstance(o, Commit):
                self.add_todo([(o.tree, b'', Tree.type_num, False)])
            elif isinstance(o, Tree):
                self.add_todo([(s, n, Blob.type_num if stat.S_ISREG(m) else Tree.type_num, not stat.S_ISDIR(m)) for n, m, s in o.iteritems() if not S_ISGITLINK(m)])
            elif isinstance(o, Tag):
                self.add_todo([(o.object[1], None, o.object[0].type_num, False)])
        if sha in self._tagged:
            self.add_todo([(self._tagged[sha], None, None, True)])
        self.sha_done.add(sha)
        if len(self.sha_done) % 1000 == 0:
            self.progress(('counting objects: %d\r' % len(self.sha_done)).encode('ascii'))
        if type_num is None:
            pack_hint = None
        else:
            pack_hint = (type_num, name)
        return (sha, pack_hint)

    def __iter__(self):
        return self

class ObjectStoreGraphWalker:
    """Graph walker that finds what commits are missing from an object store.

    Attributes:
      heads: Revisions without descendants in the local repo
      get_parents: Function to retrieve parents in the local repo
    """

    def __init__(self, local_heads, get_parents, shallow=None) -> None:
        """Create a new instance.

        Args:
          local_heads: Heads to start search with
          get_parents: Function for finding the parents of a SHA1.
        """
        self.heads = set(local_heads)
        self.get_parents = get_parents
        self.parents: Dict[ObjectID, Optional[List[ObjectID]]] = {}
        if shallow is None:
            shallow = set()
        self.shallow = shallow

    def nak(self):
        """Nothing in common was found."""
        pass

    def ack(self, sha):
        """Ack that a revision and its ancestors are present in the source."""
        pass

    def next(self):
        """Iterate over ancestors of heads in the target."""
        pass
    __next__ = next

def commit_tree_changes(object_store, tree, changes):
    """Commit a specified set of changes to a tree structure.

    This will apply a set of changes on top of an existing tree, storing new
    objects in object_store.

    changes are a list of tuples with (path, mode, object_sha).
    Paths can be both blobs and trees. See the mode and
    object sha to None deletes the path.

    This method works especially well if there are only a small
    number of changes to a big tree. For a large number of changes
    to a large tree, use e.g. commit_tree.

    Args:
      object_store: Object store to store new objects in
        and retrieve old ones from.
      tree: Original tree root
      changes: changes to apply
    Returns: New tree root object
    """
    pass

class OverlayObjectStore(BaseObjectStore):
    """Object store that can overlay multiple object stores."""

    def __init__(self, bases, add_store=None) -> None:
        self.bases = bases
        self.add_store = add_store

    def __iter__(self):
        done = set()
        for b in self.bases:
            for o_id in b:
                if o_id not in done:
                    yield o_id
                    done.add(o_id)

def read_packs_file(f):
    """Yield the packs listed in a packs file."""
    pass

class BucketBasedObjectStore(PackBasedObjectStore):
    """Object store implementation that uses a bucket store like S3 as backend."""

    def _iter_loose_objects(self):
        """Iterate over the SHAs of all loose objects."""
        pass

    def add_pack(self):
        """Add a new pack to this object store.

        Returns: Fileobject to write to, a commit function to
            call when the pack is finished and an abort
            function.
        """
        pass

def _collect_ancestors(store: ObjectContainer, heads, common: FrozenSet[ObjectID]=frozenset(), shallow: FrozenSet[ObjectID]=frozenset(), get_parents=lambda commit: commit.parents):
    """Collect all ancestors of heads up to (excluding) those in common.

    Args:
      heads: commits to start from
      common: commits to end at, or empty set to walk repository
        completely
      get_parents: Optional function for getting the parents of a
        commit.
    Returns: a tuple (A, B) where A - all commits reachable
        from heads but not present in common, B - common (shared) elements
        that are directly reachable from heads
    """
    pass

def iter_tree_contents(store: ObjectContainer, tree_id: Optional[ObjectID], *, include_trees: bool=False):
    """Iterate the contents of a tree and all subtrees.

    Iteration is depth-first pre-order, as in e.g. os.walk.

    Args:
      tree_id: SHA1 of the tree.
      include_trees: If True, include tree objects in the iteration.
    Returns: Iterator over TreeEntry namedtuples for all the objects in a
        tree.
    """
    pass

def peel_sha(store: ObjectContainer, sha: bytes) -> Tuple[ShaFile, ShaFile]:
    """Peel all tags from a SHA.

    Args:
      sha: The object SHA to peel.
    Returns: The fully-peeled SHA1 of a tag object, after peeling all
        intermediate tags; if the original ref does not point to a tag,
        this will equal the original SHA1.
    """
    pass