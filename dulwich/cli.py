"""Simple command-line interface to Dulwich>.

This is a very simple command-line wrapper for Dulwich. It is by
no means intended to be a full-blown Git command-line interface but just
a way to test Dulwich.
"""
import argparse
import optparse
import os
import signal
import sys
from getopt import getopt
from typing import ClassVar, Dict, Optional, Type
from dulwich import porcelain
from .client import GitProtocolError, get_transport_and_path
from .errors import ApplyDeltaError
from .index import Index
from .objectspec import parse_commit
from .pack import Pack, sha_to_hex
from .repo import Repo

class Command:
    """A Dulwich subcommand."""

    def run(self, args):
        """Run the command."""
        pass

class cmd_archive(Command):
    pass

class cmd_add(Command):
    pass

class cmd_rm(Command):
    pass

class cmd_fetch_pack(Command):
    pass

class cmd_fetch(Command):
    pass

class cmd_for_each_ref(Command):
    pass

class cmd_fsck(Command):
    pass

class cmd_log(Command):
    pass

class cmd_diff(Command):
    pass

class cmd_dump_pack(Command):
    pass

class cmd_dump_index(Command):
    pass

class cmd_init(Command):
    pass

class cmd_clone(Command):
    pass

class cmd_commit(Command):
    pass

class cmd_commit_tree(Command):
    pass

class cmd_update_server_info(Command):
    pass

class cmd_symbolic_ref(Command):
    pass

class cmd_pack_refs(Command):
    pass

class cmd_show(Command):
    pass

class cmd_diff_tree(Command):
    pass

class cmd_rev_list(Command):
    pass

class cmd_tag(Command):
    pass

class cmd_repack(Command):
    pass

class cmd_reset(Command):
    pass

class cmd_daemon(Command):
    pass

class cmd_web_daemon(Command):
    pass

class cmd_write_tree(Command):
    pass

class cmd_receive_pack(Command):
    pass

class cmd_upload_pack(Command):
    pass

class cmd_status(Command):
    pass

class cmd_ls_remote(Command):
    pass

class cmd_ls_tree(Command):
    pass

class cmd_pack_objects(Command):
    pass

class cmd_pull(Command):
    pass

class cmd_push(Command):
    pass

class cmd_remote_add(Command):
    pass

class SuperCommand(Command):
    subcommands: ClassVar[Dict[str, Type[Command]]] = {}
    default_command: ClassVar[Optional[Type[Command]]] = None

class cmd_remote(SuperCommand):
    subcommands: ClassVar[Dict[str, Type[Command]]] = {'add': cmd_remote_add}

class cmd_submodule_list(Command):
    pass

class cmd_submodule_init(Command):
    pass

class cmd_submodule(SuperCommand):
    subcommands: ClassVar[Dict[str, Type[Command]]] = {'init': cmd_submodule_init}
    default_command = cmd_submodule_init

class cmd_check_ignore(Command):
    pass

class cmd_check_mailmap(Command):
    pass

class cmd_stash_list(Command):
    pass

class cmd_stash_push(Command):
    pass

class cmd_stash_pop(Command):
    pass

class cmd_stash(SuperCommand):
    subcommands: ClassVar[Dict[str, Type[Command]]] = {'list': cmd_stash_list, 'pop': cmd_stash_pop, 'push': cmd_stash_push}

class cmd_ls_files(Command):
    pass

class cmd_describe(Command):
    pass

class cmd_help(Command):
    pass
commands = {'add': cmd_add, 'archive': cmd_archive, 'check-ignore': cmd_check_ignore, 'check-mailmap': cmd_check_mailmap, 'clone': cmd_clone, 'commit': cmd_commit, 'commit-tree': cmd_commit_tree, 'describe': cmd_describe, 'daemon': cmd_daemon, 'diff': cmd_diff, 'diff-tree': cmd_diff_tree, 'dump-pack': cmd_dump_pack, 'dump-index': cmd_dump_index, 'fetch-pack': cmd_fetch_pack, 'fetch': cmd_fetch, 'for-each-ref': cmd_for_each_ref, 'fsck': cmd_fsck, 'help': cmd_help, 'init': cmd_init, 'log': cmd_log, 'ls-files': cmd_ls_files, 'ls-remote': cmd_ls_remote, 'ls-tree': cmd_ls_tree, 'pack-objects': cmd_pack_objects, 'pack-refs': cmd_pack_refs, 'pull': cmd_pull, 'push': cmd_push, 'receive-pack': cmd_receive_pack, 'remote': cmd_remote, 'repack': cmd_repack, 'reset': cmd_reset, 'rev-list': cmd_rev_list, 'rm': cmd_rm, 'show': cmd_show, 'stash': cmd_stash, 'status': cmd_status, 'symbolic-ref': cmd_symbolic_ref, 'submodule': cmd_submodule, 'tag': cmd_tag, 'update-server-info': cmd_update_server_info, 'upload-pack': cmd_upload_pack, 'web-daemon': cmd_web_daemon, 'write-tree': cmd_write_tree}
if __name__ == '__main__':
    _main()