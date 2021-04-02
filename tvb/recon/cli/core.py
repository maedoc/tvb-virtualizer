
"""
Core classes for CLI information.

"""

from typing import Tuple, Dict


class Flag:

    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def __repr__(self) -> str:
        return "<Flag '%s'>" % (self.value, )

    def __str__(self) -> str:
        return self.value


class FlagsMeta(type):
    """
    Instruments flags classes so that their attributes are instances of the
    above Flag class.

    """

    def __new__(cls: type, name: str, bases: Tuple[type],
                attrs: Dict[str, object]) -> type:
        for key, value in list(attrs.items()):
            if not key.startswith('_'):
                value: str
                attrs[key] = Flag(key, value)
        return super().__new__(cls, name, bases, attrs)


class EnvVar:

    def __init__(self, key: str, name: str):
        self.key = key
        self.name = name


class EnvMeta(type):
    """
    Instruments env classes so that their attributes are instances of the
    above EnvVar class.

    """

    def __new__(cls: type, name: str, bases: Tuple[type],
                attrs: Dict[str, object]) -> type:
        for key, value in list(attrs.items()):
            if not key.startswith('_'):
                value: str
                attrs[key] = EnvVar(key, value)
        return super().__new__(cls, name, bases, attrs)


class BaseFlags(metaclass=FlagsMeta):
    help = '-h'


class BaseEnv(metaclass=EnvMeta):
    path = 'PATH'


class BaseCLI:
    exe = ()

    class Env(BaseEnv):
        pass

    class Flags(BaseFlags):
        pass

    def help(self):
        return [self.exe, self.Flags.help]
