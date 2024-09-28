"""Simple wrapper that provides porcelain-like functions on top of Dulwich.

Currently implemented:
 * archive
 * add
 * branch{_create,_delete,_list}
 * check-ignore
 * checkout_branch
 * clone
 * commit
 * commit-tree
 * daemon
 * describe
 * diff-tree
 * fetch
 * for-each-ref
 * init
 * ls-files
 * ls-remote
 * ls-tree
 * pull
 * push
 * rm
 * remote{_add}
 * receive-pack
 * reset
 * submodule_add
 * submodule_init
 * submodule_list
 * rev-list
 * tag{_create,_delete,_list}
 * upload-pack
 * update-server-info
 * status
 * symbolic-ref

These functions are meant to behave similarly to the git subcommands.
Differences in behaviour are considered bugs.

Note: one of the consequences of this is that paths tend to be
interpreted relative to the current working directory rather than relative
to the repository root.

Functions should generally accept both unicode strings and bytestrings
"""
import datetime
import fnmatch
import os
import posixpath
import stat
import sys
import time
from collections import namedtuple
from contextlib import closing, contextmanager
from io import BytesIO, RawIOBase
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from .archive import tar_stream
from .client import get_transport_and_path
from .config import Config, ConfigFile, StackedConfig, read_submodules
from .diff_tree import CHANGE_ADD, CHANGE_COPY, CHANGE_DELETE, CHANGE_MODIFY, CHANGE_RENAME, RENAME_CHANGE_TYPES
from .errors import SendPackError
from .file import ensure_dir_exists
from .graph import can_fast_forward
from .ignore import IgnoreFilterManager
from .index import _fs_to_tree_path, blob_from_path_and_stat, build_file_from_blob, get_unstaged_changes, index_entry_from_stat
from .object_store import iter_tree_contents, tree_lookup_path
from .objects import Commit, Tag, format_timezone, parse_timezone, pretty_format_tree_entry
from .objectspec import parse_commit, parse_object, parse_ref, parse_reftuples, parse_tree, to_bytes
from .pack import write_pack_from_container, write_pack_index
from .patch import write_tree_diff
from .protocol import ZERO_SHA, Protocol
from .refs import LOCAL_BRANCH_PREFIX, LOCAL_REMOTE_PREFIX, LOCAL_TAG_PREFIX, _import_remote_refs
from .repo import BaseRepo, Repo, get_user_identity
from .server import FileSystemBackend, ReceivePackHandler, TCPGitServer, UploadPackHandler
from .server import update_server_info as server_update_server_info
GitStatus = namedtuple('GitStatus', 'staged unstaged untracked')

class NoneStream(RawIOBase):
    """Fallback if stdout or stderr are unavailable, does nothing."""
default_bytes_out_stream = getattr(sys.stdout, 'buffer', None) or NoneStream()
default_bytes_err_stream = getattr(sys.stderr, 'buffer', None) or NoneStream()
DEFAULT_ENCODING = 'utf-8'

class Error(Exception):
    """Porcelain-based error."""

    def __init__(self, msg) -> None:
        super().__init__(msg)

class RemoteExists(Error):
    """Raised when the remote already exists."""

class TimezoneFormatError(Error):
    """Raised when the timezone cannot be determined from a given string."""

class CheckoutError(Error):
    """Indicates that a checkout cannot be performed."""

def parse_timezone_format(tz_str):
    """Parse given string and attempt to return a timezone offset.

    Different formats are considered in the following order:

     - Git internal format: <unix timestamp> <timezone offset>
     - RFC 2822: e.g. Mon, 20 Nov 1995 19:12:08 -0500
     - ISO 8601: e.g. 1995-11-20T19:12:08-0500

    Args:
      tz_str: datetime string
    Returns: Timezone offset as integer
    Raises:
      TimezoneFormatError: if timezone information cannot be extracted
    """
    pass

def get_user_timezones():
    """Retrieve local timezone as described in
    https://raw.githubusercontent.com/git/git/v2.3.0/Documentation/date-formats.txt
    Returns: A tuple containing author timezone, committer timezone.
    """
    pass

def open_repo(path_or_repo):
    """Open an argument that can be a repository or a path for a repository."""
    pass

@contextmanager
def _noop_context_manager(obj):
    """Context manager that has the same api as closing but does nothing."""
    pass

def open_repo_closing(path_or_repo):
    """Open an argument that can be a repository or a path for a repository.
    returns a context manager that will close the repo on exit if the argument
    is a path, else does nothing if the argument is a repo.
    """
    pass

def path_to_tree_path(repopath, path, tree_encoding=DEFAULT_ENCODING):
    """Convert a path to a path usable in an index, e.g. bytes and relative to
    the repository root.

    Args:
      repopath: Repository path, absolute or relative to the cwd
      path: A path, absolute or relative to the cwd
    Returns: A path formatted for use in e.g. an index
    """
    pass

class DivergedBranches(Error):
    """Branches have diverged and fast-forward is not possible."""

    def __init__(self, current_sha, new_sha) -> None:
        self.current_sha = current_sha
        self.new_sha = new_sha

def check_diverged(repo, current_sha, new_sha):
    """Check if updating to a sha can be done with fast forwarding.

    Args:
      repo: Repository object
      current_sha: Current head sha
      new_sha: New head sha
    """
    pass

def archive(repo, committish=None, outstream=default_bytes_out_stream, errstream=default_bytes_err_stream):
    """Create an archive.

    Args:
      repo: Path of repository for which to generate an archive.
      committish: Commit SHA1 or ref to use
      outstream: Output stream (defaults to stdout)
      errstream: Error stream (defaults to stderr)
    """
    pass

def update_server_info(repo='.'):
    """Update server info files for a repository.

    Args:
      repo: path to the repository
    """
    pass

def symbolic_ref(repo, ref_name, force=False):
    """Set git symbolic ref into HEAD.

    Args:
      repo: path to the repository
      ref_name: short name of the new ref
      force: force settings without checking if it exists in refs/heads
    """
    pass

def commit(repo='.', message=None, author=None, author_timezone=None, committer=None, commit_timezone=None, encoding=None, no_verify=False, signoff=False):
    """Create a new commit.

    Args:
      repo: Path to repository
      message: Optional commit message
      author: Optional author name and email
      author_timezone: Author timestamp timezone
      committer: Optional committer name and email
      commit_timezone: Commit timestamp timezone
      no_verify: Skip pre-commit and commit-msg hooks
      signoff: GPG Sign the commit (bool, defaults to False,
        pass True to use default GPG key,
        pass a str containing Key ID to use a specific GPG key)
    Returns: SHA1 of the new commit
    """
    pass

def commit_tree(repo, tree, message=None, author=None, committer=None):
    """Create a new commit object.

    Args:
      repo: Path to repository
      tree: An existing tree object
      author: Optional author name and email
      committer: Optional committer name and email
    """
    pass

def init(path='.', *, bare=False, symlinks: Optional[bool]=None):
    """Create a new git repository.

    Args:
      path: Path to repository.
      bare: Whether to create a bare repository.
      symlinks: Whether to create actual symlinks (defaults to autodetect)
    Returns: A Repo instance
    """
    pass

def clone(source, target=None, bare=False, checkout=None, errstream=default_bytes_err_stream, outstream=None, origin: Optional[str]='origin', depth: Optional[int]=None, branch: Optional[Union[str, bytes]]=None, config: Optional[Config]=None, refspecs=None, refspec_encoding=DEFAULT_ENCODING, filter_spec=None, protocol_version: Optional[int]=None, **kwargs):
    """Clone a local or remote git repository.

    Args:
      source: Path or URL for source repository
      target: Path to target repository (optional)
      bare: Whether or not to create a bare repository
      checkout: Whether or not to check-out HEAD after cloning
      errstream: Optional stream to write progress to
      outstream: Optional stream to write progress to (deprecated)
      origin: Name of remote from the repository used to clone
      depth: Depth to fetch at
      branch: Optional branch or tag to be used as HEAD in the new repository
        instead of the cloned repository's HEAD.
      config: Configuration to use
      refspecs: refspecs to fetch. Can be a bytestring, a string, or a list of
        bytestring/string.
      refspec_encoding: Character encoding of bytestrings provided in the refspecs parameter.
        If not specified, the internal default encoding will be used.
      filter_spec: A git-rev-list-style object filter spec, as an ASCII string.
        Only used if the server supports the Git protocol-v2 'filter'
        feature, and ignored otherwise.
      protocol_version: desired Git protocol version. By default the highest
        mutually supported protocol version will be used.
    Returns: The new repository
    """
    pass

def add(repo='.', paths=None):
    """Add files to the staging area.

    Args:
      repo: Repository for the files
      paths: Paths to add.  No value passed stages all modified files.
    Returns: Tuple with set of added files and ignored files

    If the repository contains ignored directories, the returned set will
    contain the path to an ignored directory (with trailing slash). Individual
    files within ignored directories will not be returned.
    """
    pass

def _is_subdir(subdir, parentdir):
    """Check whether subdir is parentdir or a subdir of parentdir.

    If parentdir or subdir is a relative path, it will be disamgibuated
    relative to the pwd.
    """
    pass

def clean(repo='.', target_dir=None):
    """Remove any untracked files from the target directory recursively.

    Equivalent to running ``git clean -fd`` in target_dir.

    Args:
      repo: Repository where the files may be tracked
      target_dir: Directory to clean - current directory if None
    """
    pass

def remove(repo='.', paths=None, cached=False):
    """Remove files from the staging area.

    Args:
      repo: Repository for the files
      paths: Paths to remove
    """
    pass
rm = remove

def print_commit(commit, decode, outstream=sys.stdout):
    """Write a human-readable commit log entry.

    Args:
      commit: A `Commit` object
      outstream: A stream file to write to
    """
    pass

def print_tag(tag, decode, outstream=sys.stdout):
    """Write a human-readable tag.

    Args:
      tag: A `Tag` object
      decode: Function for decoding bytes to unicode string
      outstream: A stream to write to
    """
    pass

def show_blob(repo, blob, decode, outstream=sys.stdout):
    """Write a blob to a stream.

    Args:
      repo: A `Repo` object
      blob: A `Blob` object
      decode: Function for decoding bytes to unicode string
      outstream: A stream file to write to
    """
    pass

def show_commit(repo, commit, decode, outstream=sys.stdout):
    """Show a commit to a stream.

    Args:
      repo: A `Repo` object
      commit: A `Commit` object
      decode: Function for decoding bytes to unicode string
      outstream: Stream to write to
    """
    pass

def show_tree(repo, tree, decode, outstream=sys.stdout):
    """Print a tree to a stream.

    Args:
      repo: A `Repo` object
      tree: A `Tree` object
      decode: Function for decoding bytes to unicode string
      outstream: Stream to write to
    """
    pass

def show_tag(repo, tag, decode, outstream=sys.stdout):
    """Print a tag to a stream.

    Args:
      repo: A `Repo` object
      tag: A `Tag` object
      decode: Function for decoding bytes to unicode string
      outstream: Stream to write to
    """
    pass

def print_name_status(changes):
    """Print a simple status summary, listing changed files."""
    pass

def log(repo='.', paths=None, outstream=sys.stdout, max_entries=None, reverse=False, name_status=False):
    """Write commit logs.

    Args:
      repo: Path to repository
      paths: Optional set of specific paths to print entries for
      outstream: Stream to write log output to
      reverse: Reverse order in which entries are printed
      name_status: Print name status
      max_entries: Optional maximum number of entries to display
    """
    pass

def show(repo='.', objects=None, outstream=sys.stdout, default_encoding=DEFAULT_ENCODING):
    """Print the changes in a commit.

    Args:
      repo: Path to repository
      objects: Objects to show (defaults to [HEAD])
      outstream: Stream to write to
      default_encoding: Default encoding to use if none is set in the
        commit
    """
    pass

def diff_tree(repo, old_tree, new_tree, outstream=default_bytes_out_stream):
    """Compares the content and mode of blobs found via two tree objects.

    Args:
      repo: Path to repository
      old_tree: Id of old tree
      new_tree: Id of new tree
      outstream: Stream to write to
    """
    pass

def rev_list(repo, commits, outstream=sys.stdout):
    """Lists commit objects in reverse chronological order.

    Args:
      repo: Path to repository
      commits: Commits over which to iterate
      outstream: Stream to write to
    """
    pass

def submodule_add(repo, url, path=None, name=None):
    """Add a new submodule.

    Args:
      repo: Path to repository
      url: URL of repository to add as submodule
      path: Path where submodule should live
    """
    pass

def submodule_init(repo):
    """Initialize submodules.

    Args:
      repo: Path to repository
    """
    pass

def submodule_list(repo):
    """List submodules.

    Args:
      repo: Path to repository
    """
    pass

def tag_create(repo, tag, author=None, message=None, annotated=False, objectish='HEAD', tag_time=None, tag_timezone=None, sign=False, encoding=DEFAULT_ENCODING):
    """Creates a tag in git via dulwich calls.

    Args:
      repo: Path to repository
      tag: tag string
      author: tag author (optional, if annotated is set)
      message: tag message (optional)
      annotated: whether to create an annotated tag
      objectish: object the tag should point at, defaults to HEAD
      tag_time: Optional time for annotated tag
      tag_timezone: Optional timezone for annotated tag
      sign: GPG Sign the tag (bool, defaults to False,
        pass True to use default GPG key,
        pass a str containing Key ID to use a specific GPG key)
    """
    pass

def tag_list(repo, outstream=sys.stdout):
    """List all tags.

    Args:
      repo: Path to repository
      outstream: Stream to write tags to
    """
    pass

def tag_delete(repo, name):
    """Remove a tag.

    Args:
      repo: Path to repository
      name: Name of tag to remove
    """
    pass

def reset(repo, mode, treeish='HEAD'):
    """Reset current HEAD to the specified state.

    Args:
      repo: Path to repository
      mode: Mode ("hard", "soft", "mixed")
      treeish: Treeish to reset to
    """
    pass

def push(repo, remote_location=None, refspecs=None, outstream=default_bytes_out_stream, errstream=default_bytes_err_stream, force=False, **kwargs):
    """Remote push with dulwich via dulwich.client.

    Args:
      repo: Path to repository
      remote_location: Location of the remote
      refspecs: Refs to push to remote
      outstream: A stream file to write output
      errstream: A stream file to write errors
      force: Force overwriting refs
    """
    pass

def pull(repo, remote_location=None, refspecs=None, outstream=default_bytes_out_stream, errstream=default_bytes_err_stream, fast_forward=True, force=False, refspec_encoding=DEFAULT_ENCODING, filter_spec=None, protocol_version=None, **kwargs):
    """Pull from remote via dulwich.client.

    Args:
      repo: Path to repository
      remote_location: Location of the remote
      refspecs: refspecs to fetch. Can be a bytestring, a string, or a list of
        bytestring/string.
      outstream: A stream file to write to output
      errstream: A stream file to write to errors
      refspec_encoding: Character encoding of bytestrings provided in the refspecs parameter.
        If not specified, the internal default encoding will be used.
      filter_spec: A git-rev-list-style object filter spec, as an ASCII string.
        Only used if the server supports the Git protocol-v2 'filter'
        feature, and ignored otherwise.
      protocol_version: desired Git protocol version. By default the highest
        mutually supported protocol version will be used
    """
    pass

def status(repo='.', ignored=False, untracked_files='all'):
    """Returns staged, unstaged, and untracked changes relative to the HEAD.

    Args:
      repo: Path to repository or repository object
      ignored: Whether to include ignored files in untracked
      untracked_files: How to handle untracked files, defaults to "all":
          "no": do not return untracked files
          "all": include all files in untracked directories
        Using untracked_files="no" can be faster than "all" when the worktreee
          contains many untracked files/directories.

    Note: untracked_files="normal" (git's default) is not implemented.

    Returns: GitStatus tuple,
        staged -  dict with lists of staged paths (diff index/HEAD)
        unstaged -  list of unstaged paths (diff index/working-tree)
        untracked - list of untracked, un-ignored & non-.git paths
    """
    pass

def _walk_working_dir_paths(frompath, basepath, prune_dirnames=None):
    """Get path, is_dir for files in working dir from frompath.

    Args:
      frompath: Path to begin walk
      basepath: Path to compare to
      prune_dirnames: Optional callback to prune dirnames during os.walk
        dirnames will be set to result of prune_dirnames(dirpath, dirnames)
    """
    pass

def get_untracked_paths(frompath, basepath, index, exclude_ignored=False, untracked_files='all'):
    """Get untracked paths.

    Args:
      frompath: Path to walk
      basepath: Path to compare to
      index: Index to check against
      exclude_ignored: Whether to exclude ignored paths
      untracked_files: How to handle untracked files:
        - "no": return an empty list
        - "all": return all files in untracked directories
        - "normal": Not implemented

    Note: ignored directories will never be walked for performance reasons.
      If exclude_ignored is False, only the path to an ignored directory will
      be yielded, no files inside the directory will be returned
    """
    pass

def get_tree_changes(repo):
    """Return add/delete/modify changes to tree by comparing index to HEAD.

    Args:
      repo: repo path or object
    Returns: dict with lists for each type of change
    """
    pass

def daemon(path='.', address=None, port=None):
    """Run a daemon serving Git requests over TCP/IP.

    Args:
      path: Path to the directory to serve.
      address: Optional address to listen on (defaults to ::)
      port: Optional port to listen on (defaults to TCP_GIT_PORT)
    """
    pass

def web_daemon(path='.', address=None, port=None):
    """Run a daemon serving Git requests over HTTP.

    Args:
      path: Path to the directory to serve
      address: Optional address to listen on (defaults to ::)
      port: Optional port to listen on (defaults to 80)
    """
    pass

def upload_pack(path='.', inf=None, outf=None):
    """Upload a pack file after negotiating its contents using smart protocol.

    Args:
      path: Path to the repository
      inf: Input stream to communicate with client
      outf: Output stream to communicate with client
    """
    pass

def receive_pack(path='.', inf=None, outf=None):
    """Receive a pack file after negotiating its contents using smart protocol.

    Args:
      path: Path to the repository
      inf: Input stream to communicate with client
      outf: Output stream to communicate with client
    """
    pass

def branch_delete(repo, name):
    """Delete a branch.

    Args:
      repo: Path to the repository
      name: Name of the branch
    """
    pass

def branch_create(repo, name, objectish=None, force=False):
    """Create a branch.

    Args:
      repo: Path to the repository
      name: Name of the new branch
      objectish: Target object to point new branch at (defaults to HEAD)
      force: Force creation of branch, even if it already exists
    """
    pass

def branch_list(repo):
    """List all branches.

    Args:
      repo: Path to the repository
    """
    pass

def active_branch(repo):
    """Return the active branch in the repository, if any.

    Args:
      repo: Repository to open
    Returns:
      branch name
    Raises:
      KeyError: if the repository does not have a working tree
      IndexError: if HEAD is floating
    """
    pass

def get_branch_remote(repo):
    """Return the active branch's remote name, if any.

    Args:
      repo: Repository to open
    Returns:
      remote name
    Raises:
      KeyError: if the repository does not have a working tree
    """
    pass

def fetch(repo, remote_location=None, outstream=sys.stdout, errstream=default_bytes_err_stream, message=None, depth=None, prune=False, prune_tags=False, force=False, **kwargs):
    """Fetch objects from a remote server.

    Args:
      repo: Path to the repository
      remote_location: String identifying a remote server
      outstream: Output stream (defaults to stdout)
      errstream: Error stream (defaults to stderr)
      message: Reflog message (defaults to b"fetch: from <remote_name>")
      depth: Depth to fetch at
      prune: Prune remote removed refs
      prune_tags: Prune reomte removed tags
    Returns:
      Dictionary with refs on the remote
    """
    pass

def for_each_ref(repo: Union[Repo, str]='.', pattern: Optional[Union[str, bytes]]=None) -> List[Tuple[bytes, bytes, bytes]]:
    """Iterate over all refs that match the (optional) pattern.

    Args:
      repo: Path to the repository
      pattern: Optional glob (7) patterns to filter the refs with
    Returns:
      List of bytes tuples with: (sha, object_type, ref_name)
    """
    pass

def ls_remote(remote, config: Optional[Config]=None, **kwargs):
    """List the refs in a remote.

    Args:
      remote: Remote repository location
      config: Configuration to use
    Returns:
      Dictionary with remote refs
    """
    pass

def repack(repo):
    """Repack loose files in a repository.

    Currently this only packs loose objects.

    Args:
      repo: Path to the repository
    """
    pass

def pack_objects(repo, object_ids, packf, idxf, delta_window_size=None, deltify=None, reuse_deltas=True):
    """Pack objects into a file.

    Args:
      repo: Path to the repository
      object_ids: List of object ids to write
      packf: File-like object to write to
      idxf: File-like object to write to (can be None)
      delta_window_size: Sliding window size for searching for deltas;
                         Set to None for default window size.
      deltify: Whether to deltify objects
      reuse_deltas: Allow reuse of existing deltas while deltifying
    """
    pass

def ls_tree(repo, treeish=b'HEAD', outstream=sys.stdout, recursive=False, name_only=False):
    """List contents of a tree.

    Args:
      repo: Path to the repository
      treeish: Tree id to list
      outstream: Output stream (defaults to stdout)
      recursive: Whether to recursively list files
      name_only: Only print item name
    """
    pass

def remote_add(repo: Repo, name: Union[bytes, str], url: Union[bytes, str]):
    """Add a remote.

    Args:
      repo: Path to the repository
      name: Remote name
      url: Remote URL
    """
    pass

def remote_remove(repo: Repo, name: Union[bytes, str]):
    """Remove a remote.

    Args:
      repo: Path to the repository
      name: Remote name
    """
    pass

def check_ignore(repo, paths, no_index=False):
    """Debug gitignore files.

    Args:
      repo: Path to the repository
      paths: List of paths to check for
      no_index: Don't check index
    Returns: List of ignored files
    """
    pass

def update_head(repo, target, detached=False, new_branch=None):
    """Update HEAD to point at a new branch/commit.

    Note that this does not actually update the working tree.

    Args:
      repo: Path to the repository
      detached: Create a detached head
      target: Branch or committish to switch to
      new_branch: New branch to create
    """
    pass

def reset_file(repo, file_path: str, target: bytes=b'HEAD', symlink_fn=None):
    """Reset the file to specific commit or branch.

    Args:
      repo: dulwich Repo object
      file_path: file to reset, relative to the repository path
      target: branch or commit or b'HEAD' to reset
    """
    pass

def checkout_branch(repo, target: Union[bytes, str], force: bool=False):
    """Switch branches or restore working tree files.

    The implementation of this function will probably not scale well
    for branches with lots of local changes.
    This is due to the analysis of a diff between branches before any
    changes are applied.

    Args:
      repo: dulwich Repo object
      target: branch name or commit sha to checkout
      force: true or not to force checkout
    """
    pass

def check_mailmap(repo, contact):
    """Check canonical name and email of contact.

    Args:
      repo: Path to the repository
      contact: Contact name and/or email
    Returns: Canonical contact data
    """
    pass

def fsck(repo):
    """Check a repository.

    Args:
      repo: A path to the repository
    Returns: Iterator over errors/warnings
    """
    pass

def stash_list(repo):
    """List all stashes in a repository."""
    pass

def stash_push(repo):
    """Push a new stash onto the stack."""
    pass

def stash_pop(repo, index):
    """Pop a stash from the stack."""
    pass

def stash_drop(repo, index):
    """Drop a stash from the stack."""
    pass

def ls_files(repo):
    """List all files in an index."""
    pass

def find_unique_abbrev(object_store, object_id):
    """For now, just return 7 characters."""
    pass

def describe(repo, abbrev=7):
    """Describe the repository version.

    Args:
      repo: git repository
      abbrev: number of characters of commit to take, default is 7
    Returns: a string description of the current git revision

    Examples: "gabcdefh", "v0.1" or "v0.1-5-gabcdefh".
    """
    pass

def get_object_by_path(repo, path, committish=None):
    """Get an object by path.

    Args:
      repo: A path to the repository
      path: Path to look up
      committish: Commit to look up path in
    Returns: A `ShaFile` object
    """
    pass

def write_tree(repo):
    """Write a tree object from the index.

    Args:
      repo: Repository for which to write tree
    Returns: tree id for the tree that was written
    """
    pass