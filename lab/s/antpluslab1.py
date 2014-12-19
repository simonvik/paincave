import sys
import time
import struct
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER


class ANT_SERVER(event.EventCallback):
	def __init__(self, netkey):
		self.netkey = netkey
		self.antnode = None
		self.ant_modes = {
			"cad_speed" : {
				"device_id" : 121,
				"period" : 8086,
				"freq" : 57
			},
			"hr" : {
				"device_id" : 120,
				"period" : 8070,
				"freq" : 57
			}
		}

	def start(self):
		pass

	def stop(self):
		pass

	def _start_antnode(self):
		stick = driver.USB2Driver("")
		self.antnode = node.Node(stick)
		self.antnode.start()

	def process(self, msg):
		pass
