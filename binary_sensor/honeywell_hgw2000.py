import logging
import voluptuous as vol
import time
import json

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_HOST, CONF_ID, CONF_SENSORS, CONF_SENSOR_TYPE
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['honeywell_hgw2000']

_LOGGER = logging.getLogger(__name__)

CONF_INTERVAL = 'interval'

SENSOR_SCHEMA = vol.Schema({
  vol.Required(CONF_ID): cv.positive_int,
  vol.Required(CONF_SENSOR_TYPE, default = None): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Optional(CONF_SENSORS, default={}): vol.Schema({cv.slug: SENSOR_SCHEMA}),
  vol.Optional(CONF_INTERVAL, default = 10): cv.positive_int,
})

HONEYWELL_HGW2000_API = 'honeywell_hgw2000_api'

def setup_platform(hass, config, add_devices, discovery_info=None):
  host = config.get(CONF_HOST)
  devices = config.get(CONF_SENSORS)
  HoneywellSensor.interval = config.get(CONF_INTERVAL)
  HoneywellSensor.api = hass.data[HONEYWELL_HGW2000_API]

  HoneywellSensor.update_states()

  add_devices(HoneywellSensor(name, sensor_conf) for name, sensor_conf in devices.items())

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

  def __init__(self, name, sensor_conf):
    self._name = name
    self._key = '1-{zone}'.format(zone = sensor_conf[CONF_ID])
    self._type = sensor_conf[CONF_SENSOR_TYPE]

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
  def device_class(self):
    return self._type

  @property
  def state(self):
    sensor = self.sensors[self._key]
    return 'on' if sensor['alarmed'] else 'off'

  def update(self):
    return self.update_states()