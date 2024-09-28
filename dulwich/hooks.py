"""Access to hooks."""
import os
import subprocess
from .errors import HookError

class Hook:
    """Generic hook object."""

    def execute(self, *args):
        """Execute the hook with the given args.

        Args:
          args: argument list to hook
        Raises:
          HookError: hook execution failure
        Returns:
          a hook may return a useful value
        """
        pass

class ShellHook(Hook):
    """Hook by executable file.

    Implements standard githooks(5) [0]:

    [0] http://www.kernel.org/pub/software/scm/git/docs/githooks.html
    """

    def __init__(self, name, path, numparam, pre_exec_callback=None, post_exec_callback=None, cwd=None) -> None:
        """Setup shell hook definition.

        Args:
          name: name of hook for error messages
          path: absolute path to executable file
          numparam: number of requirements parameters
          pre_exec_callback: closure for setup before execution
            Defaults to None. Takes in the variable argument list from the
            execute functions and returns a modified argument list for the
            shell hook.
          post_exec_callback: closure for cleanup after execution
            Defaults to None. Takes in a boolean for hook success and the
            modified argument list and returns the final hook return value
            if applicable
          cwd: working directory to switch to when executing the hook
        """
        self.name = name
        self.filepath = path
        self.numparam = numparam
        self.pre_exec_callback = pre_exec_callback
        self.post_exec_callback = post_exec_callback
        self.cwd = cwd

    def execute(self, *args):
        """Execute the hook with given args."""
        pass

class PreCommitShellHook(ShellHook):
    """pre-commit shell hook."""

    def __init__(self, cwd, controldir) -> None:
        filepath = os.path.join(controldir, 'hooks', 'pre-commit')
        ShellHook.__init__(self, 'pre-commit', filepath, 0, cwd=cwd)

class PostCommitShellHook(ShellHook):
    """post-commit shell hook."""

    def __init__(self, controldir) -> None:
        filepath = os.path.join(controldir, 'hooks', 'post-commit')
        ShellHook.__init__(self, 'post-commit', filepath, 0, cwd=controldir)

class CommitMsgShellHook(ShellHook):
    """commit-msg shell hook."""

    def __init__(self, controldir) -> None:
        filepath = os.path.join(controldir, 'hooks', 'commit-msg')

        def prepare_msg(*args):
            import tempfile
            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, 'wb') as f:
                f.write(args[0])
            return (path,)

        def clean_msg(success, *args):
            if success:
                with open(args[0], 'rb') as f:
                    new_msg = f.read()
                os.unlink(args[0])
                return new_msg
            os.unlink(args[0])
        ShellHook.__init__(self, 'commit-msg', filepath, 1, prepare_msg, clean_msg, controldir)

class PostReceiveShellHook(ShellHook):
    """post-receive shell hook."""

    def __init__(self, controldir) -> None:
        self.controldir = controldir
        filepath = os.path.join(controldir, 'hooks', 'post-receive')
        ShellHook.__init__(self, 'post-receive', path=filepath, numparam=0)