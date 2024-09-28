"""Client side support for the Git protocol.

The Dulwich client supports the following capabilities:

 * thin-pack
 * multi_ack_detailed
 * multi_ack
 * side-band-64k
 * ofs-delta
 * quiet
 * report-status
 * delete-refs
 * shallow

Known capabilities that are not supported:

 * no-progress
 * include-tag
"""
import copy
import logging
import os
import select
import socket
import subprocess
import sys
from contextlib import closing
from io import BufferedReader, BytesIO
from typing import IO, TYPE_CHECKING, Callable, ClassVar, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote
from urllib.parse import urljoin, urlparse, urlunparse, urlunsplit
if TYPE_CHECKING:
    import urllib3
import dulwich
from .config import Config, apply_instead_of, get_xdg_config_home_path
from .errors import GitProtocolError, NotGitRepository, SendPackError
from .pack import PACK_SPOOL_FILE_MAX_SIZE, PackChunkGenerator, UnpackedObject, write_pack_from_container
from .protocol import _RBUFSIZE, CAPABILITIES_REF, CAPABILITY_AGENT, CAPABILITY_DELETE_REFS, CAPABILITY_FETCH, CAPABILITY_FILTER, CAPABILITY_INCLUDE_TAG, CAPABILITY_MULTI_ACK, CAPABILITY_MULTI_ACK_DETAILED, CAPABILITY_OFS_DELTA, CAPABILITY_QUIET, CAPABILITY_REPORT_STATUS, CAPABILITY_SHALLOW, CAPABILITY_SIDE_BAND_64K, CAPABILITY_SYMREF, CAPABILITY_THIN_PACK, COMMAND_DEEPEN, COMMAND_DONE, COMMAND_HAVE, COMMAND_SHALLOW, COMMAND_UNSHALLOW, COMMAND_WANT, DEFAULT_GIT_PROTOCOL_VERSION_FETCH, DEFAULT_GIT_PROTOCOL_VERSION_SEND, GIT_PROTOCOL_VERSIONS, KNOWN_RECEIVE_CAPABILITIES, KNOWN_UPLOAD_CAPABILITIES, SIDE_BAND_CHANNEL_DATA, SIDE_BAND_CHANNEL_FATAL, SIDE_BAND_CHANNEL_PROGRESS, TCP_GIT_PORT, ZERO_SHA, HangupException, PktLineParser, Protocol, agent_string, capability_agent, extract_capabilities, extract_capability_names, parse_capability, pkt_line
from .refs import PEELED_TAG_SUFFIX, _import_remote_refs, read_info_refs
from .repo import Repo
url2pathname = None
logger = logging.getLogger(__name__)

class InvalidWants(Exception):
    """Invalid wants."""

    def __init__(self, wants) -> None:
        Exception.__init__(self, f'requested wants not in server provided refs: {wants!r}')

class HTTPUnauthorized(Exception):
    """Raised when authentication fails."""

    def __init__(self, www_authenticate, url) -> None:
        Exception.__init__(self, 'No valid credentials provided')
        self.www_authenticate = www_authenticate
        self.url = url

class HTTPProxyUnauthorized(Exception):
    """Raised when proxy authentication fails."""

    def __init__(self, proxy_authenticate, url) -> None:
        Exception.__init__(self, 'No valid proxy credentials provided')
        self.proxy_authenticate = proxy_authenticate
        self.url = url

def _fileno_can_read(fileno):
    """Check if a file descriptor is readable."""
    pass

def _win32_peek_avail(handle):
    """Wrapper around PeekNamedPipe to check how many bytes are available."""
    pass
COMMON_CAPABILITIES = [CAPABILITY_OFS_DELTA, CAPABILITY_SIDE_BAND_64K]
UPLOAD_CAPABILITIES = [CAPABILITY_THIN_PACK, CAPABILITY_MULTI_ACK, CAPABILITY_MULTI_ACK_DETAILED, CAPABILITY_SHALLOW, *COMMON_CAPABILITIES]
RECEIVE_CAPABILITIES = [CAPABILITY_REPORT_STATUS, CAPABILITY_DELETE_REFS, *COMMON_CAPABILITIES]

class ReportStatusParser:
    """Handle status as reported by servers with 'report-status' capability."""

    def __init__(self) -> None:
        self._done = False
        self._pack_status = None
        self._ref_statuses: List[bytes] = []

    def check(self):
        """Check if there were any errors and, if so, raise exceptions.

        Raises:
          SendPackError: Raised when the server could not unpack
        Returns:
          iterator over refs
        """
        pass

    def handle_packet(self, pkt):
        """Handle a packet.

        Raises:
          GitProtocolError: Raised when packets are received after a flush
          packet.
        """
        pass

class FetchPackResult:
    """Result of a fetch-pack operation.

    Attributes:
      refs: Dictionary with all remote refs
      symrefs: Dictionary with remote symrefs
      agent: User agent string
    """
    _FORWARDED_ATTRS: ClassVar[Set[str]] = {'clear', 'copy', 'fromkeys', 'get', 'items', 'keys', 'pop', 'popitem', 'setdefault', 'update', 'values', 'viewitems', 'viewkeys', 'viewvalues'}

    def __init__(self, refs, symrefs, agent, new_shallow=None, new_unshallow=None) -> None:
        self.refs = refs
        self.symrefs = symrefs
        self.agent = agent
        self.new_shallow = new_shallow
        self.new_unshallow = new_unshallow

    def __eq__(self, other):
        if isinstance(other, dict):
            self._warn_deprecated()
            return self.refs == other
        return self.refs == other.refs and self.symrefs == other.symrefs and (self.agent == other.agent)

    def __contains__(self, name) -> bool:
        self._warn_deprecated()
        return name in self.refs

    def __getitem__(self, name):
        self._warn_deprecated()
        return self.refs[name]

    def __len__(self) -> int:
        self._warn_deprecated()
        return len(self.refs)

    def __iter__(self):
        self._warn_deprecated()
        return iter(self.refs)

    def __getattribute__(self, name):
        if name in type(self)._FORWARDED_ATTRS:
            self._warn_deprecated()
            return getattr(self.refs, name)
        return super().__getattribute__(name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.refs!r}, {self.symrefs!r}, {self.agent!r})'

class SendPackResult:
    """Result of a upload-pack operation.

    Attributes:
      refs: Dictionary with all remote refs
      agent: User agent string
      ref_status: Optional dictionary mapping ref name to error message (if it
        failed to update), or None if it was updated successfully
    """
    _FORWARDED_ATTRS: ClassVar[Set[str]] = {'clear', 'copy', 'fromkeys', 'get', 'items', 'keys', 'pop', 'popitem', 'setdefault', 'update', 'values', 'viewitems', 'viewkeys', 'viewvalues'}

    def __init__(self, refs, agent=None, ref_status=None) -> None:
        self.refs = refs
        self.agent = agent
        self.ref_status = ref_status

    def __eq__(self, other):
        if isinstance(other, dict):
            self._warn_deprecated()
            return self.refs == other
        return self.refs == other.refs and self.agent == other.agent

    def __contains__(self, name) -> bool:
        self._warn_deprecated()
        return name in self.refs

    def __getitem__(self, name):
        self._warn_deprecated()
        return self.refs[name]

    def __len__(self) -> int:
        self._warn_deprecated()
        return len(self.refs)

    def __iter__(self):
        self._warn_deprecated()
        return iter(self.refs)

    def __getattribute__(self, name):
        if name in type(self)._FORWARDED_ATTRS:
            self._warn_deprecated()
            return getattr(self.refs, name)
        return super().__getattribute__(name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.refs!r}, {self.agent!r})'

class _v1ReceivePackHeader:

    def __init__(self, capabilities, old_refs, new_refs) -> None:
        self.want: List[bytes] = []
        self.have: List[bytes] = []
        self._it = self._handle_receive_pack_head(capabilities, old_refs, new_refs)
        self.sent_capabilities = False

    def __iter__(self):
        return self._it

    def _handle_receive_pack_head(self, capabilities, old_refs, new_refs):
        """Handle the head of a 'git-receive-pack' request.

        Args:
          capabilities: List of negotiated capabilities
          old_refs: Old refs, as received from the server
          new_refs: Refs to change

        Returns:
          (have, want) tuple
        """
        pass

def _read_side_band64k_data(pkt_seq: Iterable[bytes]) -> Iterator[Tuple[int, bytes]]:
    """Read per-channel data.

    This requires the side-band-64k capability.

    Args:
      pkt_seq: Sequence of packets to read
    """
    pass

def _handle_upload_pack_head(proto, capabilities, graph_walker, wants, can_read, depth, protocol_version):
    """Handle the head of a 'git-upload-pack' request.

    Args:
      proto: Protocol object to read from
      capabilities: List of negotiated capabilities
      graph_walker: GraphWalker instance to call .ack() on
      wants: List of commits to fetch
      can_read: function that returns a boolean that indicates
    whether there is extra graph data to read on proto
      depth: Depth for request
      protocol_version: Neogiated Git protocol version.
    """
    pass

def _handle_upload_pack_tail(proto, capabilities: Set[bytes], graph_walker, pack_data: Callable[[bytes], None], progress: Optional[Callable[[bytes], None]]=None, rbufsize=_RBUFSIZE, protocol_version=0):
    """Handle the tail of a 'git-upload-pack' request.

    Args:
      proto: Protocol object to read from
      capabilities: List of negotiated capabilities
      graph_walker: GraphWalker instance to call .ack() on
      pack_data: Function to call with pack data
      progress: Optional progress reporting function
      rbufsize: Read buffer size
      protocol_version: Neogiated Git protocol version.
    """
    pass

class GitClient:
    """Git smart server client."""

    def __init__(self, thin_packs=True, report_activity=None, quiet=False, include_tags=False, **kwargs) -> None:
        """Create a new GitClient instance.

        Args:
          thin_packs: Whether or not thin packs should be retrieved
          report_activity: Optional callback for reporting transport
            activity.
          include_tags: send annotated tags when sending the objects they point
            to
        """
        self._report_activity = report_activity
        self._report_status_parser: Optional[ReportStatusParser] = None
        self._fetch_capabilities = set(UPLOAD_CAPABILITIES)
        self._fetch_capabilities.add(capability_agent())
        self._send_capabilities = set(RECEIVE_CAPABILITIES)
        self._send_capabilities.add(capability_agent())
        if quiet:
            self._send_capabilities.add(CAPABILITY_QUIET)
        if not thin_packs:
            self._fetch_capabilities.remove(CAPABILITY_THIN_PACK)
        if include_tags:
            self._fetch_capabilities.add(CAPABILITY_INCLUDE_TAG)
        self.protocol_version = 0

    def get_url(self, path):
        """Retrieves full url to given path.

        Args:
          path: Repository path (as string)

        Returns:
          Url to path (as string)

        """
        pass

    @classmethod
    def from_parsedurl(cls, parsedurl, **kwargs):
        """Create an instance of this client from a urlparse.parsed object.

        Args:
          parsedurl: Result of urlparse()

        Returns:
          A `GitClient` object
        """
        pass

    def send_pack(self, path, update_refs, generate_pack_data: Callable[[Set[bytes], Set[bytes], bool], Tuple[int, Iterator[UnpackedObject]]], progress=None):
        """Upload a pack to a remote repository.

        Args:
          path: Repository path (as bytestring)
          update_refs: Function to determine changes to remote refs. Receive
            dict with existing remote refs, returns dict with
            changed refs (name -> sha, where sha=ZERO_SHA for deletions)
          generate_pack_data: Function that can return a tuple
            with number of objects and list of pack data to include
          progress: Optional progress function

        Returns:
          SendPackResult object

        Raises:
          SendPackError: if server rejects the pack data

        """
        pass

    def clone(self, path, target_path, mkdir: bool=True, bare: bool=False, origin: Optional[str]='origin', checkout=None, branch=None, progress=None, depth=None, ref_prefix=[], filter_spec=None, protocol_version: Optional[int]=None) -> Repo:
        """Clone a repository."""
        pass

    def fetch(self, path: str, target: Repo, determine_wants: Optional[Callable[[Dict[bytes, bytes], Optional[int]], List[bytes]]]=None, progress: Optional[Callable[[bytes], None]]=None, depth: Optional[int]=None, ref_prefix: Optional[List[bytes]]=[], filter_spec: Optional[bytes]=None, protocol_version: Optional[int]=None) -> FetchPackResult:
        """Fetch into a target repository.

        Args:
          path: Path to fetch from (as bytestring)
          target: Target repository to fetch into
          determine_wants: Optional function to determine what refs to fetch.
            Receives dictionary of name->sha, should return
            list of shas to fetch. Defaults to all shas.
          progress: Optional progress function
          depth: Depth to fetch at
          ref_prefix: Prefix of desired references, as a list of bytestrings.
            The server will limit the list of references sent to this prefix,
            provided this feature is supported and sufficient server-side
            resources are available to match all references against the prefix.
            Clients must be prepared to filter out any non-requested references
            themselves. This feature is an entirely optional optimization.
          filter_spec: A git-rev-list-style object filter spec, as bytestring.
            Only used if the server supports the Git protocol-v2 'filter'
            feature, and ignored otherwise.
          protocol_version: Desired Git protocol version. By default the highest
            mutually supported protocol version will be used.

        Returns:
          Dictionary with all remote refs (not just those fetched)

        """
        pass

    def fetch_pack(self, path: str, determine_wants, graph_walker, pack_data, *, progress: Optional[Callable[[bytes], None]]=None, depth: Optional[int]=None, ref_prefix=[], filter_spec=None, protocol_version: Optional[int]=None):
        """Retrieve a pack from a git smart server.

        Args:
          path: Remote path to fetch from
          determine_wants: Function determine what refs
            to fetch. Receives dictionary of name->sha, should return
            list of shas to fetch.
          graph_walker: Object with next() and ack().
          pack_data: Callback called for each bit of data in the pack
          progress: Callback for progress reports (strings)
          depth: Shallow fetch depth
          ref_prefix: Prefix of desired references, as a list of bytestrings.
            The server will limit the list of references sent to this prefix,
            provided this feature is supported and sufficient server-side
            resources are available to match all references against the prefix.
            Clients must be prepared to filter out any non-requested references
            themselves. This feature is an entirely optional optimization.
          filter_spec: A git-rev-list-style object filter spec, as bytestring.
            Only used if the server supports the Git protocol-v2 'filter'
            feature, and ignored otherwise.
          protocol_version: Desired Git protocol version. By default the highest
            mutually supported protocol version will be used.

        Returns:
          FetchPackResult object

        """
        pass

    def get_refs(self, path):
        """Retrieve the current refs from a git smart server.

        Args:
          path: Path to the repo to fetch from. (as bytestring)
        """
        pass

    def _handle_receive_pack_tail(self, proto: Protocol, capabilities: Set[bytes], progress: Optional[Callable[[bytes], None]]=None) -> Optional[Dict[bytes, Optional[str]]]:
        """Handle the tail of a 'git-receive-pack' request.

        Args:
          proto: Protocol object to read from
          capabilities: List of negotiated capabilities
          progress: Optional progress reporting function

        Returns:
          dict mapping ref name to:
            error message if the ref failed to update
            None if it was updated successfully
        """
        pass

    def archive(self, path, committish, write_data, progress=None, write_error=None, format=None, subdirs=None, prefix=None):
        """Retrieve an archive of the specified tree."""
        pass

def check_wants(wants, refs):
    """Check that a set of wants is valid.

    Args:
      wants: Set of object SHAs to fetch
      refs: Refs dictionary to check against
    """
    pass

class TraditionalGitClient(GitClient):
    """Traditional Git client."""
    DEFAULT_ENCODING = 'utf-8'

    def __init__(self, path_encoding=DEFAULT_ENCODING, **kwargs) -> None:
        self._remote_path_encoding = path_encoding
        super().__init__(**kwargs)

    async def _connect(self, cmd, path, protocol_version=None):
        """Create a connection to the server.

        This method is abstract - concrete implementations should
        implement their own variant which connects to the server and
        returns an initialized Protocol object with the service ready
        for use and a can_read function which may be used to see if
        reads would block.

        Args:
          cmd: The git service name to which we should connect.
          path: The path we should pass to the service. (as bytestirng)
          protocol_version: Desired Git protocol version. By default the highest
            mutually supported protocol version will be used.
        """
        pass

    def send_pack(self, path, update_refs, generate_pack_data, progress=None):
        """Upload a pack to a remote repository.

        Args:
          path: Repository path (as bytestring)
          update_refs: Function to determine changes to remote refs.
            Receive dict with existing remote refs, returns dict with
            changed refs (name -> sha, where sha=ZERO_SHA for deletions)
          generate_pack_data: Function that can return a tuple with
            number of objects and pack data to upload.
          progress: Optional callback called with progress updates

        Returns:
          SendPackResult

        Raises:
          SendPackError: if server rejects the pack data

        """
        pass

    def fetch_pack(self, path, determine_wants, graph_walker, pack_data, progress=None, depth=None, ref_prefix=[], filter_spec=None, protocol_version: Optional[int]=None):
        """Retrieve a pack from a git smart server.

        Args:
          path: Remote path to fetch from
          determine_wants: Function determine what refs
            to fetch. Receives dictionary of name->sha, should return
            list of shas to fetch.
          graph_walker: Object with next() and ack().
          pack_data: Callback called for each bit of data in the pack
          progress: Callback for progress reports (strings)
          depth: Shallow fetch depth
          ref_prefix: Prefix of desired references, as a list of bytestrings.
            The server will limit the list of references sent to this prefix,
            provided this feature is supported and sufficient server-side
            resources are available to match all references against the prefix.
            Clients must be prepared to filter out any non-requested references
            themselves. This feature is an entirely optional optimization.
          filter_spec: A git-rev-list-style object filter spec, as bytestring.
            Only used if the server supports the Git protocol-v2 'filter'
            feature, and ignored otherwise.
          protocol_version: Desired Git protocol version. By default the highest
            mutually supported protocol version will be used.

        Returns:
          FetchPackResult object

        """
        pass

    def get_refs(self, path, protocol_version=None):
        """Retrieve the current refs from a git smart server."""
        pass

class TCPGitClient(TraditionalGitClient):
    """A Git Client that works over TCP directly (i.e. git://)."""

    def __init__(self, host, port=None, **kwargs) -> None:
        if port is None:
            port = TCP_GIT_PORT
        self._host = host
        self._port = port
        super().__init__(**kwargs)

class SubprocessWrapper:
    """A socket-like object that talks to a subprocess via pipes."""

    def __init__(self, proc) -> None:
        self.proc = proc
        self.read = BufferedReader(proc.stdout).read
        self.write = proc.stdin.write

def find_git_command() -> List[str]:
    """Find command to run for system Git (usually C Git)."""
    pass

class SubprocessGitClient(TraditionalGitClient):
    """Git client that talks to a server using a subprocess."""
    git_command = None

class LocalGitClient(GitClient):
    """Git Client that just uses a local on-disk repository."""

    def __init__(self, thin_packs: bool=True, report_activity=None, config: Optional[Config]=None) -> None:
        """Create a new LocalGitClient instance.

        Args:
          thin_packs: Whether or not thin packs should be retrieved
          report_activity: Optional callback for reporting transport
            activity.
        """
        self._report_activity = report_activity

    def send_pack(self, path, update_refs, generate_pack_data, progress=None):
        """Upload a pack to a local on-disk repository.

        Args:
          path: Repository path (as bytestring)
          update_refs: Function to determine changes to remote refs.
            Receive dict with existing remote refs, returns dict with
            changed refs (name -> sha, where sha=ZERO_SHA for deletions)
            with number of items and pack data to upload.
          progress: Optional progress function

        Returns:
          SendPackResult

        Raises:
          SendPackError: if server rejects the pack data

        """
        pass

    def fetch(self, path, target, determine_wants=None, progress=None, depth=None, ref_prefix=[], filter_spec=None, **kwargs):
        """Fetch into a target repository.

        Args:
          path: Path to fetch from (as bytestring)
          target: Target repository to fetch into
          determine_wants: Optional function determine what refs
            to fetch. Receives dictionary of name->sha, should return
            list of shas to fetch. Defaults to all shas.
          progress: Optional progress function
          depth: Shallow fetch depth
          ref_prefix: Prefix of desired references, as a list of bytestrings.
            The server will limit the list of references sent to this prefix,
            provided this feature is supported and sufficient server-side
            resources are available to match all references against the prefix.
            Clients must be prepared to filter out any non-requested references
            themselves. This feature is an entirely optional optimization.
          filter_spec: A git-rev-list-style object filter spec, as bytestring.
            Only used if the server supports the Git protocol-v2 'filter'
            feature, and ignored otherwise.

        Returns:
          FetchPackResult object

        """
        pass

    def fetch_pack(self, path, determine_wants, graph_walker, pack_data, progress=None, depth=None, ref_prefix: Optional[List[bytes]]=[], filter_spec: Optional[bytes]=None, protocol_version: Optional[int]=None) -> FetchPackResult:
        """Retrieve a pack from a local on-disk repository.

        Args:
          path: Remote path to fetch from
          determine_wants: Function determine what refs
            to fetch. Receives dictionary of name->sha, should return
            list of shas to fetch.
          graph_walker: Object with next() and ack().
          pack_data: Callback called for each bit of data in the pack
          progress: Callback for progress reports (strings)
          depth: Shallow fetch depth
          ref_prefix: Prefix of desired references, as a list of bytestrings.
            The server will limit the list of references sent to this prefix,
            provided this feature is supported and sufficient server-side
            resources are available to match all references against the prefix.
            Clients must be prepared to filter out any non-requested references
            themselves. This feature is an entirely optional optimization.
          filter_spec: A git-rev-list-style object filter spec, as bytestring.
            Only used if the server supports the Git protocol-v2 'filter'
            feature, and ignored otherwise.

        Returns:
          FetchPackResult object

        """
        pass

    def get_refs(self, path):
        """Retrieve the current refs from a local on-disk repository."""
        pass
default_local_git_client_cls = LocalGitClient

class SSHVendor:
    """A client side SSH implementation."""

    def run_command(self, host, command, username=None, port=None, password=None, key_filename=None, ssh_command=None, protocol_version: Optional[int]=None):
        """Connect to an SSH server.

        Run a command remotely and return a file-like object for interaction
        with the remote command.

        Args:
          host: Host name
          command: Command to run (as argv array)
          username: Optional ame of user to log in as
          port: Optional SSH port to use
          password: Optional ssh password for login or private key
          key_filename: Optional path to private keyfile
          ssh_command: Optional SSH command
          protocol_version: Desired Git protocol version. By default the highest
            mutually supported protocol version will be used.
        """
        pass

class StrangeHostname(Exception):
    """Refusing to connect to strange SSH hostname."""

    def __init__(self, hostname) -> None:
        super().__init__(hostname)

class SubprocessSSHVendor(SSHVendor):
    """SSH vendor that shells out to the local 'ssh' command."""

class PLinkSSHVendor(SSHVendor):
    """SSH vendor that shells out to the local 'plink' command."""
get_ssh_vendor = SubprocessSSHVendor

class SSHGitClient(TraditionalGitClient):

    def __init__(self, host, port=None, username=None, vendor=None, config=None, password=None, key_filename=None, ssh_command=None, **kwargs) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.ssh_command = ssh_command or os.environ.get('GIT_SSH_COMMAND', os.environ.get('GIT_SSH'))
        super().__init__(**kwargs)
        self.alternative_paths: Dict[bytes, bytes] = {}
        if vendor is not None:
            self.ssh_vendor = vendor
        else:
            self.ssh_vendor = get_ssh_vendor()

def default_urllib3_manager(config, pool_manager_cls=None, proxy_manager_cls=None, base_url=None, **override_kwargs) -> Union['urllib3.ProxyManager', 'urllib3.PoolManager']:
    """Return urllib3 connection pool manager.

    Honour detected proxy configurations.

    Args:
      config: `dulwich.config.ConfigDict` instance with Git configuration.
      override_kwargs: Additional arguments for `urllib3.ProxyManager`

    Returns:
      Either pool_manager_cls (defaults to `urllib3.ProxyManager`) instance for
      proxy configurations, proxy_manager_cls
      (defaults to `urllib3.PoolManager`) instance otherwise

    """
    pass

class AbstractHttpGitClient(GitClient):
    """Abstract base class for HTTP Git Clients.

    This is agonistic of the actual HTTP implementation.

    Subclasses should provide an implementation of the
    _http_request method.
    """

    def __init__(self, base_url, dumb=False, **kwargs) -> None:
        self._base_url = base_url.rstrip('/') + '/'
        self.dumb = dumb
        GitClient.__init__(self, **kwargs)

    def _http_request(self, url, headers=None, data=None):
        """Perform HTTP request.

        Args:
          url: Request URL.
          headers: Optional custom headers to override defaults.
          data: Request data.

        Returns:
          Tuple (response, read), where response is an urllib3
          response object with additional content_type and
          redirect_location properties, and read is a consumable read
          method for the response data.

        Raises:
          GitProtocolError
        """
        pass

    def _smart_request(self, service, url, data):
        """Send a 'smart' HTTP request.

        This is a simple wrapper around _http_request that sets
        a couple of extra headers.
        """
        pass

    def send_pack(self, path, update_refs, generate_pack_data, progress=None):
        """Upload a pack to a remote repository.

        Args:
          path: Repository path (as bytestring)
          update_refs: Function to determine changes to remote refs.
            Receives dict with existing remote refs, returns dict with
            changed refs (name -> sha, where sha=ZERO_SHA for deletions)
          generate_pack_data: Function that can return a tuple
            with number of elements and pack data to upload.
          progress: Optional progress function

        Returns:
          SendPackResult

        Raises:
          SendPackError: if server rejects the pack data

        """
        pass

    def fetch_pack(self, path, determine_wants, graph_walker, pack_data, progress=None, depth=None, ref_prefix=[], filter_spec=None, protocol_version: Optional[int]=None):
        """Retrieve a pack from a git smart server.

        Args:
          path: Path to fetch from
          determine_wants: Callback that returns list of commits to fetch
          graph_walker: Object with next() and ack().
          pack_data: Callback called for each bit of data in the pack
          progress: Callback for progress reports (strings)
          depth: Depth for request
          ref_prefix: Prefix of desired references, as a list of bytestrings.
            The server will limit the list of references sent to this prefix,
            provided this feature is supported and sufficient server-side
            resources are available to match all references against the prefix.
            Clients must be prepared to filter out any non-requested references
            themselves. This feature is an entirely optional optimization.
          filter_spec: A git-rev-list-style object filter spec, as bytestring.
            Only used if the server supports the Git protocol-v2 'filter'
            feature, and ignored otherwise.
          protocol_version: Desired Git protocol version. By default the highest
            mutually supported protocol version will be used.

        Returns:
          FetchPackResult object

        """
        pass

    def get_refs(self, path):
        """Retrieve the current refs from a git smart server."""
        pass

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._base_url!r}, dumb={self.dumb!r})'

class Urllib3HttpGitClient(AbstractHttpGitClient):

    def __init__(self, base_url, dumb=None, pool_manager=None, config=None, username=None, password=None, **kwargs) -> None:
        self._username = username
        self._password = password
        if pool_manager is None:
            self.pool_manager = default_urllib3_manager(config, base_url=base_url)
        else:
            self.pool_manager = pool_manager
        if username is not None:
            credentials = f'{username}:{password or ''}'
            import urllib3.util
            basic_auth = urllib3.util.make_headers(basic_auth=credentials)
            self.pool_manager.headers.update(basic_auth)
        self.config = config
        super().__init__(base_url=base_url, dumb=dumb, **kwargs)
HttpGitClient = Urllib3HttpGitClient

def _win32_url_to_path(parsed) -> str:
    """Convert a file: URL to a path.

    https://datatracker.ietf.org/doc/html/rfc8089
    """
    pass

def get_transport_and_path_from_url(url: str, config: Optional[Config]=None, operation: Optional[str]=None, **kwargs) -> Tuple[GitClient, str]:
    """Obtain a git client from a URL.

    Args:
      url: URL to open (a unicode string)
      config: Optional config object
      operation: Kind of operation that'll be performed; "pull" or "push"
      thin_packs: Whether or not thin packs should be retrieved
      report_activity: Optional callback for reporting transport
        activity.

    Returns:
      Tuple with client instance and relative path.

    """
    pass

def parse_rsync_url(location: str) -> Tuple[Optional[str], str, str]:
    """Parse a rsync-style URL."""
    pass

def get_transport_and_path(location: str, config: Optional[Config]=None, operation: Optional[str]=None, **kwargs) -> Tuple[GitClient, str]:
    """Obtain a git client from a URL.

    Args:
      location: URL or path (a string)
      config: Optional config object
      operation: Kind of operation that'll be performed; "pull" or "push"
      thin_packs: Whether or not thin packs should be retrieved
      report_activity: Optional callback for reporting transport
        activity.

    Returns:
      Tuple with client instance and relative path.

    """
    pass
DEFAULT_GIT_CREDENTIALS_PATHS = [os.path.expanduser('~/.git-credentials'), get_xdg_config_home_path('git', 'credentials')]