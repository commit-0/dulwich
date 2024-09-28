"""Mailmap file reader."""
from typing import Dict, Optional, Tuple

def read_mailmap(f):
    """Read a mailmap.

    Args:
      f: File-like object to read from
    Returns: Iterator over
        ((canonical_name, canonical_email), (from_name, from_email)) tuples
    """
    pass

class Mailmap:
    """Class for accessing a mailmap file."""

    def __init__(self, map=None) -> None:
        self._table: Dict[Tuple[Optional[str], str], Tuple[str, str]] = {}
        if map:
            for canonical_identity, from_identity in map:
                self.add_entry(canonical_identity, from_identity)

    def add_entry(self, canonical_identity, from_identity=None):
        """Add an entry to the mail mail.

        Any of the fields can be None, but at least one of them needs to be
        set.

        Args:
          canonical_identity: The canonical identity (tuple)
          from_identity: The from identity (tuple)
        """
        pass

    def lookup(self, identity):
        """Lookup an identity in this mailmail."""
        pass