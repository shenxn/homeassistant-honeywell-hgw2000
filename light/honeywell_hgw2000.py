import logging
import voluptuous as vol
import time

from homeassistant.components.light import Light, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_DEVICES
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['honeywell_hgw2000']

_LOGGER = logging.getLogger(__name__)

CONF_INTERVAL = 'interval'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Optional(CONF_DEVICES, default=[]): vol.All(cv.ensure_list, [dict]),
  vol.Optional(CONF_INTERVAL, default = 2): cv.positive_int,
})

HONEYWELL_HGW2000_API = 'honeywell_hgw2000_api'

def setup_platform(hass, config, add_devices, discovery_info=None):
  host = config.get(CONF_HOST)
  lights = config.get(CONF_DEVICES)
  interval = config.get(CONF_INTERVAL)

  HoneywellLight.api = hass.data[HONEYWELL_HGW2000_API]

  total_interval = interval * len(lights)
  HoneywellLight.interval = total_interval
  add_devices(HoneywellLight(lights[i], i * interval) for i in range(len(lights)))

class HoneywellLight(Light):
  api = None
  interval = 100

  def __init__(self, light, initial_update):
    self._name = light['name']
    self._id = light['id']
    self._state = None
    self._last_update = time.time() + initial_update - self.interval
  
  @property
  def name(self):
    return self._name

  @property
  def is_on(self):
    return self._state

  def update_state(self, states, key):
    if states['rt'] != '0':
      return False
    self._state = states[key] == '1'
    self._last_update = time.time()
    return True

  def turn(self, switch):
    self.update_state(self.api.request('controllight', 'lightid={id}&lightswitch={switch}&action=4&dimmer=255&_='.format(id = self._id, switch = switch)), 'lightswitch')
  
  def update_query(self, retry = 0):
    return self.update_state(self.api.request('querylight', 'lightid={id}&_='.format(id = self._id), retry), 'switch')

  def turn_on(self, **kwargs):
    self.turn(1)
  
  def turn_off(self, **kwargs):
    self.turn(0)

  def toggle(self, **kwargs):
    if self.update_query(1):
      self.turn(0 if self._state else 1)

  def update(self):
    if self._last_update == None or self._last_update + self.interval < time.time():
      self.update_query()
