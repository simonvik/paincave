import sys
import time
import struct
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER

class HRM(event.EventCallback):

    def __init__(self, netkey):
        self.netkey = netkey
        self.antnode = None
        self.channel_cs = None
	self.lastCad = {"time" : 0, "count" : 0}
	self.lastSpeed = {"time" : 0, "count" : 0}

    def start(self):
        print("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel_cs.registerCallback(self)
        print("start listening for cad events")

    def stop(self):
        if self.channel_cs:
            self.channel_cs.close()
            self.channel_cs.unassign()
        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB2Driver("")
        self.antnode = node.Node(stick)
        self.antnode.start()

    def _setup_channel(self):
        key = node.NetworkKey('N:ANT+', self.netkey)
	self.antnode.registerEventListener(self)
        self.antnode.setNetworkKey(0, key)
        self.channel_cs = self.antnode.getFreeChannel()
        self.channel_cs.name = 'C:CAD'
        self.channel_cs.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel_cs.setID(121, 0, 0)
        self.channel_cs.setSearchTimeout(TIMEOUT_NEVER)
        self.channel_cs.setPeriod(8086)
        self.channel_cs.setFrequency(57)
        self.channel_cs.open()

    def process_events(self, msg):
	print msg

    def process(self, msg):
	#print(msg.payload)
	#return
	#if isinstance(msg, message.ChannelEventMessage):
	#    print(msg.getMessageID())
	#    print(msg.getMessageCode())
        #    print(msg.payload)

        if isinstance(msg, message.ChannelBroadcastDataMessage):

            BikeCadEventTime = ord(msg.payload[2]) * 256 + ord(msg.payload[1])
            BikeCadEventCount = ord(msg.payload[4]) * 256 + ord(msg.payload[3])

            BikeSpeedEventTime = ord(msg.payload[6]) * 256 + ord(msg.payload[5])
            BikeSpeedEventCount = ord(msg.payload[8]) * 256 + ord(msg.payload[7])


	    if BikeCadEventCount != self.lastCad["count"]:
                cad = (60 * (BikeCadEventCount - self.lastCad["count"])*1024) / (BikeCadEventTime - self.lastCad["time"])


		self.lastCad["time"] = BikeCadEventTime
		self.lastCad["count"] = BikeCadEventCount
		print "bajs"
                print cad


	    if BikeSpeedEventCount != self.lastSpeed["count"]:
                speed = (2.096 * (BikeSpeedEventCount - self.lastSpeed["count"])*1024) / (BikeSpeedEventTime - self.lastSpeed["time"])


		self.lastSpeed["time"] = BikeSpeedEventTime
		self.lastSpeed["count"] = BikeSpeedEventCount

                print speed*3.6



            #print("heart rate is {}".format(ord(msg.payload[-1])))
            #print(ord(msg.payload[1]) * 256 + ord(msg.payload[2]), "\n")

NETKEY = 'B9A521FBBD72C345'.decode('hex')

with HRM(netkey=NETKEY) as hrm:
    hrm.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
