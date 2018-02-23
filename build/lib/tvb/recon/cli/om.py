
"""
CLI information for om.

"""

from .core import BaseCLI, BaseEnv, BaseFlags


class BaseOmFlags(BaseFlags):
    """
    Base flags for om commands.

    """
    pass


class BaseOmEnv(BaseEnv):
    """
    Base environment variables for om commands.

    """
    pass


class BaseOmCLI(BaseCLI):
    """
    Base CLI for om commands.

    """

    class Flags(BaseOmFlags):
        pass

    class Env(BaseOmEnv):
        pass


class om_assemble(BaseOmCLI):
    """
    The om_assemble command from the om package.

    """
    exe = 'om_assemble'


class om_gain(BaseOmCLI):
    """
    The om_gain command from the om package.

    """
    exe = 'om_gain'


class om_minverser(BaseOmCLI):
    """
    The om_minverser command from the om package.

    """
    exe = 'om_minverser'
