"""h plugins module."""
try:  # pragma: no cover
    from plugins import Plugins
except ImportError:
    from .plugins import Plugins

registered = Plugins()

# def startConnectionLoop():
#   def autoConnectHooks():
#       run = True
#       while run:
#           run = registered._connectHooks()
#   auto_t = threading.Thread(target=autoConnectHooks)
#   auto_t.start()
