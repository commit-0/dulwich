import re
import sys
from typing import List, Optional, Tuple
_git_header_name = re.compile(b'diff --git a/(.*) b/(.*)')
_GIT_HEADER_START = b'diff --git a/'
_GIT_BINARY_START = b'Binary file'
_GIT_RENAMEFROM_START = b'rename from'
_GIT_RENAMETO_START = b'rename to'
_GIT_CHUNK_START = b'@@'
_GIT_ADDED_START = b'+'
_GIT_DELETED_START = b'-'
_GIT_UNCHANGED_START = b' '

def _parse_patch(lines: List[bytes]) -> Tuple[List[bytes], List[bool], List[Tuple[int, int]]]:
    """Parse a git style diff or patch to generate diff stats.

    Args:
      lines: list of byte string lines from the diff to be parsed
    Returns: A tuple (names, is_binary, counts) of three lists
    """
    pass

def diffstat(lines, max_width=80):
    """Generate summary statistics from a git style diff ala
       (git diff tag1 tag2 --stat).

    Args:
      lines: list of byte string "lines" from the diff to be parsed
      max_width: maximum line length for generating the summary
                 statistics (default 80)
    Returns: A byte string that lists the changed files with change
             counts and histogram.
    """
    pass
if __name__ == '__main__':
    sys.exit(main())