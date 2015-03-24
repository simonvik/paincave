import sys
import time
import struct
import threading
import json
import random

from websocket import WebSocketsServer

from ant.easy.node import Node
from ant.easy.channel import Channel
from ant.base.message import Message

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

    self.hr_parser = antparsers.Hr()
    self.power_parser = antparsers.Power()
    self.speed_cadence_parser = antparsers.SpeedCadence()

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


  def _handle_hr(self, msg):
    if self.hr_parser.parse(msg):
      hr = str(self.hr_parser.hr())
      msg = json.dumps({"event_type" : "hr", "value" : hr})
      self.was.send_to_all(msg)
      print("HR event %s" % msg)

  def _handle_speed_cad(self, msg):
    if self.speed_cadence_parser.parse(msg):
      cadence = self.speed_cadence_parser.cadence()
      m = json.dumps({"event_type" : "cad", "value" : str(cadence)})
      self.was.send_to_all(m)
      print("CAD event %s" % m)

      speed = self.speed_cadence_parser.speed()
      m = json.dumps({"event_type" : "speed", "value" : str(speed * 3.6)})
      self.was.send_to_all(m)
      print("Speed event %s" % m)

  def _handle_power(self, msg):
    if self.power_parser.parse(msg):
      power = self.power_parser.power()
      m = json.dumps({"event_type" : "power", "value" : power})
      self.was.send_to_all(m)
      print("Power event %s" % m)

  def __exit__(self, type_, value, traceback):
    self.stop()


def test_watt():
  parser = antparsers.Power()
  with open("stages_power_50-100watt.txt") as f:
    lines = f.read().splitlines()
    for line in lines:
      buf = line.split(",")
      out = []
      for num in buf:
        out.append(int(num))
      if random.randint(1, 10) > 0: # add some fun
        parser.parse(out)
  quit()


if __name__ == "__main__":

#  test_watt()

  NETKEY = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

  websocket_ant_server = WEBSOCKET_ANT_SERVER()
  websocket_ant_server.start()

  ant_server = ANT_SERVER(netkey=NETKEY, \
                          ant_devices = [ "power"], \
                          was = websocket_ant_server)
  ant_server.start()

  while True:
    try:
      time.sleep(1)
    except KeyboardInterrupt:
      ant_server.stop()
      websocket_ant_server.stop()
      sys.exit(0)



