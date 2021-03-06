# global imports
import json
import time

# local imports
import antparsers


class LogReplayer():
  def __init__(self, config, websocket_server):
    self.logfile = config["logfile"]
    self.speed = float(config["replay_speed"])
    self.websocket_server = websocket_server
    self.parsers = {
      "hr" : antparsers.Hr(),
      "power" : antparsers.Power(),
      "speed_cad" : antparsers.SpeedCadence()
    }

  def run(self):
    with open(self.logfile) as f:
      lines = f.read().splitlines()
    t = json.loads(lines[0])["time_millis"]

    for line in lines:
      line_j = json.loads(line)
      delta_t = line_j["time_millis"] - t
      t = line_j["time_millis"]
      if delta_t > 1:
        time.sleep(delta_t / 1000.0 / self.speed)

      parser = self.parsers[line_j["event_type"]]
      values = parser.parse(line_j["data"])
      if values:
        for value in antparsers.Parser.to_json(values):
          if self.websocket_server:
            self.websocket_server.send_to_all(value)
