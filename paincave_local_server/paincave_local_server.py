import sys
import time
import struct
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER


class ANT_SERVER(event.EventCallback):
  def __init__(self, netkey, ant_devices):
    self.ant_devices = ant_devices
    self.channels = []
    self.netkey = netkey
    self.antnode = None
    self.ant_modes = {
      "cad_speed" : {
        "device_id" : 121,
        "period" : 8086,
        "freq" : 57,
        "ant_name" : "C:CAD"
      },
      "hr" : {
        "device_id" : 120,
        "period" : 8070,
        "freq" : 57,
        "ant_name" : "C:HRM"
      }
    }

  def start(self):
    self._start_antnode()
    self._setup_channels()

  def stop(self):
    for c in self.channels:
      print("Killing : %s" % c.name)
      c.close()
      c.unassign()

    self.antnode.stop()

  def _start_antnode(self):
    stick = driver.USB2Driver("")
    self.antnode = node.Node(stick)
    self.antnode.start()

    print("Starting ant-node")

  def __enter__(self):
        return self

  def _setup_channels(self):

    key = node.NetworkKey('N:ANT+', self.netkey)
    self.antnode.setNetworkKey(0, key)
    self.antnode.registerEventListener(self)

    for device in self.ant_devices:
      print("Registering device : %s : %s" % (device, self.ant_modes[device]))
      dev = self.ant_modes[device]

      c = self.antnode.getFreeChannel()
      c.name = dev["ant_name"]
      c.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
      c.setID(dev["device_id"], 0, 0)
      c.setSearchTimeout(TIMEOUT_NEVER)
      c.setPeriod(dev["period"])
      c.setFrequency(dev["freq"])
      c.open()

      self.channels.append(c)

  def process(self, msg):
    print(msg)

  def __exit__(self, type_, value, traceback):
    self.stop()


if __name__ == "__main__":
  NETKEY = 'B9A521FBBD72C345'.decode('hex')

  ant_server = ANT_SERVER(netkey=NETKEY, ant_devices = ["hr"])
  ant_server.start()

  while True:
    try:
      time.sleep(1)
      print("sleeepy")
    except KeyboardInterrupt:
      ant_server.stop()
      sys.exit(0)



