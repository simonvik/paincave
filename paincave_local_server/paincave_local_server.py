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
    pass

  def _parse_args(self):
    parser = argparse.ArgumentParser(description='Paincave server')
    parser.add_argument('-l', '--replay-log', metavar='logfile', help='Replays a log file')
    parser.add_argument('--replay-speed', metavar='speed', default=1.0, type=float, help='Replay speed factor')
    parser.add_argument('-v', action='store_true', default=False, help='Verbose, prints parsed data')
    parser.add_argument('--enable-log', action='store_true', default=True, help='Logs raw data')
    self._args = parser.parse_args()

  def _replay_log(self):
    log_replayer = LogReplayer(self._args.replay_log,
                               self._args.replay_speed,
                               self._websocket_server)
    try:
      log_replayer.run()
    except KeyboardInterrupt:
      pass

  def _setup_and_start_antserver(self):
    try:
      log_config = {"log_decoded" : self._args.v,
                    "log_raw_data" : self._args.enable_log}
      antserver = AntServer.setup_and_start(ant_devices = ["hr", "speed_cad", "power"], \
                                websocket_server = self._websocket_server,
                                log_config = log_config)
    except KeyboardInterrupt:
      pass

  def main(self):
    logging.basicConfig()
    self._parse_args()

    self._websocket_server = WebsocketServer()
    self._websocket_server.start()

    try:
      if self._args.replay_log:
        self._replay_log()
      else:
        self._setup_and_start_antserver()
    finally:
      print("INF: Killing websocket")
      self._websocket_server.stop()


if __name__ == "__main__":
  Paincave().main()
