import logging
import voluptuous as vol

from homeassistant.components.light import Light, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_DEVICES
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['honeywell_hgw2000']

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Optional(CONF_DEVICES, default=[]): vol.All(cv.ensure_list, [dict]),
})

HONEYWELL_HGW2000_API = 'honeywell_hgw2000_api'

def setup_platform(hass, config, add_devices, discovery_info=None):
  host = config.get(CONF_HOST)
  lights = config.get(CONF_DEVICES)

  add_devices(HoneywellLight(hass.data[HONEYWELL_HGW2000_API], light) for light in lights)

class HoneywellLight(Light):
  def __init__(self, api, light):
    self._api = api
    self._name = light['name']
    self._id = light['id']
    self._state = None
    self.update()
  
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
    return True

  def turn(self, switch):
    return self.update_state(self._api.request('controllight', 'lightid={id}&lightswitch={switch}&action=4&dimmer=255&_='.format(id = self._id, switch = switch)), 'lightswitch')

  def turn_on(self):
    if not self.turn(1):
      return self.turn(1)
    return True
  
  def turn_off(self):
    if not self.turn(0):
      return self.turn(0)
    return True

  def update(self):
    return self.update_state(self._api.request('querylight', 'lightid={id}&_='.format(id = self._id)), 'switch')
