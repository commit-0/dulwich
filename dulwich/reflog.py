"""Utilities for reading and generating reflogs."""
import collections
from .objects import ZERO_SHA, format_timezone, parse_timezone
Entry = collections.namedtuple('Entry', ['old_sha', 'new_sha', 'committer', 'timestamp', 'timezone', 'message'])

def format_reflog_line(old_sha, new_sha, committer, timestamp, timezone, message):
    """Generate a single reflog line.

    Args:
      old_sha: Old Commit SHA
      new_sha: New Commit SHA
      committer: Committer name and e-mail
      timestamp: Timestamp
      timezone: Timezone
      message: Message
    """
    pass

def parse_reflog_line(line):
    """Parse a reflog line.

    Args:
      line: Line to parse
    Returns: Tuple of (old_sha, new_sha, committer, timestamp, timezone,
        message)
    """
    pass

def read_reflog(f):
    """Read reflog.

    Args:
      f: File-like object
    Returns: Iterator over Entry objects
    """
    pass

def drop_reflog_entry(f, index, rewrite=False):
    """Drop the specified reflog entry.

    Args:
        f: File-like object
        index: Reflog entry index (in Git reflog reverse 0-indexed order)
        rewrite: If a reflog entry's predecessor is removed, set its
            old SHA to the new SHA of the entry that now precedes it
    """
    pass