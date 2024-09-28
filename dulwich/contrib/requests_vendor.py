"""Requests HTTP client support for Dulwich.

To use this implementation as the HTTP implementation in Dulwich, override
the dulwich.client.HttpGitClient attribute:

  >>> from dulwich import client as _mod_client
  >>> from dulwich.contrib.requests_vendor import RequestsHttpGitClient
  >>> _mod_client.HttpGitClient = RequestsHttpGitClient

This implementation is experimental and does not have any tests.
"""
from io import BytesIO
from requests import Session
from ..client import AbstractHttpGitClient, HTTPProxyUnauthorized, HTTPUnauthorized, default_user_agent_string
from ..errors import GitProtocolError, NotGitRepository

class RequestsHttpGitClient(AbstractHttpGitClient):

    def __init__(self, base_url, dumb=None, config=None, username=None, password=None, **kwargs) -> None:
        self._username = username
        self._password = password
        self.session = get_session(config)
        if username is not None:
            self.session.auth = (username, password)
        super().__init__(base_url=base_url, dumb=dumb, **kwargs)