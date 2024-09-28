"""Paramiko SSH support for Dulwich.

To use this implementation as the SSH implementation in Dulwich, override
the dulwich.client.get_ssh_vendor attribute:

  >>> from dulwich import client as _mod_client
  >>> from dulwich.contrib.paramiko_vendor import ParamikoSSHVendor
  >>> _mod_client.get_ssh_vendor = ParamikoSSHVendor

This implementation is experimental and does not have any tests.
"""
import paramiko
import paramiko.client

class _ParamikoWrapper:

    def __init__(self, client, channel) -> None:
        self.client = client
        self.channel = channel
        self.channel.setblocking(True)

class ParamikoSSHVendor:

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs