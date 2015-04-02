
class Controller():
  def __init__(self):
    self._antserver = None
    self._websocket_server = None

  def onmessage(self, handler, client, message):
    print message
    pass

  def send_to_all(self, message):
    if self._websocket_server:
      self._websocket_server.send_to_all(message)
