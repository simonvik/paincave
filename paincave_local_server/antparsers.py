import math

class Hr():
  def __init__(self):
    self.hr = 0

  def hr(self):
    return self.hr

  def parse(self, msg):
    self.hr = msg[-1]
    return True


class Power():
  def __init__(self):
    self._count = 0
    self._cad = 0         # [0-255] rpm
    self._prev_time = 0   # 1/2048 s
    self._prev_torque = 0 # 1/32 Nm
    self._power = 0       # watt
    self._pi_times_128 = 128 * math.pi

  def power(self):
    return self._power

  def parse(self, msg):
    if msg[0] is 0x12:
      return self.handle_0x12(msg)
    if msg[0] is 0x13:
      return self.handle_0x13(msg)
    return False

  def handle_0x12(self, msg):
    # Standard Crank Torque Main Data Page (0x12)
    delta_count = msg[1] - self._count
    if (delta_count > 0): # TODO: Handle wrap
      if (delta_count > 1):
        print "WRN: delta_count:", delta_count

      time = msg[5] * 256 + msg[4]
      torque = msg[7] * 256 + msg[6]

      delta_time = time - self._prev_time
      if delta_time < 0:
        print "INF: time wraps"
        delta_time += 65536

      delta_torque = torque - self._prev_torque
      if delta_torque < 0:
        print "INF: torque wraps"
        delta_torque += 65536

      self._count = msg[1]
      self._cad = msg[3]
      self._prev_time = time
      self._prev_torque = torque

      # angular_vel = 2 * math.pi * delta_count / (delta_time / 2048)
      # power = delta_torque * angular_vel / 32
      # power = self.pi_times_128 * delta_torque * delta_count / delta_time
      self._power = self._pi_times_128 * delta_torque / delta_time

      # print "Ang vel: ", angular_vel
      # print "Time:  ", time
      # print "dTime: ", delta_time
      # print "Torque: ", delta_torque
      print "Power: ", self._power, " W"
      return True

  def handle_0x13(self, msg):
    pass


class SpeedCadence():
  def __init__(self):
    self._speed = 0
    self._cadence = 0
    self._prev_cadence = {"time" : 0, "count" : -1}
    self._prev_speed = {"time" : 0, "count" : -1}

  def speed(self):
    return self._speed

  def cadence(self):
    return self._cadence

  def parse(self, msg):
    parsed_cadence = self.parse_cadence(msg)
    parsed_speed = self.parse_speed(msg)
    if parsed_speed or parsed_cadence:
      return True
    return False

  def parse_cadence(self, msg):
    ret = False
    cad_event_time = msg[1] * 256 + msg[0]
    cad_event_count = msg[3] * 256 + msg[2]
    cad_event_time_delta = cad_event_time - self._prev_cadence["time"]
    # ignore redundant, old or invalid data
    if self._prev_cadence["count"] >= 0 \
        and cad_event_count != self._prev_cadence["count"] \
        and cad_event_time_delta > 0 \
        and cad_event_time_delta < 6000:
      self._cadence = (60 * (cad_event_count - self._prev_cadence["count"]) * 1024) \
            / cad_event_time_delta
      ret = True
    self._prev_cadence["time"] = cad_event_time
    self._prev_cadence["count"] = cad_event_count
    return ret

  def parse_speed(self, msg):
    ret = False
    speed_event_time = msg[5] * 256 + msg[4]
    speed_event_count = msg[7] * 256 + msg[6]
    speed_event_time_delta = speed_event_time - self._prev_speed["time"]
    # ignore redundant, old or invalid data
    if self._prev_speed["count"] >= 0 \
        and speed_event_count != self._prev_speed["count"] \
        and speed_event_time_delta > 0:
      self._speed = (2.096 * (speed_event_count - self._prev_speed["count"]) * 1024) \
              / speed_event_time_delta
      ret = True
    self._prev_speed["time"] = speed_event_time
    self._prev_speed["count"] = speed_event_count
    return ret
