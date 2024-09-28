"""Support for git credential helpers.

https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage

"""
import sys
from typing import Iterator, Optional
from urllib.parse import ParseResult, urlparse
from .config import ConfigDict, SectionLike

def match_partial_url(valid_url: ParseResult, partial_url: str) -> bool:
    """Matches a parsed url with a partial url (no scheme/netloc)."""
    pass

def urlmatch_credential_sections(config: ConfigDict, url: Optional[str]) -> Iterator[SectionLike]:
    """Returns credential sections from the config which match the given URL."""
    pass