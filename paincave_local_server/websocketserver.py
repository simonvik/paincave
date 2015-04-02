# global imports
import threading

# local imports
import websocket


class WebsocketServer:
  def __init__(self, config, controller):
    self._port = int(config["port"])
    self._host = config["host"]
    self._controller = controller
    self._controller._websocket_server = self
    self._server_thread = None
    self._server = websocket.WebSocketsServer(self._port, self._host)
    self._server.set_fn_new_client(self._client_connect)
    self._server.set_fn_client_left(self._client_left)
    self._server.set_fn_message_received(self._message_received)

  def start(self):
    self._server_thread = threading.Thread(target=self._server.serve_forever)
    self._server_thread.start()

  def send_to_all(self, message):
    self._server.send_message_to_all(message)

  def stop(self):
    print("Stopping websocket server")
    self._server.shutdown()
    self._server.killall()

  def _message_received(self, handler, client, message):
    self._controller.onmessage(handler, client, message)

  def _client_connect(self, client, server):
    pass

  def _client_left(self, client, server):
    pass

