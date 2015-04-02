# global imports
import json
import os.path
import time
from datetime import datetime

# local imports
import antparsers

try:
  from ant.easy.node import Node
  from ant.easy.channel import Channel
  from ant.base.message import Message
  from ant.easy.exception import AntException
  from usb.core import USBError # TODO: let ant/base/driver.py throw an AntException
except ImportError as e:
  print("Failed to load ant libs : \n%s" % e)
  print("Download ant-lib from https://github.com/simonvik/openant")


class AntServer():
  def __init__(self, netkey, ant_devices, websocket_server):
    self.ant_devices = ant_devices
    self.channels = []
    self.netkey = netkey
    self.antnode = None
    self.websocket_server = websocket_server
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


  @staticmethod
  def setup_and_start(websocket_server, config):
    NETKEY = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]
    antserver = None
    for i in range(1, 3):
      try:
        antserver = AntServer(NETKEY, config["devices"], websocket_server)
        antserver._log_raw_data = config["raw_logging"]
        antserver._log_decoded = config["verbose"]
        try:
          antserver.start()
        except KeyboardInterrupt:
          pass
        finally:
          antserver.stop()
        break
      except AntException:
        print("ERR: Failed to setup ant server. Retrying... %s" % i)

  def start(self):
    if not os.path.isdir("logs"):
      os.mkdir("logs")
    self.logfile = datetime.strftime(datetime.now(), "logs/%Y%m%d_%H%M.txt")
    self.logfile_handle = open(self.logfile, "w")

    self._setup_channels()

  def stop(self):
    if self.antnode:
      self.antnode.stop()

  def __enter__(self):
    return self

  def _setup_channels(self):
    try:
      self.antnode = Node()
    except USBError:
      self.antnode = None
      print("""

Fatal error: Could not connect to ANT USB dongle
Could not connect to ANT USB dongle.
Please make sure no other application is using it, e.g. Garmin ANT Agent

""")
      return

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
      self.logfile_handle.write(m)
      self.logfile_handle.write("\n")
      self.logfile_handle.flush()
      os.fsync(self.logfile_handle.fileno())

  def _parse_and_send(self, event_type, data):
    self._log_raw(event_type, data)

    parser = self.parsers[event_type]
    values = parser.parse(data)
    if values:
      for value in antparsers.Parser.to_json(values):
        self.websocket_server.send_to_all(value)
        if self._log_decoded:
          print(value)

  def _handle_hr(self, data):
    self._parse_and_send("hr", data)

  def _handle_speed_cad(self, data):
    self._parse_and_send("speed_cad", data)

  def _handle_power(self, data):
    self._parse_and_send("power", data)

  def __exit__(self, type_, value, traceback):
    self.stop()
    self.logfile_handle.close()
