"""hplugin meta module."""
import logging
import uuid

from PyQt5.QtCore import pyqtWrapperType

try:  # pragma: no cover
    from hook import Hook
    from hplugins import registered
    from other_hplugin import OtherHPlugin
    from plugins_exception import PluginMethodError
except ImportError:
    from .hook import Hook
    from .hplugins import registered
    from .other_hplugin import OtherHPlugin
    from .plugins_exception import PluginMethodError

log = logging.getLogger(__name__)
""":class:`logging.Logger`: Logger for module."""
log_i = log.info
""":meth:`logging.Logger.info`: Info logger func"""
log_d = log.debug
""":meth:`logging.Logger.debug`: Debug logger func"""
log_w = log.warning
""":meth:`logging.Logger.warning`: Warning logger func"""
log_e = log.error
""":meth:`logging.Logger.error`: Error logger func"""
log_c = log.critical
""":meth:`logging.Logger.critical`: Critical logger func"""


class HPluginMeta(pyqtWrapperType):
    """h plugin meta."""

    def __init__(cls, name, bases, dct):  # NOQA
        if not name.endswith("HPlugin"):
            log_e("Main plugin class should end with name HPlugin")
            return

        if not hasattr(cls, "ID"):
            log_e("ID attribute is missing")
            return
        cls.ID = cls.ID.replace('-', '')
        if not hasattr(cls, "NAME"):
            log_e("NAME attribute is missing")
            return
        if not hasattr(cls, "VERSION"):
            log_e("VERSION attribute is missing")
            return
        if not hasattr(cls, "AUTHOR"):
            log_e("AUTHOR attribute is missing")
            return
        if not hasattr(cls, "DESCRIPTION"):
            log_e("DESCRIPTION attribute is missing")
            return

        try:
            val = uuid.UUID(cls.ID, version=4)
            assert val.hex == cls.ID
        except ValueError:
            log_e("Invalid plugin id. UUID4 is required.")
            return
        except AssertionError:
            log_e("Invalid plugin id. A valid UUID4 is required.")
            return

        if not isinstance(cls.NAME, str):
            log_e("Plugin name should be a string")
            return
        if not isinstance(cls.VERSION, tuple):
            log_e("Plugin version should be a tuple with 3 integers")
            return
        if not isinstance(cls.AUTHOR, str):
            log_e("Plugin author should be a string")
            return
        if not isinstance(cls.DESCRIPTION, str):
            log_e("Plugin description should be a string")
            return

        super().__init__(name, bases, dct)

        setattr(cls, "connectPlugin", cls.connectPlugin)
        setattr(cls, "newHook", cls.createHook)
        setattr(cls, "connectHook", cls.connectHook)
        setattr(cls, "__getattr__", cls.__getattr__)

        registered.register(cls)

    def connectPlugin(cls, pluginid, plugin_name):
        """
        Connect to other plugins
        Params:
            pluginid: PluginID of the plugin you want to connect to
            plugin_name: Name you want to referrer the other plugin as

        Other methods of other plugins can be used as such: self.plugin_name.method()
        """
        setattr(cls, plugin_name, OtherHPlugin(pluginid))

    def connectHook(self, pluginid, hook_name, handler):
        """Connect to other plugins' hooks.

        Args:
            pluginid: PluginID of the plugin that has the hook you want to connect to
            hook_name: Exact name of the hook you want to connect to
            handler: Your custom method that should be executed
                when the other plugin uses its hook.
        """

        assert isinstance(
            pluginid, str
        ) and isinstance(hook_name, str) and callable(handler), ""
        registered._connections.append((self.NAME, pluginid.replace('-', ''), hook_name, handler))

    def createHook(self, hook_name):
        """
        Create hooks that other plugins can extend
        Params:
            hook_name: Name of the hook you want to create.

        Hook will be used as such: self.hook_name()
        """

        assert isinstance(hook_name, str), ""
        h = Hook()
        registered.hooks[self.ID][hook_name] = h

    def __getattr__(self, key):
        try:
            return registered.hooks[self.ID][key]
        except KeyError:
            return PluginMethodError(key)
