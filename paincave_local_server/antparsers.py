import math
import json

def _byte_wrap_delta(x, y):
  return x - y + 256 if x - y < -127 else x - y

class Parser():
  def __init__(self):
    self._values = {}

  def parse(self, msg):
    raise NotImplementedError()

  def values(self):
    return self._values

  def build_dict(self, keys):
    ret = dict()
    for key in keys:
      ret[key] = self._values[key]
    return ret

  @staticmethod
  def to_json(values):
    ret = []
    for key in values:
      print key , "-" , values[key]
      ret.append({"event_type" : key, "value" : values[key]})
    return ret

class Hr(Parser):
  def parse(self, msg):
    self._values["hr"] = msg[-1]
    return self.build_dict(["hr"])

class Power(Parser):
  def __init__(self):
    Parser.__init__(self)

    self._cad = 0         # [0-255] rpm
    self._prev_time = 0   # 1/2048 s
    self._prev_torque = 0 # 1/32 Nm
    self._power = 0       # watt
    self._pi_times_128 = 128 * math.pi

    self._0x10_count = 0
    self._0x10_cad = 0

    self._0x12_count = 0

    self._0x13_count = 0


    self._0x52_battery_status_names = {
      0x00 : "invalid",
      0x01 : "new",
      0x02 : "good",
      0x03 : "ok",
      0x04 : "low",
      0x05 : "critical",
      0x06 : "invalid",
      0x07 : "invalid"}

    self._message_handlers = {
      0x10 : self.handle_0x10,
      0x12 : self.handle_0x12,
      0x13 : self.handle_0x13,
      0x50 : self.handle_0x50,
      0x51 : self.handle_0x51,
      0x52 : self.handle_0x52}

  def parse(self, msg):
    data_page = msg[0]
    if data_page in self._message_handlers:
      return self._message_handlers[data_page](msg)
    else:
      print "WRN: Unhandled data page from power meter:", data_page
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

      self._values["power_0x10"] = self._0x10_current_power
      self._values["acc_power_0x10"] = self._0x10_acc_power
      self._values["cad_0x10"] = self._0x10_acc_power
      return self.build_dict([
          "power_0x10",
          "acc_power_0x10",
          "cad_0x10"
        ])

  def handle_0x12(self, msg):
    # Standard Crank Torque Main Data Page (0x12)
    delta_count = _byte_wrap_delta(msg[1], self._0x12_count)
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

      self._0x12_count = msg[1]
      self._cad = msg[3]
      self._prev_time = time
      self._prev_torque = torque
      self._power = self._pi_times_128 * delta_torque / delta_time

      self._values["power"] = self._power
      self._values["cad"] = self._cad
      return self.build_dict(["power", "cad"])

  def handle_0x13(self, msg):
    # Torque Effectiveness and Pedal Smoothness Main Data Page (0x13)
    delta_count = _byte_wrap_delta(msg[1], self._0x13_count)
    if (delta_count <= 0):
      return False
    self._0x13_count = msg[1]

    self._values["left_torque_effectiveness"] = msg[2] / 2.0 if msg[2] != 0xFF else msg[2]
    self._values["right_torque_effectiveness"] = msg[3] / 2.0 if msg[3] != 0xFF else msg[3]
    self._values["left_smoothness"] = msg[4] / 2.0 if msg[4] != 0xFF else msg[4]
    self._values["right_smoothness"] = msg[5] / 2.0 if msg[5] != 0xFF else msg[5]

    return self.build_dict([
        "left_torque_effectiveness",
        "right_torque_effectiveness",
        "left_smoothness",
        "right_smoothness"
      ])

  def handle_0x50(self, msg):
    # Common Data Page 80: Manufacturer's Information
    self._values["hw_revision"] = msg[3]
    self._values["manufacturer_id"] = msg[4] | (msg[5] << 8)
    self._values["model_number"] = msg[6] | (msg[7] << 8)
    return self.build_dict([
        "hw_revision",
        "manufacturer_id",
        "model_number"
      ])

  def handle_0x51(self, msg):
    # Common Page 81 (0x51) - Product Information
    self._values["sw_revision"] = msg[3] / 10.0 + (msg[2] / 1000.0 if msg[2] != 0xFF else 0)
    self._values["serial_number"] = msg[4] | (msg[5] << 8) | (msg[6] << 16) | (msg[7] << 24)
    return self.build_dict([
        "sw_revision",
        "serial_number"
      ])

  def handle_0x52(self, msg):
    # Common Page 82 (0x52): Battery Status
    self._values["battery_voltage"] = (msg[7] & 0x0F) + msg[6] / 256.0
    battery_status = (msg[7] & 0x7F) >> 4
    self._values["battery_status"] = self._0x52_battery_status_names[battery_status]

    resolution = 2 if msg[7] & 128 == 128 else 6
    self._values["battery_operating_time"] = (msg[3] + msg[4] * 256 + msg[5] * 65536) / resolution

    return self.build_dict([
        "battery_voltage",
        "battery_status",
        "battery_operating_time"
      ])

class SpeedCadence(Parser):
  def __init__(self):
    Parser.__init__(self)

    self._speed = 0
    self._cad = 0
    self._prev_cad = {"time" : 0, "count" : -1}
    self._prev_speed = {"time" : 0, "count" : -1}

  def parse(self, msg):
    ret = {}
    if self._parse_speed(msg):
      ret["speed"] = self._values["speed"]
    if self._parse_cadence(msg):
      ret["cad"] = self._values["cad"]
    return ret if len(ret) > 0 else False

  def _parse_cadence(self, msg):
    ret = False
    cad_event_time = msg[1] * 256 + msg[0]
    cad_event_count = msg[3] * 256 + msg[2]
    cad_event_time_delta = cad_event_time - self._prev_cad["time"]
    # ignore redundant, old or invalid data
    if self._prev_cad["count"] >= 0 \
        and cad_event_count != self._prev_cad["count"] \
        and cad_event_time_delta > 0 \
        and cad_event_time_delta < 6000:
      self._cad = (60 * (cad_event_count - self._prev_cad["count"]) * 1024) \
            / cad_event_time_delta
      self._values["cad"] = self._cad
      ret = True
    self._prev_cad["time"] = cad_event_time
    self._prev_cad["count"] = cad_event_count
    return ret

  def _parse_speed(self, msg):
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
      self._values["speed"] = self._speed
      ret = True
    self._prev_speed["time"] = speed_event_time
    self._prev_speed["count"] = speed_event_count
    return ret
