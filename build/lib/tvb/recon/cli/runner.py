
"""
Simple CLI runner.

- serial execution in cwd
- little path management
- small API, replaceable by other job engine

"""

import os
import time
import subprocess
import tempfile
import enum
import abc
from typing import Sequence
from .. import logger
from . import core


class File(os.PathLike):
    """
    File captures a CLI arg which should be a file.

    """

    def __init__(self, path: str):
        self.path = path

    @property
    def exists(self):
        return os.path.exists(self.path)

    def __fspath__(self):
        return self.path


class Runner(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def tmp_fname(self, fname: str): pass

    @abc.abstractmethod
    def fname(self, fname: str): pass

    @abc.abstractmethod
    def run(self, args): pass


class SimpleRunner(Runner):

    def __init__(self):
        self.logger = logger.get_logger(self.__class__.__name__)
        self._which_cache = {}
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tmp_fname(self, fname) -> File:
        return File(os.path.join(self.tmp_dir.name, fname))

    def fname(self, fname) -> File:
        return File(fname)

    def _which(self, name: str, paths: str=None) -> str:
        paths = paths or os.environ['PATH']
        found = None
        for path in paths.split(os.path.pathsep):
            path_name = os.path.join(path, name)
            if os.path.exists(path_name):
                found = path_name
        if found is None:
            raise RuntimeError('%r not found in PATH.' % (name, ))
        else:
            self.logger.debug('using %r at %r' % (name, found))
        return found

    def which(self, exe_names: str, paths: str=None) -> str:
        if isinstance(exe_names, str):
            exe_names = [exe_names]
        for ename in exe_names:
            try:
                return self._which(ename, paths)
            except RuntimeError as exc:
                pass
        raise RuntimeError('None of %r found in PATH.' % (exe_names, ))

    def stringify_args(self, args) -> Sequence[str]:
        str_args = [self.which(args[0], os.environ['PATH'])]
        no_val = object()
        for arg in args[1:]:
            val = no_val
            if isinstance(arg, core.EnvVar):
                val = arg.name
            if isinstance(arg, core.Flag):
                val = arg.value
            if isinstance(arg, enum.Enum):
                val = str(arg.value)
            if isinstance(arg, File):
                if not arg.exists:
                    self.logger.debug('%r does not (yet) exist', arg.path)
                val = arg.path
            if isinstance(arg, (int, float)):
                val = str(arg)
            if isinstance(arg, str):
                val = arg
            if val == no_val:
                msg = 'Cannot handle arg %r of type %r'
                msg %= arg, type(val)
                raise RuntimeError(msg)
            str_args.append(val)
        return str_args

    def run(self, args, **kwargs):
        str_args = self.stringify_args(args)
        for i, arg in enumerate(str_args):
            self.logger.debug('args[%d]: %r', i, arg)
        tic = time.time()
        subprocess.check_call(str_args, **kwargs)
        self.logger.debug('elapsed %.2fs' % (time.time() - tic, ))
