"""Parsing of gitignore files.

For details for the matching rules, see https://git-scm.com/docs/gitignore
"""
import os.path
import re
from contextlib import suppress
from typing import TYPE_CHECKING, BinaryIO, Dict, Iterable, List, Optional, Union
if TYPE_CHECKING:
    from .repo import Repo
from .config import Config, get_xdg_config_home_path

def translate(pat: bytes) -> bytes:
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.

    Originally copied from fnmatch in Python 2.7, but modified for Dulwich
    to cope with features in Git ignore patterns.
    """
    pass

def read_ignore_patterns(f: BinaryIO) -> Iterable[bytes]:
    """Read a git ignore file.

    Args:
      f: File-like object to read from
    Returns: List of patterns
    """
    pass

def match_pattern(path: bytes, pattern: bytes, ignorecase: bool=False) -> bool:
    """Match a gitignore-style pattern against a path.

    Args:
      path: Path to match
      pattern: Pattern to match
      ignorecase: Whether to do case-sensitive matching
    Returns:
      bool indicating whether the pattern matched
    """
    pass

class Pattern:
    """A single ignore pattern."""

    def __init__(self, pattern: bytes, ignorecase: bool=False) -> None:
        self.pattern = pattern
        self.ignorecase = ignorecase
        if pattern[0:1] == b'!':
            self.is_exclude = False
            pattern = pattern[1:]
        else:
            if pattern[0:1] == b'\\':
                pattern = pattern[1:]
            self.is_exclude = True
        flags = 0
        if self.ignorecase:
            flags = re.IGNORECASE
        self._re = re.compile(translate(pattern), flags)

    def __bytes__(self) -> bytes:
        return self.pattern

    def __str__(self) -> str:
        return os.fsdecode(self.pattern)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.pattern == other.pattern and (self.ignorecase == other.ignorecase)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.pattern!r}, {self.ignorecase!r})'

    def match(self, path: bytes) -> bool:
        """Try to match a path against this ignore pattern.

        Args:
          path: Path to match (relative to ignore location)
        Returns: boolean
        """
        pass

class IgnoreFilter:

    def __init__(self, patterns: Iterable[bytes], ignorecase: bool=False, path=None) -> None:
        self._patterns: List[Pattern] = []
        self._ignorecase = ignorecase
        self._path = path
        for pattern in patterns:
            self.append_pattern(pattern)

    def append_pattern(self, pattern: bytes) -> None:
        """Add a pattern to the set."""
        pass

    def find_matching(self, path: Union[bytes, str]) -> Iterable[Pattern]:
        """Yield all matching patterns for path.

        Args:
          path: Path to match
        Returns:
          Iterator over iterators
        """
        pass

    def is_ignored(self, path: bytes) -> Optional[bool]:
        """Check whether a path is ignored.

        For directories, include a trailing slash.

        Returns: status is None if file is not mentioned, True if it is
            included, False if it is explicitly excluded.
        """
        pass

    def __repr__(self) -> str:
        path = getattr(self, '_path', None)
        if path is not None:
            return f'{type(self).__name__}.from_path({path!r})'
        else:
            return f'<{type(self).__name__}>'

class IgnoreFilterStack:
    """Check for ignore status in multiple filters."""

    def __init__(self, filters) -> None:
        self._filters = filters

    def is_ignored(self, path: str) -> Optional[bool]:
        """Check whether a path is explicitly included or excluded in ignores.

        Args:
          path: Path to check
        Returns:
          None if the file is not mentioned, True if it is included,
          False if it is explicitly excluded.
        """
        pass

def default_user_ignore_filter_path(config: Config) -> str:
    """Return default user ignore filter path.

    Args:
      config: A Config object
    Returns:
      Path to a global ignore file
    """
    pass

class IgnoreFilterManager:
    """Ignore file manager."""

    def __init__(self, top_path: str, global_filters: List[IgnoreFilter], ignorecase: bool) -> None:
        self._path_filters: Dict[str, Optional[IgnoreFilter]] = {}
        self._top_path = top_path
        self._global_filters = global_filters
        self._ignorecase = ignorecase

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._top_path}, {self._global_filters!r}, {self._ignorecase!r})'

    def find_matching(self, path: str) -> Iterable[Pattern]:
        """Find matching patterns for path.

        Args:
          path: Path to check
        Returns:
          Iterator over Pattern instances
        """
        pass

    def is_ignored(self, path: str) -> Optional[bool]:
        """Check whether a path is explicitly included or excluded in ignores.

        Args:
          path: Path to check
        Returns:
          None if the file is not mentioned, True if it is included,
          False if it is explicitly excluded.
        """
        pass

    @classmethod
    def from_repo(cls, repo: 'Repo') -> 'IgnoreFilterManager':
        """Create a IgnoreFilterManager from a repository.

        Args:
          repo: Repository object
        Returns:
          A `IgnoreFilterManager` object
        """
        pass