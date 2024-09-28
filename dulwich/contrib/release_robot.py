"""Determine last version string from tags.

Alternate to `Versioneer <https://pypi.python.org/pypi/versioneer/>`_ using
`Dulwich <https://pypi.python.org/pypi/dulwich>`_ to sort tags by time from
newest to oldest.

Copy the following into the package ``__init__.py`` module::

    from dulwich.contrib.release_robot import get_current_version
    __version__ = get_current_version()

This example assumes the tags have a leading "v" like "v0.3", and that the
``.git`` folder is in a project folder that contains the package folder.

EG::

    * project
    |
    * .git
    |
    +-* package
      |
      * __init__.py  <-- put __version__ here


"""
import datetime
import re
import sys
import time
from ..repo import Repo
PROJDIR = '.'
PATTERN = '[ a-zA-Z_\\-]*([\\d\\.]+[\\-\\w\\.]*)'

def get_recent_tags(projdir=PROJDIR):
    """Get list of tags in order from newest to oldest and their datetimes.

    Args:
      projdir: path to ``.git``
    Returns:
      list of tags sorted by commit time from newest to oldest

    Each tag in the list contains the tag name, commit time, commit id, author
    and any tag meta. If a tag isn't annotated, then its tag meta is ``None``.
    Otherwise the tag meta is a tuple containing the tag time, tag id and tag
    name. Time is in UTC.
    """
    pass

def get_current_version(projdir=PROJDIR, pattern=PATTERN, logger=None):
    """Return the most recent tag, using an options regular expression pattern.

    The default pattern will strip any characters preceding the first semantic
    version. *EG*: "Release-0.2.1-rc.1" will be come "0.2.1-rc.1". If no match
    is found, then the most recent tag is return without modification.

    Args:
      projdir: path to ``.git``
      pattern: regular expression pattern with group that matches version
      logger: a Python logging instance to capture exception
    Returns:
      tag matching first group in regular expression pattern
    """
    pass
if __name__ == '__main__':
    if len(sys.argv) > 1:
        _PROJDIR = sys.argv[1]
    else:
        _PROJDIR = PROJDIR
    print(get_current_version(projdir=_PROJDIR))