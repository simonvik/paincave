# global imports
import argparse
import json
import os.path
import random
import struct
import sys
import threading
import time
from datetime import datetime

# local imports
import antparsers
from antserver import AntServer
from websocket import WebSocketsServer


class WebsocketAntServer:
  def __init__(self):
    self.port = 13254
    self.server_thread = None
    self.server = WebSocketsServer(self.port, "0.0.0.0")
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


class LogReplayer():
  def __init__(self, logfile, speed, was):
    self.logfile = logfile
    self.speed = speed
    self.was = was
    self.parsers = {
      "hr" : antparsers.Hr(),
      "power" : antparsers.Power(),
      "speed_cad" : antparsers.SpeedCadence()
    }

  def run(self):
    with open(self.logfile) as f:
      lines = f.read().splitlines()
    t = json.loads(lines[0])["time_millis"]

    for line in lines:
      line_j = json.loads(line)
      delta_t = line_j["time_millis"] - t
      t = line_j["time_millis"]
      if delta_t > 1:
        time.sleep(delta_t / 1000.0 / self.speed)

      parser = self.parsers[line_j["event_type"]]
      values = parser.parse(line_j["data"])
      if values:
        for value in antparsers.Parser.to_json(values):
          print(value)
          self.was.send_to_all(json.dumps(value))


class Paincave():
  def __init__(self):
    self._NETKEY = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

  def _parse_args(self):
    parser = argparse.ArgumentParser(description='Paincave server')
    parser.add_argument('-l', '--replay-log', metavar='logfile', help='Replays a log file')
    parser.add_argument('--replay-speed', metavar='speed', default=1.0, type=float, help='Replay speed factor')
    parser.add_argument('-v', action='store_true', default=False, help='Verbose, prints parsed data')
    parser.add_argument('--enable-log', action='store_true', default=True, help='Logs raw data')
    self._args = parser.parse_args()

  def _replay_log(self):
    log_replayer = LogReplayer(self._args.replay_log, self._args.replay_speed, self._websocket_ant_server)
    try:
      log_replayer.run()
    except KeyboardInterrupt:
      pass

  def _setup_and_start_antserver(self):
    try:
      #todo
      log_config = {"log_decoded" : self._args.v,
                    "log_raw_data" : self._args.enable_log}
      antserver = AntServer.setup_and_start(netkey=self._NETKEY, \
                                ant_devices = ["hr", "speed_cad", "power"], \
                                was = self._websocket_ant_server,
                                log_config = log_config)
    except KeyboardInterrupt:
      pass

  def main(self):
    self._parse_args()

    self._websocket_ant_server = WebsocketAntServer()
    self._websocket_ant_server.start()

    try:
      if self._args.replay_log:
        self._replay_log()
      else:
        self._setup_and_start_antserver()
    finally:
      print("INF: Killing websocket")
      self._websocket_ant_server.stop()


if __name__ == "__main__":
  Paincave().main()
