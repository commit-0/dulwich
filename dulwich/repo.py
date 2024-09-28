"""Repository access.

This module contains the base class for git repositories
(BaseRepo) and an implementation which uses a repository on
local disk (Repo).

"""
import os
import stat
import sys
import time
import warnings
from io import BytesIO
from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple, Union
if TYPE_CHECKING:
    from .config import ConfigFile, StackedConfig
    from .index import Index
from .errors import CommitError, HookError, NoIndexPresent, NotBlobError, NotCommitError, NotGitRepository, NotTagError, NotTreeError, RefFormatError
from .file import GitFile
from .hooks import CommitMsgShellHook, Hook, PostCommitShellHook, PostReceiveShellHook, PreCommitShellHook
from .line_ending import BlobNormalizer, TreeBlobNormalizer
from .object_store import DiskObjectStore, MemoryObjectStore, MissingObjectFinder, ObjectStoreGraphWalker, PackBasedObjectStore, peel_sha
from .objects import Blob, Commit, ObjectID, ShaFile, Tag, Tree, check_hexsha, valid_hexsha
from .pack import generate_unpacked_objects
from .refs import ANNOTATED_TAG_SUFFIX, LOCAL_BRANCH_PREFIX, LOCAL_TAG_PREFIX, SYMREF, DictRefsContainer, DiskRefsContainer, InfoRefsContainer, Ref, RefsContainer, _set_default_branch, _set_head, _set_origin_head, check_ref_format, read_packed_refs, read_packed_refs_with_peeled, serialize_refs, write_packed_refs
CONTROLDIR = '.git'
OBJECTDIR = 'objects'
REFSDIR = 'refs'
REFSDIR_TAGS = 'tags'
REFSDIR_HEADS = 'heads'
INDEX_FILENAME = 'index'
COMMONDIR = 'commondir'
GITDIR = 'gitdir'
WORKTREES = 'worktrees'
BASE_DIRECTORIES = [['branches'], [REFSDIR], [REFSDIR, REFSDIR_TAGS], [REFSDIR, REFSDIR_HEADS], ['hooks'], ['info']]
DEFAULT_BRANCH = b'master'

class InvalidUserIdentity(Exception):
    """User identity is not of the format 'user <email>'."""

    def __init__(self, identity) -> None:
        self.identity = identity

class DefaultIdentityNotFound(Exception):
    """Default identity could not be determined."""

def get_user_identity(config: 'StackedConfig', kind: Optional[str]=None) -> bytes:
    """Determine the identity to use for new commits.

    If kind is set, this first checks
    GIT_${KIND}_NAME and GIT_${KIND}_EMAIL.

    If those variables are not set, then it will fall back
    to reading the user.name and user.email settings from
    the specified configuration.

    If that also fails, then it will fall back to using
    the current users' identity as obtained from the host
    system (e.g. the gecos field, $EMAIL, $USER@$(hostname -f).

    Args:
      kind: Optional kind to return identity for,
        usually either "AUTHOR" or "COMMITTER".

    Returns:
      A user identity
    """
    pass

def check_user_identity(identity):
    """Verify that a user identity is formatted correctly.

    Args:
      identity: User identity bytestring
    Raises:
      InvalidUserIdentity: Raised when identity is invalid
    """
    pass

def parse_graftpoints(graftpoints: Iterable[bytes]) -> Dict[bytes, List[bytes]]:
    """Convert a list of graftpoints into a dict.

    Args:
      graftpoints: Iterator of graftpoint lines

    Each line is formatted as:
        <commit sha1> <parent sha1> [<parent sha1>]*

    Resulting dictionary is:
        <commit sha1>: [<parent sha1>*]

    https://git.wiki.kernel.org/index.php/GraftPoint
    """
    pass

def serialize_graftpoints(graftpoints: Dict[bytes, List[bytes]]) -> bytes:
    """Convert a dictionary of grafts into string.

    The graft dictionary is:
        <commit sha1>: [<parent sha1>*]

    Each line is formatted as:
        <commit sha1> <parent sha1> [<parent sha1>]*

    https://git.wiki.kernel.org/index.php/GraftPoint

    """
    pass

def _set_filesystem_hidden(path):
    """Mark path as to be hidden if supported by platform and filesystem.

    On win32 uses SetFileAttributesW api:
    <https://docs.microsoft.com/windows/desktop/api/fileapi/nf-fileapi-setfileattributesw>
    """
    pass

class ParentsProvider:

    def __init__(self, store, grafts={}, shallows=[]) -> None:
        self.store = store
        self.grafts = grafts
        self.shallows = set(shallows)

class BaseRepo:
    """Base class for a git repository.

    This base class is meant to be used for Repository implementations that e.g.
    work on top of a different transport than a standard filesystem path.

    Attributes:
      object_store: Dictionary-like object for accessing
        the objects
      refs: Dictionary-like object with the refs in this
        repository
    """

    def __init__(self, object_store: PackBasedObjectStore, refs: RefsContainer) -> None:
        """Open a repository.

        This shouldn't be called directly, but rather through one of the
        base classes, such as MemoryRepo or Repo.

        Args:
          object_store: Object store to use
          refs: Refs container to use
        """
        self.object_store = object_store
        self.refs = refs
        self._graftpoints: Dict[bytes, List[bytes]] = {}
        self.hooks: Dict[str, Hook] = {}

    def _determine_file_mode(self) -> bool:
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        pass

    def _determine_symlinks(self) -> bool:
        """Probe the filesystem to determine whether symlinks can be created.

        Returns: True if symlinks can be created, False otherwise.
        """
        pass

    def _init_files(self, bare: bool, symlinks: Optional[bool]=None) -> None:
        """Initialize a default set of named files."""
        pass

    def get_named_file(self, path: str) -> Optional[BinaryIO]:
        """Get a file from the control dir with a specific name.

        Although the filename should be interpreted as a filename relative to
        the control dir in a disk-based Repo, the object returned need not be
        pointing to a file in that location.

        Args:
          path: The path to the file, relative to the control dir.
        Returns: An open file object, or None if the file does not exist.
        """
        pass

    def _put_named_file(self, path: str, contents: bytes):
        """Write a file to the control dir with the given name and contents.

        Args:
          path: The path to the file, relative to the control dir.
          contents: A string to write to the file.
        """
        pass

    def _del_named_file(self, path: str):
        """Delete a file in the control directory with the given name."""
        pass

    def open_index(self) -> 'Index':
        """Open the index for this repository.

        Raises:
          NoIndexPresent: If no index is present
        Returns: The matching `Index`
        """
        pass

    def fetch(self, target, determine_wants=None, progress=None, depth=None):
        """Fetch objects into another repository.

        Args:
          target: The target repository
          determine_wants: Optional function to determine what refs to
            fetch.
          progress: Optional progress function
          depth: Optional shallow fetch depth
        Returns: The local refs
        """
        pass

    def fetch_pack_data(self, determine_wants, graph_walker, progress, get_tagged=None, depth=None):
        """Fetch the pack data required for a set of revisions.

        Args:
          determine_wants: Function that takes a dictionary with heads
            and returns the list of heads to fetch.
          graph_walker: Object that can iterate over the list of revisions
            to fetch and has an "ack" method that will be called to acknowledge
            that a revision is present.
          progress: Simple progress function that will be called with
            updated progress strings.
          get_tagged: Function that returns a dict of pointed-to sha ->
            tag sha for including tags.
          depth: Shallow fetch depth
        Returns: count and iterator over pack data
        """
        pass

    def find_missing_objects(self, determine_wants, graph_walker, progress, get_tagged=None, depth=None) -> Optional[MissingObjectFinder]:
        """Fetch the missing objects required for a set of revisions.

        Args:
          determine_wants: Function that takes a dictionary with heads
            and returns the list of heads to fetch.
          graph_walker: Object that can iterate over the list of revisions
            to fetch and has an "ack" method that will be called to acknowledge
            that a revision is present.
          progress: Simple progress function that will be called with
            updated progress strings.
          get_tagged: Function that returns a dict of pointed-to sha ->
            tag sha for including tags.
          depth: Shallow fetch depth
        Returns: iterator over objects, with __len__ implemented
        """
        pass

    def generate_pack_data(self, have: List[ObjectID], want: List[ObjectID], progress: Optional[Callable[[str], None]]=None, ofs_delta: Optional[bool]=None):
        """Generate pack data objects for a set of wants/haves.

        Args:
          have: List of SHA1s of objects that should not be sent
          want: List of SHA1s of objects that should be sent
          ofs_delta: Whether OFS deltas can be included
          progress: Optional progress reporting method
        """
        pass

    def get_graph_walker(self, heads: Optional[List[ObjectID]]=None) -> ObjectStoreGraphWalker:
        """Retrieve a graph walker.

        A graph walker is used by a remote repository (or proxy)
        to find out which objects are present in this repository.

        Args:
          heads: Repository heads to use (optional)
        Returns: A graph walker object
        """
        pass

    def get_refs(self) -> Dict[bytes, bytes]:
        """Get dictionary with all refs.

        Returns: A ``dict`` mapping ref names to SHA1s
        """
        pass

    def head(self) -> bytes:
        """Return the SHA1 pointed at by HEAD."""
        pass

    def get_object(self, sha: bytes) -> ShaFile:
        """Retrieve the object with the specified SHA.

        Args:
          sha: SHA to retrieve
        Returns: A ShaFile object
        Raises:
          KeyError: when the object can not be found
        """
        pass

    def get_parents(self, sha: bytes, commit: Optional[Commit]=None) -> List[bytes]:
        """Retrieve the parents of a specific commit.

        If the specific commit is a graftpoint, the graft parents
        will be returned instead.

        Args:
          sha: SHA of the commit for which to retrieve the parents
          commit: Optional commit matching the sha
        Returns: List of parents
        """
        pass

    def get_config(self) -> 'ConfigFile':
        """Retrieve the config object.

        Returns: `ConfigFile` object for the ``.git/config`` file.
        """
        pass

    def get_worktree_config(self) -> 'ConfigFile':
        """Retrieve the worktree config object."""
        pass

    def get_description(self):
        """Retrieve the description for this repository.

        Returns: String with the description of the repository
            as set by the user.
        """
        pass

    def set_description(self, description):
        """Set the description for this repository.

        Args:
          description: Text to set as description for this repository.
        """
        pass

    def get_config_stack(self) -> 'StackedConfig':
        """Return a config stack for this repository.

        This stack accesses the configuration for both this repository
        itself (.git/config) and the global configuration, which usually
        lives in ~/.gitconfig.

        Returns: `Config` instance for this repository
        """
        pass

    def get_shallow(self) -> Set[ObjectID]:
        """Get the set of shallow commits.

        Returns: Set of shallow commits.
        """
        pass

    def update_shallow(self, new_shallow, new_unshallow):
        """Update the list of shallow objects.

        Args:
          new_shallow: Newly shallow objects
          new_unshallow: Newly no longer shallow objects
        """
        pass

    def get_peeled(self, ref: Ref) -> ObjectID:
        """Get the peeled value of a ref.

        Args:
          ref: The refname to peel.
        Returns: The fully-peeled SHA1 of a tag object, after peeling all
            intermediate tags; if the original ref does not point to a tag,
            this will equal the original SHA1.
        """
        pass

    def get_walker(self, include: Optional[List[bytes]]=None, *args, **kwargs):
        """Obtain a walker for this repository.

        Args:
          include: Iterable of SHAs of commits to include along with their
            ancestors. Defaults to [HEAD]
          exclude: Iterable of SHAs of commits to exclude along with their
            ancestors, overriding includes.
          order: ORDER_* constant specifying the order of results.
            Anything other than ORDER_DATE may result in O(n) memory usage.
          reverse: If True, reverse the order of output, requiring O(n)
            memory.
          max_entries: The maximum number of entries to yield, or None for
            no limit.
          paths: Iterable of file or subtree paths to show entries for.
          rename_detector: diff.RenameDetector object for detecting
            renames.
          follow: If True, follow path across renames/copies. Forces a
            default rename_detector.
          since: Timestamp to list commits after.
          until: Timestamp to list commits before.
          queue_cls: A class to use for a queue of commits, supporting the
            iterator protocol. The constructor takes a single argument, the
            Walker.
        Returns: A `Walker` object
        """
        pass

    def __getitem__(self, name: Union[ObjectID, Ref]):
        """Retrieve a Git object by SHA1 or ref.

        Args:
          name: A Git object SHA1 or a ref name
        Returns: A `ShaFile` object, such as a Commit or Blob
        Raises:
          KeyError: when the specified ref or object does not exist
        """
        if not isinstance(name, bytes):
            raise TypeError(f"'name' must be bytestring, not {type(name).__name__:.80}")
        if len(name) in (20, 40):
            try:
                return self.object_store[name]
            except (KeyError, ValueError):
                pass
        try:
            return self.object_store[self.refs[name]]
        except RefFormatError as exc:
            raise KeyError(name) from exc

    def __contains__(self, name: bytes) -> bool:
        """Check if a specific Git object or ref is present.

        Args:
          name: Git object SHA1 or ref name
        """
        if len(name) == 20 or (len(name) == 40 and valid_hexsha(name)):
            return name in self.object_store or name in self.refs
        else:
            return name in self.refs

    def __setitem__(self, name: bytes, value: Union[ShaFile, bytes]) -> None:
        """Set a ref.

        Args:
          name: ref name
          value: Ref value - either a ShaFile object, or a hex sha
        """
        if name.startswith(b'refs/') or name == b'HEAD':
            if isinstance(value, ShaFile):
                self.refs[name] = value.id
            elif isinstance(value, bytes):
                self.refs[name] = value
            else:
                raise TypeError(value)
        else:
            raise ValueError(name)

    def __delitem__(self, name: bytes) -> None:
        """Remove a ref.

        Args:
          name: Name of the ref to remove
        """
        if name.startswith(b'refs/') or name == b'HEAD':
            del self.refs[name]
        else:
            raise ValueError(name)

    def _get_user_identity(self, config: 'StackedConfig', kind: Optional[str]=None) -> bytes:
        """Determine the identity to use for new commits."""
        pass

    def _add_graftpoints(self, updated_graftpoints: Dict[bytes, List[bytes]]):
        """Add or modify graftpoints.

        Args:
          updated_graftpoints: Dict of commit shas to list of parent shas
        """
        pass

    def _remove_graftpoints(self, to_remove: List[bytes]=[]) -> None:
        """Remove graftpoints.

        Args:
          to_remove: List of commit shas
        """
        pass

    def do_commit(self, message: Optional[bytes]=None, committer: Optional[bytes]=None, author: Optional[bytes]=None, commit_timestamp=None, commit_timezone=None, author_timestamp=None, author_timezone=None, tree: Optional[ObjectID]=None, encoding: Optional[bytes]=None, ref: Ref=b'HEAD', merge_heads: Optional[List[ObjectID]]=None, no_verify: bool=False, sign: bool=False):
        """Create a new commit.

        If not specified, committer and author default to
        get_user_identity(..., 'COMMITTER')
        and get_user_identity(..., 'AUTHOR') respectively.

        Args:
          message: Commit message
          committer: Committer fullname
          author: Author fullname
          commit_timestamp: Commit timestamp (defaults to now)
          commit_timezone: Commit timestamp timezone (defaults to GMT)
          author_timestamp: Author timestamp (defaults to commit
            timestamp)
          author_timezone: Author timestamp timezone
            (defaults to commit timestamp timezone)
          tree: SHA1 of the tree root to use (if not specified the
            current index will be committed).
          encoding: Encoding
          ref: Optional ref to commit to (defaults to current branch)
          merge_heads: Merge heads (defaults to .git/MERGE_HEAD)
          no_verify: Skip pre-commit and commit-msg hooks
          sign: GPG Sign the commit (bool, defaults to False,
            pass True to use default GPG key,
            pass a str containing Key ID to use a specific GPG key)

        Returns:
          New commit SHA1
        """
        pass

def read_gitfile(f):
    """Read a ``.git`` file.

    The first line of the file should start with "gitdir: "

    Args:
      f: File-like object to read from
    Returns: A path
    """
    pass

class UnsupportedVersion(Exception):
    """Unsupported repository version."""

    def __init__(self, version) -> None:
        self.version = version

class UnsupportedExtension(Exception):
    """Unsupported repository extension."""

    def __init__(self, extension) -> None:
        self.extension = extension

class Repo(BaseRepo):
    """A git repository backed by local disk.

    To open an existing repository, call the constructor with
    the path of the repository.

    To create a new repository, use the Repo.init class method.

    Note that a repository object may hold on to resources such
    as file handles for performance reasons; call .close() to free
    up those resources.

    Attributes:
      path: Path to the working copy (if it exists) or repository control
        directory (if the repository is bare)
      bare: Whether this is a bare repository
    """
    path: str
    bare: bool

    def __init__(self, root: str, object_store: Optional[PackBasedObjectStore]=None, bare: Optional[bool]=None) -> None:
        hidden_path = os.path.join(root, CONTROLDIR)
        if bare is None:
            if os.path.isfile(hidden_path) or os.path.isdir(os.path.join(hidden_path, OBJECTDIR)):
                bare = False
            elif os.path.isdir(os.path.join(root, OBJECTDIR)) and os.path.isdir(os.path.join(root, REFSDIR)):
                bare = True
            else:
                raise NotGitRepository('No git repository was found at {path}'.format(**dict(path=root)))
        self.bare = bare
        if bare is False:
            if os.path.isfile(hidden_path):
                with open(hidden_path) as f:
                    path = read_gitfile(f)
                self._controldir = os.path.join(root, path)
            else:
                self._controldir = hidden_path
        else:
            self._controldir = root
        commondir = self.get_named_file(COMMONDIR)
        if commondir is not None:
            with commondir:
                self._commondir = os.path.join(self.controldir(), os.fsdecode(commondir.read().rstrip(b'\r\n')))
        else:
            self._commondir = self._controldir
        self.path = root
        config = self.get_config()
        try:
            repository_format_version = config.get('core', 'repositoryformatversion')
            format_version = 0 if repository_format_version is None else int(repository_format_version)
        except KeyError:
            format_version = 0
        if format_version not in (0, 1):
            raise UnsupportedVersion(format_version)
        for extension, _value in config.items((b'extensions',)):
            if extension.lower() not in (b'worktreeconfig',):
                raise UnsupportedExtension(extension)
        if object_store is None:
            object_store = DiskObjectStore.from_config(os.path.join(self.commondir(), OBJECTDIR), config)
        refs = DiskRefsContainer(self.commondir(), self._controldir, logger=self._write_reflog)
        BaseRepo.__init__(self, object_store, refs)
        self._graftpoints = {}
        graft_file = self.get_named_file(os.path.join('info', 'grafts'), basedir=self.commondir())
        if graft_file:
            with graft_file:
                self._graftpoints.update(parse_graftpoints(graft_file))
        graft_file = self.get_named_file('shallow', basedir=self.commondir())
        if graft_file:
            with graft_file:
                self._graftpoints.update(parse_graftpoints(graft_file))
        self.hooks['pre-commit'] = PreCommitShellHook(self.path, self.controldir())
        self.hooks['commit-msg'] = CommitMsgShellHook(self.controldir())
        self.hooks['post-commit'] = PostCommitShellHook(self.controldir())
        self.hooks['post-receive'] = PostReceiveShellHook(self.controldir())

    @classmethod
    def discover(cls, start='.'):
        """Iterate parent directories to discover a repository.

        Return a Repo object for the first parent directory that looks like a
        Git repository.

        Args:
          start: The directory to start discovery from (defaults to '.')
        """
        pass

    def controldir(self):
        """Return the path of the control directory."""
        pass

    def commondir(self):
        """Return the path of the common directory.

        For a main working tree, it is identical to controldir().

        For a linked working tree, it is the control directory of the
        main working tree.
        """
        pass

    def _determine_file_mode(self):
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        pass

    def _determine_symlinks(self):
        """Probe the filesystem to determine whether symlinks can be created.

        Returns: True if symlinks can be created, False otherwise.
        """
        pass

    def _put_named_file(self, path, contents):
        """Write a file to the control dir with the given name and contents.

        Args:
          path: The path to the file, relative to the control dir.
          contents: A string to write to the file.
        """
        pass

    def get_named_file(self, path, basedir=None):
        """Get a file from the control dir with a specific name.

        Although the filename should be interpreted as a filename relative to
        the control dir in a disk-based Repo, the object returned need not be
        pointing to a file in that location.

        Args:
          path: The path to the file, relative to the control dir.
          basedir: Optional argument that specifies an alternative to the
            control dir.
        Returns: An open file object, or None if the file does not exist.
        """
        pass

    def index_path(self):
        """Return path to the index file."""
        pass

    def open_index(self) -> 'Index':
        """Open the index for this repository.

        Raises:
          NoIndexPresent: If no index is present
        Returns: The matching `Index`
        """
        pass

    def has_index(self):
        """Check if an index is present."""
        pass

    def stage(self, fs_paths: Union[str, bytes, os.PathLike, Iterable[Union[str, bytes, os.PathLike]]]) -> None:
        """Stage a set of paths.

        Args:
          fs_paths: List of paths, relative to the repository path
        """
        pass

    def unstage(self, fs_paths: List[str]):
        """Unstage specific file in the index
        Args:
          fs_paths: a list of files to unstage,
            relative to the repository path.
        """
        pass

    def clone(self, target_path, *, mkdir=True, bare=False, origin=b'origin', checkout=None, branch=None, progress=None, depth=None, symlinks=None) -> 'Repo':
        """Clone this repository.

        Args:
          target_path: Target path
          mkdir: Create the target directory
          bare: Whether to create a bare repository
          checkout: Whether or not to check-out HEAD after cloning
          origin: Base name for refs in target repository
            cloned from this repository
          branch: Optional branch or tag to be used as HEAD in the new repository
            instead of this repository's HEAD.
          progress: Optional progress function
          depth: Depth at which to fetch
          symlinks: Symlinks setting (default to autodetect)
        Returns: Created repository as `Repo`
        """
        pass

    def reset_index(self, tree: Optional[bytes]=None):
        """Reset the index back to a specific tree.

        Args:
          tree: Tree SHA to reset to, None for current HEAD tree.
        """
        pass

    def get_config(self) -> 'ConfigFile':
        """Retrieve the config object.

        Returns: `ConfigFile` object for the ``.git/config`` file.
        """
        pass

    def get_description(self):
        """Retrieve the description of this repository.

        Returns: A string describing the repository or None.
        """
        pass

    def __repr__(self) -> str:
        return f'<Repo at {self.path!r}>'

    def set_description(self, description):
        """Set the description for this repository.

        Args:
          description: Text to set as description for this repository.
        """
        pass

    @classmethod
    def init(cls, path: str, *, mkdir: bool=False, config=None, default_branch=None, symlinks: Optional[bool]=None) -> 'Repo':
        """Create a new repository.

        Args:
          path: Path in which to create the repository
          mkdir: Whether to create the directory
        Returns: `Repo` instance
        """
        pass

    @classmethod
    def _init_new_working_directory(cls, path, main_repo, identifier=None, mkdir=False):
        """Create a new working directory linked to a repository.

        Args:
          path: Path in which to create the working tree.
          main_repo: Main repository to reference
          identifier: Worktree identifier
          mkdir: Whether to create the directory
        Returns: `Repo` instance
        """
        pass

    @classmethod
    def init_bare(cls, path, *, mkdir=False, object_store=None, config=None, default_branch=None):
        """Create a new bare repository.

        ``path`` should already exist and be an empty directory.

        Args:
          path: Path to create bare repository in
        Returns: a `Repo` instance
        """
        pass
    create = init_bare

    def close(self):
        """Close any files opened by this repository."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_blob_normalizer(self):
        """Return a BlobNormalizer object."""
        pass

class MemoryRepo(BaseRepo):
    """Repo that stores refs, objects, and named files in memory.

    MemoryRepos are always bare: they have no working tree and no index, since
    those have a stronger dependency on the filesystem.
    """

    def __init__(self) -> None:
        from .config import ConfigFile
        self._reflog: List[Any] = []
        refs_container = DictRefsContainer({}, logger=self._append_reflog)
        BaseRepo.__init__(self, MemoryObjectStore(), refs_container)
        self._named_files: Dict[str, bytes] = {}
        self.bare = True
        self._config = ConfigFile()
        self._description = None

    def _determine_file_mode(self):
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        pass

    def _determine_symlinks(self):
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        pass

    def _put_named_file(self, path, contents):
        """Write a file to the control dir with the given name and contents.

        Args:
          path: The path to the file, relative to the control dir.
          contents: A string to write to the file.
        """
        pass

    def get_named_file(self, path, basedir=None):
        """Get a file from the control dir with a specific name.

        Although the filename should be interpreted as a filename relative to
        the control dir in a disk-baked Repo, the object returned need not be
        pointing to a file in that location.

        Args:
          path: The path to the file, relative to the control dir.
        Returns: An open file object, or None if the file does not exist.
        """
        pass

    def open_index(self):
        """Fail to open index for this repo, since it is bare.

        Raises:
          NoIndexPresent: Raised when no index is present
        """
        pass

    def get_config(self):
        """Retrieve the config object.

        Returns: `ConfigFile` object.
        """
        pass

    @classmethod
    def init_bare(cls, objects, refs):
        """Create a new bare repository in memory.

        Args:
          objects: Objects for the new repository,
            as iterable
          refs: Refs as dictionary, mapping names
            to object SHA1s
        """
        pass