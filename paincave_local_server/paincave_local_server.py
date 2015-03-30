# global imports
import argparse
import json
import logging
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
from logreplayer import LogReplayer
from websocketserver import WebsocketServer


class Paincave():
  def __init__(self):
    self._websocket_server = None
    pass

  def _parse_args(self):
    parser = argparse.ArgumentParser(description='Paincave server')
    parser.add_argument('-c', '--config', metavar='config_file', default="config.json", help='Configuration file')
    parser.add_argument('-l', '--replay-log', metavar='logfile', help='Replays a log file')
    parser.add_argument('--replay-speed', metavar='speed', default=None, type=float, help='Replay speed factor')
    parser.add_argument('-v', action='store_true', default=None, help='Verbose, prints parsed data')
    self._args = parser.parse_args()

  def _load_config(self, config_file):
    with open(config_file) as f:
      self._config = json.loads(f.read())

    # Need a cleaner way to override config. "python server.py ant.verbose=1 logreplayer.logfile=file.txt"?
    if self._args.replay_log != None:
      self._config["logreplayer"]["enabled"] = 1
      self._config["logreplayer"]["logfile"] = self._args.replay_log
      if self._args.replay_speed != None:
        self._config["logreplayer"]["replay_speed"] = self._args.replay_speed
    if self._args.v:
      self._config["ant"]["verbose"] = True

  def _replay_log(self):
    log_replayer = LogReplayer(self._config["logreplayer"],
                               self._websocket_server)
    try:
      log_replayer.run()
    except KeyboardInterrupt:
      pass

  def _setup_and_start_antserver(self, config):
    try:
      antserver = AntServer.setup_and_start(websocket_server = self._websocket_server,
                                            config = config)
    except KeyboardInterrupt:
      pass

  def main(self):
    logging.basicConfig()
    self._parse_args()
    self._load_config(self._args.config)

    if self._config["server"]["enabled"]:
      self._websocket_server = WebsocketServer(self._config["server"])
      self._websocket_server.start()

    try:
      if self._config["logreplayer"]["enabled"]:
        self._replay_log()
      elif self._config["ant"]["enabled"]:
        self._setup_and_start_antserver(self._config["ant"])
    finally:
      print("INF: Killing websocket")
      if self._websocket_server:
        self._websocket_server.stop()


if __name__ == "__main__":
  Paincave().main()
