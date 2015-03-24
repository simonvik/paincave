import math

class Power():
  def __init__(self):
    self.count = 0
    self.cad = 0         # [0-255] rpm
    self.prev_time = 0   # 1/2048 s
    self.prev_torque = 0 # 1/32 Nm
    self.power = 0       # watt
    self.pi_times_128 = 128 * math.pi

  def value():
    return self.power

  def parse(self, msg):
    if (msg[0] == 0x12):
      self.handle_0x12(msg)
    if (msg[0] == 0x13):
      self.handle_0x13(msg)

  def handle_0x12(self, msg):
    # Standard Crank Torque Main Data Page (0x12)
    delta_count = msg[1] - self.count
    if (delta_count > 0): # TODO: Handle wrap
      if (delta_count > 1):
        print "WRN: delta_count:", delta_count

      time = msg[5] * 256 + msg[4]
      torque = msg[7] * 256 + msg[6]

      delta_time = time - self.prev_time
      if delta_time < 0:
        print "INF: time wraps"
        delta_time += 65536

      delta_torque = torque - self.prev_torque
      if delta_torque < 0:
        print "INF: torque wraps"
        delta_torque += 65536

      self.count = msg[1]
      self.cad = msg[3]
      self.prev_time = time
      self.prev_torque = torque

      # angular_vel = 2 * math.pi * delta_count / (delta_time / 2048)
      # power = delta_torque * angular_vel / 32
      # power = self.pi_times_128 * delta_torque * delta_count / delta_time
      power = self.pi_times_128 * delta_torque / delta_time

      # print "Ang vel: ", angular_vel
      # print "Time:  ", time
      # print "dTime: ", delta_time
      # print "Torque: ", delta_torque
      print "Power: ", power, " W"

  def handle_0x13(self, msg):
    print "TODO"
