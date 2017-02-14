"""module for Hook class."""
try:  # pragma: no cover
    from plugins_exception import PluginError
except ImportError:
    from .plugins_exception import PluginError


class Hook:
    """Hook class.

    used in HPluginMeta.

    Attributes:
        _handlers: Handlers.
    """

    _handlers = set()

    def addHandler(self, handler, pluginfo):
        self._handlers.add((handler, pluginfo))

    def __call__(self, *args, **kwargs):
        handler_returns = []
        for handlers, pluginfo in self._handlers:
            try:
                handler_returns.append(handlers(*args, **kwargs))
            except Exception as e:
                raise PluginError("{}:{}".format(pluginfo[0], pluginfo[1]))
        return handler_returns
