import sys
import time
import struct
import threading
import json
import random
import time

from websocket import WebSocketsServer
import argparse

try:
  from ant.easy.node import Node
  from ant.easy.channel import Channel
  from ant.base.message import Message
except ImportError as e:
  print ("Failed to load ant libs : \n%s" % e)
  print ("Download ant-lib from https://github.com/simonvik/openant")

import antparsers

class WEBSOCKET_ANT_SERVER:
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
    self.server_thread.daemon = True
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


class ANT_SERVER():
  def __init__(self, netkey, ant_devices, was):
    self.ant_devices = ant_devices
    self.channels = []
    self.netkey = netkey
    self.antnode = None
    self.was = was
    self.ant_modes = {
      "speed_cad" : {
        "device_id" : 121,
        "period" : 8086,
        "freq" : 57,
        "ant_name" : "C:CAD",
        "handler" : "_handle_speed_cad"
      },
      "hr" : {
        "device_id" : 120,
        "period" : 8070,
        "freq" : 57,
        "ant_name" : "C:HRM",
        "handler" : "_handle_hr"
      },
      "power" : {
        "device_id" : 11,
        "period" : 8182,
        "freq" : 57,
        "ant_name" : "C:PWR",
        "handler" : "_handle_power"
      }
    }

    self.parsers = {
      "hr" : antparsers.Hr(),
      "power" : antparsers.Power(),
      "speed_cad" : antparsers.SpeedCadence()
    }
    self._log_raw_data = False
    self._log_decoded = True

  def start(self):
    self._setup_channels()

  def stop(self):
    self.antnode.stop()

  def __enter__(self):
    return self

  def _setup_channels(self):
    self.antnode = Node()
    self.antnode.set_network_key(0x00, self.netkey)

    for device in self.ant_devices:
      print("Registering device : %s : %s" % (device, self.ant_modes[device]))
      dev = self.ant_modes[device]

      c = self.antnode.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)
      c.set_id(0, dev["device_id"], 0)
      c.set_search_timeout(12)
      c.set_period(dev["period"])
      c.set_rf_freq(dev["freq"])
      m = getattr(self, dev["handler"])
      c.on_broadcast_data = m
      c.on_burst_data = m
      c.open()
      self.channels.append(c)

    self.antnode.start()

  def _log_raw(self, event_type, msg):
    if self._log_raw_data:
      data = []
      for m in msg:
        data.append(m)
      m = json.dumps({"raw" : "true",
                      "event_type" : event_type,
                      "time_millis" : int(time.time() * 1000),
                      "data" : data})
      print >> sys.stderr, m

  def _parse_and_send(self, event_type, data):
    self._log_raw(event_type, data)

    parser = self.parsers[event_type]
    if parser.parse(data):
      for value in parser.values():
        self.was.send_to_all(json.dumps(value))
        if self._log_decoded:
          print value

  def _handle_hr(self, data):
    self._parse_and_send("hr", data)

  def _handle_speed_cad(self, msg):
    self._parse_and_send("speed_cad", data)

  def _handle_power(self, msg):
    self._parse_and_send("power", data)

  def __exit__(self, type_, value, traceback):
    self.stop()


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
    for line in lines:
      time.sleep(0.1) # TODO: Replay in realtime or factor of time
      line_j = json.loads(line)
      parser = self.parsers[line_j["event_type"]]
      if parser.parse(line_j["data"]):
        for value in parser.values():
          print "Decoded value: %s" % value
          self.was.send_to_all(json.dumps(value))


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Paincave server')
  parser.add_argument('-l', '--replay-log', metavar='logfile', help='Replays a log file')
  parser.add_argument('--replay-speed', metavar='speed', default=1.0, type=float, help='Replay speed factor')
  parser.add_argument('-v', action='store_true', default=False, help='Verbose, prints parsed data')
  parser.add_argument('--enable-log', action='store_true', default=False, help='Logs raw data')
  args = parser.parse_args()

  NETKEY = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

  websocket_ant_server = WEBSOCKET_ANT_SERVER()
  websocket_ant_server.start()

  if args.replay_log:
    log_replayer = LogReplayer(args.replay_log, args.replay_speed, websocket_ant_server)
    log_replayer.run()
    quit()

  ant_server = ANT_SERVER(netkey=NETKEY, \
                          ant_devices = ["hr", "speed_cad", "power"], \
                          was = websocket_ant_server)
  ant_server._log_decoded = args.v
  ant_server._log_raw_data = args.enable_log #TODO: write to ./logs/YYYYMMDD-HHMM.txt
  ant_server.start()

  while True:
    try:
      time.sleep(1)
    except KeyboardInterrupt:
      ant_server.stop()
      websocket_ant_server.stop()
      sys.exit(0)
