import logging
import voluptuous as vol

from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['requests']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'honeywell_hgw2000'

CONFIG_SCHEMA = vol.Schema({
  DOMAIN: vol.Schema({
    vol.Required(CONF_HOST): cv.string,
  })
}, extra=vol.ALLOW_EXTRA)

HONEYWELL_HGW2000_API = 'honeywell_hgw2000_api'

def setup(hass, config):
  host = config[DOMAIN].get(CONF_HOST)
  hass.data[HONEYWELL_HGW2000_API] = HoneywellAPI(host)
  return True

class HoneywellAPI():
  def __init__(self, host):
    self._host = host

  def request(self, action, payload):
    import requests
    r = requests.post(
      'http://{host}/cgi-bin/{action}.cgi'.format(host = self._host, action = action),
      data = payload)
    states = r.text.split(',')
    states_parsed = {}
    for state in states:
      key_value = state.split(':')
      states_parsed[key_value[0]] = key_value[1] if len(key_value) > 1 else ''
    if states_parsed['rt'] != '0':
      _LOGGER.error('Request failed [{action}({payload})]: {msg}'.format(action = action, payload = payload, msg = r.text))
    return states_parsed
