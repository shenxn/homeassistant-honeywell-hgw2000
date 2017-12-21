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

  def request(self, action, payload, retry = 1):
    import requests
    r = requests.post(
      'http://{host}/cgi-bin/{action}.cgi'.format(host = self._host, action = action),
      data = payload)
    states = r.text.split(',')
    states_parsed = {}
    for state in states:
      values = state.split(':')
      if len(values) == 2:
        states_parsed[values[0]] = values[1]
      else:
        if not '_' in states_parsed:
          states_parsed['_'] = []
        states_parsed['_'].append(values)
    if states_parsed['rt'] != '0':
      if retry > 0:
        self.request(action, payload, retry - 1)
      else:
        _LOGGER.error('Request failed [{action}({payload})]: {msg}'.format(action = action, payload = payload, msg = r.text))
    return states_parsed
