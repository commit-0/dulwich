"""Generic functions for talking the git smart server protocol."""
from io import BytesIO
from os import SEEK_END
import dulwich
from .errors import GitProtocolError, HangupException
TCP_GIT_PORT = 9418
GIT_PROTOCOL_VERSIONS = [0, 1, 2]
DEFAULT_GIT_PROTOCOL_VERSION_FETCH = 2
DEFAULT_GIT_PROTOCOL_VERSION_SEND = 0
ZERO_SHA = b'0' * 40
SINGLE_ACK = 0
MULTI_ACK = 1
MULTI_ACK_DETAILED = 2
SIDE_BAND_CHANNEL_DATA = 1
SIDE_BAND_CHANNEL_PROGRESS = 2
SIDE_BAND_CHANNEL_FATAL = 3
CAPABILITY_ATOMIC = b'atomic'
CAPABILITY_DEEPEN_SINCE = b'deepen-since'
CAPABILITY_DEEPEN_NOT = b'deepen-not'
CAPABILITY_DEEPEN_RELATIVE = b'deepen-relative'
CAPABILITY_DELETE_REFS = b'delete-refs'
CAPABILITY_INCLUDE_TAG = b'include-tag'
CAPABILITY_MULTI_ACK = b'multi_ack'
CAPABILITY_MULTI_ACK_DETAILED = b'multi_ack_detailed'
CAPABILITY_NO_DONE = b'no-done'
CAPABILITY_NO_PROGRESS = b'no-progress'
CAPABILITY_OFS_DELTA = b'ofs-delta'
CAPABILITY_QUIET = b'quiet'
CAPABILITY_REPORT_STATUS = b'report-status'
CAPABILITY_SHALLOW = b'shallow'
CAPABILITY_SIDE_BAND = b'side-band'
CAPABILITY_SIDE_BAND_64K = b'side-band-64k'
CAPABILITY_THIN_PACK = b'thin-pack'
CAPABILITY_AGENT = b'agent'
CAPABILITY_SYMREF = b'symref'
CAPABILITY_ALLOW_TIP_SHA1_IN_WANT = b'allow-tip-sha1-in-want'
CAPABILITY_ALLOW_REACHABLE_SHA1_IN_WANT = b'allow-reachable-sha1-in-want'
CAPABILITY_FETCH = b'fetch'
CAPABILITY_FILTER = b'filter'
CAPABILITIES_REF = b'capabilities^{}'
COMMON_CAPABILITIES = [CAPABILITY_OFS_DELTA, CAPABILITY_SIDE_BAND, CAPABILITY_SIDE_BAND_64K, CAPABILITY_AGENT, CAPABILITY_NO_PROGRESS]
KNOWN_UPLOAD_CAPABILITIES = set([*COMMON_CAPABILITIES, CAPABILITY_THIN_PACK, CAPABILITY_MULTI_ACK, CAPABILITY_MULTI_ACK_DETAILED, CAPABILITY_INCLUDE_TAG, CAPABILITY_DEEPEN_SINCE, CAPABILITY_SYMREF, CAPABILITY_SHALLOW, CAPABILITY_DEEPEN_NOT, CAPABILITY_DEEPEN_RELATIVE, CAPABILITY_ALLOW_TIP_SHA1_IN_WANT, CAPABILITY_ALLOW_REACHABLE_SHA1_IN_WANT, CAPABILITY_FETCH])
KNOWN_RECEIVE_CAPABILITIES = set([*COMMON_CAPABILITIES, CAPABILITY_REPORT_STATUS, CAPABILITY_DELETE_REFS, CAPABILITY_QUIET, CAPABILITY_ATOMIC])
DEPTH_INFINITE = 2147483647
NAK_LINE = b'NAK\n'
COMMAND_DEEPEN = b'deepen'
COMMAND_SHALLOW = b'shallow'
COMMAND_UNSHALLOW = b'unshallow'
COMMAND_DONE = b'done'
COMMAND_WANT = b'want'
COMMAND_HAVE = b'have'

def pkt_line(data):
    """Wrap data in a pkt-line.

    Args:
      data: The data to wrap, as a str or None.
    Returns: The data prefixed with its length in pkt-line format; if data was
        None, returns the flush-pkt ('0000').
    """
    pass

class Protocol:
    """Class for interacting with a remote git process over the wire.

    Parts of the git wire protocol use 'pkt-lines' to communicate. A pkt-line
    consists of the length of the line as a 4-byte hex string, followed by the
    payload data. The length includes the 4-byte header. The special line
    '0000' indicates the end of a section of input and is called a 'flush-pkt'.

    For details on the pkt-line format, see the cgit distribution:
        Documentation/technical/protocol-common.txt
    """

    def __init__(self, read, write, close=None, report_activity=None) -> None:
        self.read = read
        self.write = write
        self._close = close
        self.report_activity = report_activity
        self._readahead = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_pkt_line(self):
        """Reads a pkt-line from the remote git process.

        This method may read from the readahead buffer; see unread_pkt_line.

        Returns: The next string from the stream, without the length prefix, or
            None for a flush-pkt ('0000') or delim-pkt ('0001').
        """
        pass

    def eof(self):
        """Test whether the protocol stream has reached EOF.

        Note that this refers to the actual stream EOF and not just a
        flush-pkt.

        Returns: True if the stream is at EOF, False otherwise.
        """
        pass

    def unread_pkt_line(self, data):
        """Unread a single line of data into the readahead buffer.

        This method can be used to unread a single pkt-line into a fixed
        readahead buffer.

        Args:
          data: The data to unread, without the length prefix.

        Raises:
          ValueError: If more than one pkt-line is unread.
        """
        pass

    def read_pkt_seq(self):
        """Read a sequence of pkt-lines from the remote git process.

        Returns: Yields each line of data up to but not including the next
            flush-pkt.
        """
        pass

    def write_pkt_line(self, line):
        """Sends a pkt-line to the remote git process.

        Args:
          line: A string containing the data to send, without the length
            prefix.
        """
        pass

    def write_sideband(self, channel, blob):
        """Write multiplexed data to the sideband.

        Args:
          channel: An int specifying the channel to write to.
          blob: A blob of data (as a string) to send on this channel.
        """
        pass

    def send_cmd(self, cmd, *args):
        """Send a command and some arguments to a git server.

        Only used for the TCP git protocol (git://).

        Args:
          cmd: The remote service to access.
          args: List of arguments to send to remove service.
        """
        pass

    def read_cmd(self):
        """Read a command and some arguments from the git client.

        Only used for the TCP git protocol (git://).

        Returns: A tuple of (command, [list of arguments]).
        """
        pass
_RBUFSIZE = 8192

class ReceivableProtocol(Protocol):
    """Variant of Protocol that allows reading up to a size without blocking.

    This class has a recv() method that behaves like socket.recv() in addition
    to a read() method.

    If you want to read n bytes from the wire and block until exactly n bytes
    (or EOF) are read, use read(n). If you want to read at most n bytes from
    the wire but don't care if you get less, use recv(n). Note that recv(n)
    will still block until at least one byte is read.
    """

    def __init__(self, recv, write, close=None, report_activity=None, rbufsize=_RBUFSIZE) -> None:
        super().__init__(self.read, write, close=close, report_activity=report_activity)
        self._recv = recv
        self._rbuf = BytesIO()
        self._rbufsize = rbufsize

def extract_capabilities(text):
    """Extract a capabilities list from a string, if present.

    Args:
      text: String to extract from
    Returns: Tuple with text with capabilities removed and list of capabilities
    """
    pass

def extract_want_line_capabilities(text):
    """Extract a capabilities list from a want line, if present.

    Note that want lines have capabilities separated from the rest of the line
    by a space instead of a null byte. Thus want lines have the form:

        want obj-id cap1 cap2 ...

    Args:
      text: Want line to extract from
    Returns: Tuple with text with capabilities removed and list of capabilities
    """
    pass

def ack_type(capabilities):
    """Extract the ack type from a capabilities list."""
    pass

class BufferedPktLineWriter:
    """Writer that wraps its data in pkt-lines and has an independent buffer.

    Consecutive calls to write() wrap the data in a pkt-line and then buffers
    it until enough lines have been written such that their total length
    (including length prefix) reach the buffer size.
    """

    def __init__(self, write, bufsize=65515) -> None:
        """Initialize the BufferedPktLineWriter.

        Args:
          write: A write callback for the underlying writer.
          bufsize: The internal buffer size, including length prefixes.
        """
        self._write = write
        self._bufsize = bufsize
        self._wbuf = BytesIO()
        self._buflen = 0

    def write(self, data):
        """Write data, wrapping it in a pkt-line."""
        pass

    def flush(self):
        """Flush all data from the buffer."""
        pass

class PktLineParser:
    """Packet line parser that hands completed packets off to a callback."""

    def __init__(self, handle_pkt) -> None:
        self.handle_pkt = handle_pkt
        self._readahead = BytesIO()

    def parse(self, data):
        """Parse a fragment of data and call back for any completed packets."""
        pass

    def get_tail(self):
        """Read back any unused data."""
        pass