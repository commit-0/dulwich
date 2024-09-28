"""Object specification."""
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple, Union
if TYPE_CHECKING:
    from .objects import Commit, ShaFile, Tree
    from .refs import Ref, RefsContainer
    from .repo import Repo

def parse_object(repo: 'Repo', objectish: Union[bytes, str]) -> 'ShaFile':
    """Parse a string referring to an object.

    Args:
      repo: A `Repo` object
      objectish: A string referring to an object
    Returns: A git object
    Raises:
      KeyError: If the object can not be found
    """
    pass

def parse_tree(repo: 'Repo', treeish: Union[bytes, str]) -> 'Tree':
    """Parse a string referring to a tree.

    Args:
      repo: A `Repo` object
      treeish: A string referring to a tree
    Returns: A git object
    Raises:
      KeyError: If the object can not be found
    """
    pass

def parse_ref(container: Union['Repo', 'RefsContainer'], refspec: Union[str, bytes]) -> 'Ref':
    """Parse a string referring to a reference.

    Args:
      container: A RefsContainer object
      refspec: A string referring to a ref
    Returns: A ref
    Raises:
      KeyError: If the ref can not be found
    """
    pass

def parse_reftuple(lh_container: Union['Repo', 'RefsContainer'], rh_container: Union['Repo', 'RefsContainer'], refspec: Union[str, bytes], force: bool=False) -> Tuple[Optional['Ref'], Optional['Ref'], bool]:
    """Parse a reftuple spec.

    Args:
      lh_container: A RefsContainer object
      rh_container: A RefsContainer object
      refspec: A string
    Returns: A tuple with left and right ref
    Raises:
      KeyError: If one of the refs can not be found
    """
    pass

def parse_reftuples(lh_container: Union['Repo', 'RefsContainer'], rh_container: Union['Repo', 'RefsContainer'], refspecs: Union[bytes, List[bytes]], force: bool=False):
    """Parse a list of reftuple specs to a list of reftuples.

    Args:
      lh_container: A RefsContainer object
      rh_container: A RefsContainer object
      refspecs: A list of refspecs or a string
      force: Force overwriting for all reftuples
    Returns: A list of refs
    Raises:
      KeyError: If one of the refs can not be found
    """
    pass

def parse_refs(container, refspecs):
    """Parse a list of refspecs to a list of refs.

    Args:
      container: A RefsContainer object
      refspecs: A list of refspecs or a string
    Returns: A list of refs
    Raises:
      KeyError: If one of the refs can not be found
    """
    pass

def parse_commit_range(repo: 'Repo', committishs: Union[str, bytes]) -> Iterator['Commit']:
    """Parse a string referring to a range of commits.

    Args:
      repo: A `Repo` object
      committishs: A string referring to a range of commits.
    Returns: An iterator over `Commit` objects
    Raises:
      KeyError: When the reference commits can not be found
      ValueError: If the range can not be parsed
    """
    pass

class AmbiguousShortId(Exception):
    """The short id is ambiguous."""

    def __init__(self, prefix, options) -> None:
        self.prefix = prefix
        self.options = options

def scan_for_short_id(object_store, prefix):
    """Scan an object store for a short id."""
    pass

def parse_commit(repo: 'Repo', committish: Union[str, bytes]) -> 'Commit':
    """Parse a string referring to a single commit.

    Args:
      repo: A` Repo` object
      committish: A string referring to a single commit.
    Returns: A Commit object
    Raises:
      KeyError: When the reference commits can not be found
      ValueError: If the range can not be parsed
    """
    pass