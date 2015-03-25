import math
import json

def _byte_wrap_delta(x, y):
  return x - y + 256 if x - y < -127 else x - y

class Hr():
  def __init__(self):
    self._hr = 0

  def hr(self):
    return self._hr

  def json_messages(self):
    hr = str(self._hr)
    msg = json.dumps({"event_type" : "hr", "value" : hr})
    return [msg]

  def parse(self, msg):
    self._hr = msg[-1]
    return True


class Power():
  def __init__(self):
    self._count = 0
    self._cad = 0         # [0-255] rpm
    self._prev_time = 0   # 1/2048 s
    self._prev_torque = 0 # 1/32 Nm
    self._power = 0       # watt
    self._pi_times_128 = 128 * math.pi

    self._0x10_count = 0
    self._0x10_cad = 0

  def power(self):
    return self._power

  def json_messages(self):
    msg_power = json.dumps({"event_type" : "power", \
                            "value" : str(self._power)})
    msg_cadence = json.dumps({"event_type" : "cad", \
                              "value" : str(self._cad), \
                              "source" : "power"})
    return [msg_power, msg_cadence]

  def parse(self, msg):
    if msg[0] == 0x10:
      return self.handle_0x10(msg)
    if msg[0] == 0x12:
      return self.handle_0x12(msg)
    if msg[0] == 0x13:
      return self.handle_0x13(msg)
    return False

  def handle_0x10(self, msg):
    # Standard Power-Only Main Data Page (0x10)
    delta_count = _byte_wrap_delta(msg[1], self._0x10_count)
    if (delta_count > 0):
      if (delta_count > 1):
        print "WRN: delta_count:", delta_count

      self._0x10_count = msg[1]
      self._0x10_cad = msg[3]
      self._0x10_acc_power = msg[5] * 256 + msg[4]
      self._0x10_current_power = msg[7] * 256 + msg[6]

      print "Accumulated Power: ", self._0x10_acc_power
      print "Instant Power: ", self._0x10_current_power
      return True

  def handle_0x12(self, msg):
    # Standard Crank Torque Main Data Page (0x12)
    delta_count = _byte_wrap_delta(msg[1], self._count)
    if (delta_count > 0):
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

  def json_messages(self):
    msg_speed = json.dumps({"event_type" : \
                            "speed", "value" : str(self._speed * 3.6)})
    msg_cadence = json.dumps({"event_type" : "cad", \
                              "value" : str(self._cadence), \
                              "source" : "speed_cad"})
    return [msg_speed, msg_cadence]

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
