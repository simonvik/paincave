import sys
import time
import struct
import threading
import json
import math
import random

from websocket import WebSocketsServer

from ant.easy.node import Node
from ant.easy.channel import Channel
from ant.base.message import Message


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
      "cad_speed" : {
        "device_id" : 121,
        "period" : 8086,
        "freq" : 57,
        "ant_name" : "C:CAD",
        "handler" : "_handle_cad_speed"
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

    self.ant_power_parser = AntPowerParser()

    #Semi temp-values, needs to diff
    self.lastCad = {"time" : 0, "count" : -1}
    self.lastSpeed = {"time" : 0, "count" : -1}

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
    hr = str(msg[-1])
    msg = json.dumps({"event_type" : "hr", "value" : hr})
    print("HR event %s" % msg)

    self.was.send_to_all(msg)

  def _handle_cad_speed(self, msg):
    #Can probably be written more nicely

    #CADENCE
    BikeCadEventTime = msg[1] * 256 + msg[0]
    BikeCadEventCount = msg[3] * 256 + msg[2]
    BikeCadEventTimeDelta = BikeCadEventTime - self.lastCad["time"]

    # ignore redundant, old or invalid data
    if self.lastCad["count"] >= 0 \
        and BikeCadEventCount != self.lastCad["count"] \
        and BikeCadEventTimeDelta > 0 \
        and BikeCadEventTimeDelta < 6000:
      cad = (60 * (BikeCadEventCount - self.lastCad["count"]) * 1024) \
            / BikeCadEventTimeDelta
      m = json.dumps({"event_type" : "cad", "value" : cad})
      self.was.send_to_all(m)
      print("CAD event %s" % m)

    self.lastCad["time"] = BikeCadEventTime
    self.lastCad["count"] = BikeCadEventCount

    #SPEED
    BikeSpeedEventTime = msg[5] * 256 + msg[4]
    BikeSpeedEventCount = msg[7] * 256 + msg[6]
    BikeSpeedEventTimeDelta = BikeSpeedEventTime - self.lastSpeed["time"]

    # ignore redundant, old or invalid data
    if self.lastSpeed["count"] >= 0 \
        and BikeSpeedEventCount != self.lastSpeed["count"] \
        and BikeSpeedEventTimeDelta > 0:
      speed = (2.096 * (BikeSpeedEventCount - self.lastSpeed["count"]) * 1024) \
              / BikeSpeedEventTimeDelta
      m = json.dumps({"event_type" : "speed", "value" : speed * 3.6})
      self.was.send_to_all(m)
      print("Speed event %s" % m)

    self.lastSpeed["time"] = BikeSpeedEventTime
    self.lastSpeed["count"] = BikeSpeedEventCount

  def _handle_power(self, msg):
    #hr = str(msg[-1])
    #msg = json.dumps({"event_type" : "hr", "value" : hr})
    power = self.ant_power_parser.on_message(msg[1])
    m = json.dumps({"event_type" : "power", "value" : power})
    self.was.send_to_all(m)
    print("Power event %s" % m)

  def __exit__(self, type_, value, traceback):
    self.stop()


class AntPowerParser():
  def __init__(self):
    self.msg_0x12_count = 0
    self.msg_0x12_cad = 0
    self.msg_0x12_prev_time = 0 # 1/2048s
    self.msg_0x12_prev_torque = 0
    self.pi_times_128 = 128 * math.pi

  def on_message(self, msg):

    if (msg[0] == 0x12):
      # Standard Crank Torque Main Data Page (0x12)
      delta_count = msg[1] - self.msg_0x12_count
      if (delta_count > 0): # TODO: Handle wrap
        if (delta_count > 1):
          print "WRN: delta_count:", delta_count
        time = msg[5] * 256 + msg[4]
        torque = msg[7] * 256 + msg[6]

        delta_time = time - self.msg_0x12_prev_time
        if delta_time < 0:
          print "INF: time wraps"
          delta_time += 65536

        delta_torque = torque - self.msg_0x12_prev_torque
        if delta_torque < 0:
          print "INF: torque wraps"
          delta_torque += 65536

        self.msg_0x12_count = msg[1]
        self.msg_0x12_cad = msg[3]
        self.msg_0x12_prev_time = time
        self.msg_0x12_prev_torque = torque

#        angular_vel = 2 * math.pi * delta_count / (delta_time / 2048)
#        watt = delta_torque * angular_vel / 32
#        watt = self.pi_times_128 * delta_torque * delta_count / delta_time
        watt = self.pi_times_128 * delta_torque / delta_time

#        print "Ang vel: ", angular_vel
#        print "Time:  ", time
#        print "dTime: ", delta_time
#        print "Torque: ", delta_torque
        print "Watt: ",watt






def test_watt():
  parser = AntPowerParser()
  with open("stages_power_50-100watt.txt") as f:
    lines = f.read().splitlines()
    for line in lines:
      buf = line.split(",")
      out = []
      for num in buf:
        out.append(int(num))
      if random.randint(1, 10) > 0: # add some fun
        parser.on_message(out)
  quit()



if __name__ == "__main__":

  test_watt()

  NETKEY = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

  websocket_ant_server = WEBSOCKET_ANT_SERVER()
  websocket_ant_server.start()

  ant_server = ANT_SERVER(netkey=NETKEY, \
                          ant_devices = ["power"], \
                          was = websocket_ant_server)
  ant_server.start()

  while True:
    try:
      time.sleep(1)
    except KeyboardInterrupt:
      ant_server.stop()
      websocket_ant_server.stop()
      sys.exit(0)



