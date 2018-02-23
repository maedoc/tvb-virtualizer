
"""
CLI information for mne.

"""

from .core import BaseCLI, BaseEnv, BaseFlags


class BaseMneFlags(BaseFlags):
    """
    Base flags for mne commands.

    """
    pass


class BaseMneEnv(BaseEnv):
    """
    Base environment variables for mne commands.

    """
    pass


class BaseMneCLI(BaseCLI):
    """
    Base CLI for mne commands.

    """

    class Flags(BaseMneFlags):
        pass

    class Env(BaseMneEnv):
        pass


class mne_watershed_bem(BaseMneCLI):
    """
    The mne_watershed_bem command from the mne package.

    """
    exe = 'mne_watershed_bem'
