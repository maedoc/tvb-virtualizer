from __future__ import absolute_import
import abc
from ..cli.runner import Runner


class Flow(metaclass=abc.ABCMeta):
    """
    Interface for workflows.

    """

    @abc.abstractmethod
    def run(self, runner: Runner):
        pass
