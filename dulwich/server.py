"""Git smart network protocol server implementation.

For more detailed implementation on the network protocol, see the
Documentation/technical directory in the cgit distribution, and in particular:

* Documentation/technical/protocol-capabilities.txt
* Documentation/technical/pack-protocol.txt

Currently supported capabilities:

 * include-tag
 * thin-pack
 * multi_ack_detailed
 * multi_ack
 * side-band-64k
 * ofs-delta
 * no-progress
 * report-status
 * delete-refs
 * shallow
 * symref
"""
import collections
import os
import socket
import socketserver
import sys
import time
import zlib
from functools import partial
from typing import Dict, Iterable, List, Optional, Set, Tuple, cast
from typing import Protocol as TypingProtocol
from dulwich import log_utils
from .archive import tar_stream
from .errors import ApplyDeltaError, ChecksumMismatch, GitProtocolError, HookError, NotGitRepository, ObjectFormatException, UnexpectedCommandError
from .object_store import peel_sha
from .objects import Commit, ObjectID, valid_hexsha
from .pack import ObjectContainer, PackedObjectContainer, write_pack_from_container
from .protocol import CAPABILITIES_REF, CAPABILITY_AGENT, CAPABILITY_DELETE_REFS, CAPABILITY_INCLUDE_TAG, CAPABILITY_MULTI_ACK, CAPABILITY_MULTI_ACK_DETAILED, CAPABILITY_NO_DONE, CAPABILITY_NO_PROGRESS, CAPABILITY_OFS_DELTA, CAPABILITY_QUIET, CAPABILITY_REPORT_STATUS, CAPABILITY_SHALLOW, CAPABILITY_SIDE_BAND_64K, CAPABILITY_THIN_PACK, COMMAND_DEEPEN, COMMAND_DONE, COMMAND_HAVE, COMMAND_SHALLOW, COMMAND_UNSHALLOW, COMMAND_WANT, MULTI_ACK, MULTI_ACK_DETAILED, NAK_LINE, SIDE_BAND_CHANNEL_DATA, SIDE_BAND_CHANNEL_FATAL, SIDE_BAND_CHANNEL_PROGRESS, SINGLE_ACK, TCP_GIT_PORT, ZERO_SHA, BufferedPktLineWriter, Protocol, ReceivableProtocol, ack_type, capability_agent, extract_capabilities, extract_want_line_capabilities, format_ack_line, format_ref_line, format_shallow_line, format_unshallow_line, symref_capabilities
from .refs import PEELED_TAG_SUFFIX, RefsContainer, write_info_refs
from .repo import BaseRepo, Repo
logger = log_utils.getLogger(__name__)

class Backend:
    """A backend for the Git smart server implementation."""

    def open_repository(self, path):
        """Open the repository at a path.

        Args:
          path: Path to the repository
        Raises:
          NotGitRepository: no git repository was found at path
        Returns: Instance of BackendRepo
        """
        pass

class BackendRepo(TypingProtocol):
    """Repository abstraction used by the Git server.

    The methods required here are a subset of those provided by
    dulwich.repo.Repo.
    """
    object_store: PackedObjectContainer
    refs: RefsContainer

    def get_refs(self) -> Dict[bytes, bytes]:
        """Get all the refs in the repository.

        Returns: dict of name -> sha
        """
        pass

    def get_peeled(self, name: bytes) -> Optional[bytes]:
        """Return the cached peeled value of a ref, if available.

        Args:
          name: Name of the ref to peel
        Returns: The peeled value of the ref. If the ref is known not point to
            a tag, this will be the SHA the ref refers to. If no cached
            information about a tag is available, this method may return None,
            but it should attempt to peel the tag if possible.
        """
        pass

    def find_missing_objects(self, determine_wants, graph_walker, progress, get_tagged=None):
        """Yield the objects required for a list of commits.

        Args:
          progress: is a callback to send progress messages to the client
          get_tagged: Function that returns a dict of pointed-to sha ->
            tag sha for including tags.
        """
        pass

class DictBackend(Backend):
    """Trivial backend that looks up Git repositories in a dictionary."""

    def __init__(self, repos) -> None:
        self.repos = repos

class FileSystemBackend(Backend):
    """Simple backend looking up Git repositories in the local file system."""

    def __init__(self, root=os.sep) -> None:
        super().__init__()
        self.root = (os.path.abspath(root) + os.sep).replace(os.sep * 2, os.sep)

class Handler:
    """Smart protocol command handler base class."""

    def __init__(self, backend, proto, stateless_rpc=False) -> None:
        self.backend = backend
        self.proto = proto
        self.stateless_rpc = stateless_rpc

class PackHandler(Handler):
    """Protocol handler for packs."""

    def __init__(self, backend, proto, stateless_rpc=False) -> None:
        super().__init__(backend, proto, stateless_rpc)
        self._client_capabilities: Optional[Set[bytes]] = None
        self._done_received = False

    @classmethod
    def required_capabilities(cls) -> Iterable[bytes]:
        """Return a list of capabilities that we require the client to have."""
        pass

class UploadPackHandler(PackHandler):
    """Protocol handler for uploading a pack to the client."""

    def __init__(self, backend, args, proto, stateless_rpc=False, advertise_refs=False) -> None:
        super().__init__(backend, proto, stateless_rpc=stateless_rpc)
        self.repo = backend.open_repository(args[0])
        self._graph_walker = None
        self.advertise_refs = advertise_refs
        self._processing_have_lines = False

    def get_tagged(self, refs=None, repo=None) -> Dict[ObjectID, ObjectID]:
        """Get a dict of peeled values of tags to their original tag shas.

        Args:
          refs: dict of refname -> sha of possible tags; defaults to all
            of the backend's refs.
          repo: optional Repo instance for getting peeled refs; defaults
            to the backend's repo, if available
        Returns: dict of peeled_sha -> tag_sha, where tag_sha is the sha of a
            tag whose peeled value is peeled_sha.
        """
        pass

def _split_proto_line(line, allowed):
    """Split a line read from the wire.

    Args:
      line: The line read from the wire.
      allowed: An iterable of command names that should be allowed.
        Command names not listed below as possible return values will be
        ignored.  If None, any commands from the possible return values are
        allowed.
    Returns: a tuple having one of the following forms:
        ('want', obj_id)
        ('have', obj_id)
        ('done', None)
        (None, None)  (for a flush-pkt)

    Raises:
      UnexpectedCommandError: if the line cannot be parsed into one of the
        allowed return values.
    """
    pass

def _find_shallow(store: ObjectContainer, heads, depth):
    """Find shallow commits according to a given depth.

    Args:
      store: An ObjectStore for looking up objects.
      heads: Iterable of head SHAs to start walking from.
      depth: The depth of ancestors to include. A depth of one includes
        only the heads themselves.
    Returns: A tuple of (shallow, not_shallow), sets of SHAs that should be
        considered shallow and unshallow according to the arguments. Note that
        these sets may overlap if a commit is reachable along multiple paths.
    """
    pass

def _all_wants_satisfied(store: ObjectContainer, haves, wants):
    """Check whether all the current wants are satisfied by a set of haves.

    Args:
      store: Object store to retrieve objects from
      haves: A set of commits we know the client has.
      wants: A set of commits the client wants
    Note: Wants are specified with set_wants rather than passed in since
        in the current interface they are determined outside this class.
    """
    pass

class _ProtocolGraphWalker:
    """A graph walker that knows the git protocol.

    As a graph walker, this class implements ack(), next(), and reset(). It
    also contains some base methods for interacting with the wire and walking
    the commit tree.

    The work of determining which acks to send is passed on to the
    implementation instance stored in _impl. The reason for this is that we do
    not know at object creation time what ack level the protocol requires. A
    call to set_ack_type() is required to set up the implementation, before
    any calls to next() or ack() are made.
    """

    def __init__(self, handler, object_store: ObjectContainer, get_peeled, get_symrefs) -> None:
        self.handler = handler
        self.store: ObjectContainer = object_store
        self.get_peeled = get_peeled
        self.get_symrefs = get_symrefs
        self.proto = handler.proto
        self.stateless_rpc = handler.stateless_rpc
        self.advertise_refs = handler.advertise_refs
        self._wants: List[bytes] = []
        self.shallow: Set[bytes] = set()
        self.client_shallow: Set[bytes] = set()
        self.unshallow: Set[bytes] = set()
        self._cached = False
        self._cache: List[bytes] = []
        self._cache_index = 0
        self._impl = None

    def determine_wants(self, heads, depth=None):
        """Determine the wants for a set of heads.

        The given heads are advertised to the client, who then specifies which
        refs they want using 'want' lines. This portion of the protocol is the
        same regardless of ack type, and in fact is used to set the ack type of
        the ProtocolGraphWalker.

        If the client has the 'shallow' capability, this method also reads and
        responds to the 'shallow' and 'deepen' lines from the client. These are
        not part of the wants per se, but they set up necessary state for
        walking the graph. Additionally, later code depends on this method
        consuming everything up to the first 'have' line.

        Args:
          heads: a dict of refname->SHA1 to advertise
        Returns: a list of SHA1s requested by the client
        """
        pass
    __next__ = next

    def read_proto_line(self, allowed):
        """Read a line from the wire.

        Args:
          allowed: An iterable of command names that should be allowed.
        Returns: A tuple of (command, value); see _split_proto_line.

        Raises:
          UnexpectedCommandError: If an error occurred reading the line.
        """
        pass

    def all_wants_satisfied(self, haves):
        """Check whether all the current wants are satisfied by a set of haves.

        Args:
          haves: A set of commits we know the client has.
        Note: Wants are specified with set_wants rather than passed in since
            in the current interface they are determined outside this class.
        """
        pass
_GRAPH_WALKER_COMMANDS = (COMMAND_HAVE, COMMAND_DONE, None)

class SingleAckGraphWalkerImpl:
    """Graph walker implementation that speaks the single-ack protocol."""

    def __init__(self, walker) -> None:
        self.walker = walker
        self._common: List[bytes] = []
    __next__ = next

class MultiAckGraphWalkerImpl:
    """Graph walker implementation that speaks the multi-ack protocol."""

    def __init__(self, walker) -> None:
        self.walker = walker
        self._found_base = False
        self._common: List[bytes] = []
    __next__ = next

class MultiAckDetailedGraphWalkerImpl:
    """Graph walker implementation speaking the multi-ack-detailed protocol."""

    def __init__(self, walker) -> None:
        self.walker = walker
        self._common: List[bytes] = []
    __next__ = next

class ReceivePackHandler(PackHandler):
    """Protocol handler for downloading a pack from the client."""

    def __init__(self, backend, args, proto, stateless_rpc=False, advertise_refs=False) -> None:
        super().__init__(backend, proto, stateless_rpc=stateless_rpc)
        self.repo = backend.open_repository(args[0])
        self.advertise_refs = advertise_refs

class UploadArchiveHandler(Handler):

    def __init__(self, backend, args, proto, stateless_rpc=False) -> None:
        super().__init__(backend, proto, stateless_rpc)
        self.repo = backend.open_repository(args[0])
DEFAULT_HANDLERS = {b'git-upload-pack': UploadPackHandler, b'git-receive-pack': ReceivePackHandler, b'git-upload-archive': UploadArchiveHandler}

class TCPGitRequestHandler(socketserver.StreamRequestHandler):

    def __init__(self, handlers, *args, **kwargs) -> None:
        self.handlers = handlers
        socketserver.StreamRequestHandler.__init__(self, *args, **kwargs)

class TCPGitServer(socketserver.TCPServer):
    allow_reuse_address = True
    serve = socketserver.TCPServer.serve_forever

    def __init__(self, backend, listen_addr, port=TCP_GIT_PORT, handlers=None) -> None:
        self.handlers = dict(DEFAULT_HANDLERS)
        if handlers is not None:
            self.handlers.update(handlers)
        self.backend = backend
        logger.info('Listening for TCP connections on %s:%d', listen_addr, port)
        socketserver.TCPServer.__init__(self, (listen_addr, port), self._make_handler)

def main(argv=sys.argv):
    """Entry point for starting a TCP git server."""
    pass

def serve_command(handler_cls, argv=sys.argv, backend=None, inf=sys.stdin, outf=sys.stdout):
    """Serve a single command.

    This is mostly useful for the implementation of commands used by e.g.
    git+ssh.

    Args:
      handler_cls: `Handler` class to use for the request
      argv: execv-style command-line arguments. Defaults to sys.argv.
      backend: `Backend` to use
      inf: File-like object to read from, defaults to standard input.
      outf: File-like object to write to, defaults to standard output.
    Returns: Exit code for use with sys.exit. 0 on success, 1 on failure.
    """
    pass

def generate_info_refs(repo):
    """Generate an info refs file."""
    pass

def generate_objects_info_packs(repo):
    """Generate an index for for packs."""
    pass

def update_server_info(repo):
    """Generate server info for dumb file access.

    This generates info/refs and objects/info/packs,
    similar to "git update-server-info".
    """
    pass
if __name__ == '__main__':
    main()