# global imports
import threading

# local imports
import websocket


class WebsocketServer:
  def __init__(self, config):
    self.port = int(config["port"])
    self.host = config["host"]
    self.server_thread = None
    self.server = websocket.WebSocketsServer(self.port, self.host)
    self.server.set_fn_new_client(self.client_connect)
    self.server.set_fn_client_left(self.client_left)
    self.server.set_fn_message_received(self.message_received)

  def client_connect(self, client, server):
    pass

  def start(self):
    self.server_thread = threading.Thread(target=self.server.serve_forever)
    self.server_thread.start()

  def client_left(self, client, server):
    pass

  def message_received(self, client, server):
    pass

  def send_to_all(self, message):
    self.server.send_message_to_all(message)

  def stop(self):
    print("Stopping websocket server")
    self.server.shutdown()
    self.server.killall()
