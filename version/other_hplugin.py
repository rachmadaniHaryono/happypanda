"""module for OtherHPlugin."""
try:  # pragma: no cover
    from plugins import registered
    from plugins_exception import (
        PluginIDError,
        PluginMethodError,
    )
except ImportError:
    from .plugins import registered
    from .plugins_exception import (
        PluginIDError,
        PluginMethodError,
    )


class OtherHPlugin:
    """other HPlugin class.

    Used in HPluginMeta.

    _id: Id.
    """

    def __init__(self, pluginid):
        self._id = pluginid.replace('-', '')

    def __getattr__(self, key):
        try:
            plugin = registered._pluginsbyids[self._id]

            pluginmethod = getattr(plugin, key, None)
            if pluginmethod:
                return pluginmethod
            else:
                raise PluginMethodError(key)
        except KeyError:
            raise PluginIDError(self._id)
