"""module for Plugins class."""
import logging

try:  # pragma: no cover
    from hplugin_meta import HPluginMeta
    from plugins_exception import PluginNameError
except ImportError:
    from .hplugin_meta import HPluginMeta
    from .plugins_exception import PluginNameError


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


class Plugins:
    ""
    _connections = []
    _plugins = {}
    _pluginsbyids = {}
    hooks = {}

    def register(self, plugin):
        assert isinstance(plugin, HPluginMeta)
        self.hooks[plugin.ID] = {}
        self._plugins[plugin.NAME] = plugin()  # TODO: name conflicts?
        self._pluginsbyids[plugin.ID] = self._plugins[plugin.NAME]

    def _connectHooks(self):
        for plugin_name, pluginid, h_name, handler in self._connections:
            log_i("{}:{} connection to {}:{}".format(plugin_name, handler, pluginid, h_name))
            print(self.hooks)
            try:
                p = self.hooks[pluginid]
            except KeyError:
                log_e("Could not find plugin with plugin id: {}".format(pluginid))
                return
            try:
                h = p[h_name]
            except KeyError:
                log_e("Could not find pluginhook with name: {}".format(h_name))
                return

            h.addHandler(handler, (plugin_name, pluginid))
        return True

    def __getattr__(self, key):
        try:
            return self._plugins[key]
        except KeyError:
            raise PluginNameError(key)
