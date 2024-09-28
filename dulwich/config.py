"""Reading and writing Git configuration files.

Todo:
 * preserve formatting when updating configuration files
 * treat subsection names as case-insensitive for [branch.foo] style
   subsections
"""
import os
import sys
from contextlib import suppress
from typing import Any, BinaryIO, Dict, Iterable, Iterator, KeysView, List, MutableMapping, Optional, Tuple, Union, overload
from .file import GitFile
SENTINEL = object()

class CaseInsensitiveOrderedMultiDict(MutableMapping):

    def __init__(self) -> None:
        self._real: List[Any] = []
        self._keyed: Dict[Any, Any] = {}

    def __len__(self) -> int:
        return len(self._keyed)

    def __iter__(self):
        return self._keyed.__iter__()

    def __setitem__(self, key, value) -> None:
        self._real.append((key, value))
        self._keyed[lower_key(key)] = value

    def __delitem__(self, key) -> None:
        key = lower_key(key)
        del self._keyed[key]
        for i, (actual, unused_value) in reversed(list(enumerate(self._real))):
            if lower_key(actual) == key:
                del self._real[i]

    def __getitem__(self, item):
        return self._keyed[lower_key(item)]
Name = bytes
NameLike = Union[bytes, str]
Section = Tuple[bytes, ...]
SectionLike = Union[bytes, str, Tuple[Union[bytes, str], ...]]
Value = bytes
ValueLike = Union[bytes, str]

class Config:
    """A Git configuration."""

    def get(self, section: SectionLike, name: NameLike) -> Value:
        """Retrieve the contents of a configuration setting.

        Args:
          section: Tuple with section name and optional subsection name
          name: Variable name
        Returns:
          Contents of the setting
        Raises:
          KeyError: if the value is not set
        """
        pass

    def get_multivar(self, section: SectionLike, name: NameLike) -> Iterator[Value]:
        """Retrieve the contents of a multivar configuration setting.

        Args:
          section: Tuple with section name and optional subsection namee
          name: Variable name
        Returns:
          Contents of the setting as iterable
        Raises:
          KeyError: if the value is not set
        """
        pass

    def get_boolean(self, section: SectionLike, name: NameLike, default: Optional[bool]=None) -> Optional[bool]:
        """Retrieve a configuration setting as boolean.

        Args:
          section: Tuple with section name and optional subsection name
          name: Name of the setting, including section and possible
            subsection.

        Returns:
          Contents of the setting
        """
        pass

    def set(self, section: SectionLike, name: NameLike, value: Union[ValueLike, bool]) -> None:
        """Set a configuration value.

        Args:
          section: Tuple with section name and optional subsection namee
          name: Name of the configuration value, including section
            and optional subsection
          value: value of the setting
        """
        pass

    def items(self, section: SectionLike) -> Iterator[Tuple[Name, Value]]:
        """Iterate over the configuration pairs for a specific section.

        Args:
          section: Tuple with section name and optional subsection namee
        Returns:
          Iterator over (name, value) pairs
        """
        pass

    def sections(self) -> Iterator[Section]:
        """Iterate over the sections.

        Returns: Iterator over section tuples
        """
        pass

    def has_section(self, name: Section) -> bool:
        """Check if a specified section exists.

        Args:
          name: Name of section to check for
        Returns:
          boolean indicating whether the section exists
        """
        pass

class ConfigDict(Config, MutableMapping[Section, MutableMapping[Name, Value]]):
    """Git configuration stored in a dictionary."""

    def __init__(self, values: Union[MutableMapping[Section, MutableMapping[Name, Value]], None]=None, encoding: Union[str, None]=None) -> None:
        """Create a new ConfigDict."""
        if encoding is None:
            encoding = sys.getdefaultencoding()
        self.encoding = encoding
        self._values = CaseInsensitiveOrderedMultiDict.make(values)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._values!r})'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other._values == self._values

    def __getitem__(self, key: Section) -> MutableMapping[Name, Value]:
        return self._values.__getitem__(key)

    def __setitem__(self, key: Section, value: MutableMapping[Name, Value]) -> None:
        return self._values.__setitem__(key, value)

    def __delitem__(self, key: Section) -> None:
        return self._values.__delitem__(key)

    def __iter__(self) -> Iterator[Section]:
        return self._values.__iter__()

    def __len__(self) -> int:
        return self._values.__len__()
_ESCAPE_TABLE = {ord(b'\\'): ord(b'\\'), ord(b'"'): ord(b'"'), ord(b'n'): ord(b'\n'), ord(b't'): ord(b'\t'), ord(b'b'): ord(b'\x08')}
_COMMENT_CHARS = [ord(b'#'), ord(b';')]
_WHITESPACE_CHARS = [ord(b'\t'), ord(b' ')]

def _escape_value(value: bytes) -> bytes:
    """Escape a value."""
    pass

class ConfigFile(ConfigDict):
    """A Git configuration file, like .git/config or ~/.gitconfig."""

    def __init__(self, values: Union[MutableMapping[Section, MutableMapping[Name, Value]], None]=None, encoding: Union[str, None]=None) -> None:
        super().__init__(values=values, encoding=encoding)
        self.path: Optional[str] = None

    @classmethod
    def from_file(cls, f: BinaryIO) -> 'ConfigFile':
        """Read configuration from a file-like object."""
        pass

    @classmethod
    def from_path(cls, path: str) -> 'ConfigFile':
        """Read configuration from a file on disk."""
        pass

    def write_to_path(self, path: Optional[str]=None) -> None:
        """Write configuration to a file on disk."""
        pass

    def write_to_file(self, f: BinaryIO) -> None:
        """Write configuration to a file-like object."""
        pass

class StackedConfig(Config):
    """Configuration which reads from multiple config files.."""

    def __init__(self, backends: List[ConfigFile], writable: Optional[ConfigFile]=None) -> None:
        self.backends = backends
        self.writable = writable

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} for {self.backends!r}>'

    @classmethod
    def default_backends(cls) -> List[ConfigFile]:
        """Retrieve the default configuration.

        See git-config(1) for details on the files searched.
        """
        pass

def read_submodules(path: str) -> Iterator[Tuple[bytes, bytes, bytes]]:
    """Read a .gitmodules file."""
    pass

def parse_submodules(config: ConfigFile) -> Iterator[Tuple[bytes, bytes, bytes]]:
    """Parse a gitmodules GitConfig file, returning submodules.

    Args:
      config: A `ConfigFile`
    Returns:
      list of tuples (submodule path, url, name),
        where name is quoted part of the section's name.
    """
    pass

def iter_instead_of(config: Config, push: bool=False) -> Iterable[Tuple[str, str]]:
    """Iterate over insteadOf / pushInsteadOf values."""
    pass

def apply_instead_of(config: Config, orig_url: str, push: bool=False) -> str:
    """Apply insteadOf / pushInsteadOf to a URL."""
    pass