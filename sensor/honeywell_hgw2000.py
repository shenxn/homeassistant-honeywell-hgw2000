import logging
import voluptuous as vol
import time
import json

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_HOST, CONF_DEVICES
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['honeywell_hgw2000']

_LOGGER = logging.getLogger(__name__)

CONF_INTERVAL = 'interval'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Optional(CONF_DEVICES, default=[]): vol.All(cv.ensure_list, [dict]),
  vol.Optional(CONF_INTERVAL, default = 5): cv.positive_int,
})

HONEYWELL_HGW2000_API = 'honeywell_hgw2000_api'

def setup_platform(hass, config, add_devices, discovery_info=None):
  host = config.get(CONF_HOST)
  sensors = config.get(CONF_DEVICES)
  HoneywellSensor.interval = config.get(CONF_INTERVAL)
  HoneywellSensor.api = hass.data[HONEYWELL_HGW2000_API]

  HoneywellSensor.update_states()

  add_devices(HoneywellSensor(sensor) for sensor in sensors)

LOCK_TIMEOUT = 2

class HoneywellSensorStatus:
  def __init__(self, zone, zone_type, armed, is_24h, alarmed, error, state):
    self.zone = zone
    self.zone_type = zone_type
    self.armed = armed
    self.is_24h = is_24h
    self.alarmed = alarmed
    self.error = error
    self.state = state

class HoneywellSensor(Entity):
  api = None
  interval = 5
  state_key = 0
  last_update = None
  lock_time = None

  sensors = {}

  def __init__(self, sensor):
    self._name = sensor['name']
    self._key = sensor['key']

  @staticmethod
  def update_states():
    if HoneywellSensor.lock_time != None and HoneywellSensor.lock_time + LOCK_TIMEOUT >= time.time():
      return True
    if HoneywellSensor.last_update != None and HoneywellSensor.last_update + HoneywellSensor.interval >= time.time():
      return True
    HoneywellSensor.lock_time = time.time()
    states = HoneywellSensor.api.request('queryalarm', 'zone=0&ztype=0&zoneinfo=0&zonestatekey={state_key}'.format(state_key = HoneywellSensor.state_key))
    if states['rt'] != '0':
      lock_time = None
      return False
    state_key = int(states['_'][0][0])
    if state_key <= HoneywellSensor.state_key:
      return False # Timeout
    states = states['_']
    for i in range(1, len(states)):
      zone = int(states[i][1])
      zone_type = int(states[i][2])
      state = int(states[i][3])
      key = '{type}-{zone}'.format(type = zone_type, zone = zone)
      HoneywellSensor.sensors[key] = {
        'armed': (state & 0x100) == 0x100,
        'is_24h': (state & 0x200) == 0x200,
        'alarmed': (state & 0x080) > 0,
        'error': (not (state & 0x080) and (state & 0x47f)) > 0
      }
    HoneywellSensor.last_update = time.time()
    HoneywellSensor.lock_time = None
    return True
  
  @property
  def name(self):
    return self._name

  @property
  def state(self):
    sensor = self.sensors[self._key]
    if sensor['error']:
      return 'error'
    if not sensor['is_24h'] and not sensor['armed']:
      return 'disarmed'
    return 'on' if sensor['alarmed'] else 'off'

  def update(self):
    return self.update_states()
