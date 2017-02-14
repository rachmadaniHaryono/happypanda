"""Module for error used in plugins."""


class PluginError(ValueError):
    """plugin error."""

    pass


class PluginIDError(PluginError):
    """plugin ide error."""

    pass


class PluginNameError(PluginIDError):
    """plugin name error."""

    pass


class PluginMethodError(PluginError):
    """plugin method error."""
    pass
