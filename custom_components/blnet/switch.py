"""
Connect to a BL-NET via its web interface and read and write data

Switch to control digital outputs
"""
import logging

from homeassistant.const import (
    STATE_UNKNOWN,
    STATE_OFF,
    STATE_ON,
)

try:
    from homeassistant.components.switch import SwitchEntity
except ImportError:
    from homeassistant.components.switch import SwitchDevice as SwitchEntity

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'blnet'

MODE = 'mode'
FRIENDLY_NAME = 'friendly_name'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the BLNET component."""

    if discovery_info is None:
        _LOGGER.error("No BL-Net communication configured")
        return False

    switch_id = discovery_info['id']
    blnet_id = discovery_info['name']
    comm = hass.data['DATA_{}'.format(DOMAIN)]

    add_devices([BLNETSwitch(switch_id, blnet_id, comm),
                 BLNETModeSwitch(switch_id, blnet_id, comm)], True)
    return True


class BLNETSwitch(SwitchEntity):
    """
    Representation of a switch that toggles a digital output of the UVR1611.
    """

    def __init__(self, switch_id, blnet_id, comm):
        """Initialize the switch."""
        self._blnet_id = blnet_id
        self._id = switch_id
        self.communication = comm
        self._name = blnet_id
        self._friendly_name = blnet_id
        self._unique_id = f"{switch_id}_{blnet_id}"  # Eindeutige ID
        self._state = STATE_UNKNOWN
        self._assumed_state = True
        self._icon = None
        self._mode = STATE_UNKNOWN
        self._last_updated = None

    @property
    def unique_id(self):
        """Return a unique ID for this switch."""
        return self._unique_id

    def update(self):
        """Get the latest data from communication device."""
        last_blnet_update = self.communication.last_updated()

        if last_blnet_update == self._last_updated:
            return

        sensor_data = self.communication.data.get(self._blnet_id)

        if sensor_data is None:
            _LOGGER.warning(f"No data received for switch {self._blnet_id}")
            return

        self._friendly_name = sensor_data.get('friendly_name')
        self._state = STATE_ON if sensor_data.get('value') == "EIN" else STATE_OFF
        self._icon = 'mdi:flash' if self._state == STATE_ON else 'mdi:flash-off'
        self._mode = sensor_data.get('mode')

        self._last_updated = last_blnet_update
        self._assumed_state = False

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the device."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            MODE: self._mode,
            FRIENDLY_NAME: self._friendly_name
        }

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.info(f"Turning on switch {self._blnet_id}")
        self.communication.turn_on(self._id)
        self._state = STATE_ON
        self._assumed_state = True

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.info(f"Turning off switch {self._blnet_id}")
        self.communication.turn_off(self._id)
        self._state = STATE_OFF
        self._assumed_state = True

    @property
    def assumed_state(self) -> bool:
        return self._assumed_state


class BLNETModeSwitch(SwitchEntity):
    """
    Representation of a switch that toggles the operation mode
    of a digital output of the UVR1611. On means automated.
    """

    def __init__(self, switch_id, blnet_id, comm):
        """Initialize the switch."""
        self._blnet_id = blnet_id
        self._id = switch_id
        self.communication = comm
        self._name = '{} automated'.format(blnet_id)
        self._friendly_name = blnet_id
        self._unique_id = f"{switch_id}_{blnet_id}_mode"  # Eindeutige ID für Modusschalter
        self._state = STATE_UNKNOWN
        self._activated = self._state
        self._assumed_state = True
        self._icon = None
        self._last_updated = None

    @property
    def unique_id(self):
        """Return a unique ID for this mode switch."""
        return self._unique_id

    def update(self):
        """Get the latest data from communication device."""
        last_blnet_update = self.communication.last_updated()

        if last_blnet_update == self._last_updated:
            return

        sensor_data = self.communication.data.get(self._blnet_id)

        if sensor_data is None:
            _LOGGER.warning(f"No data received for mode switch {self._blnet_id}")
            return

        self._friendly_name = "{} automated".format(sensor_data.get('friendly_name'))
        self._state = STATE_ON if sensor_data.get('mode') != 'HAND' else STATE_OFF
        self._icon = 'mdi:cog' if self._state == STATE_ON else 'mdi:cog-off'
        self._activated = sensor_data.get('value')

        self._last_updated = last_blnet_update
        self._assumed_state = False

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the device."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            FRIENDLY_NAME: self._friendly_name
        }

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.info(f"Setting mode to automatic for switch {self._blnet_id}")
        self.communication.turn_auto(self._id)
        self._state = STATE_ON
        self._assumed_state = True

    def turn_off(self, **kwargs):
        """Turn the device off, enabling manual control."""
        _LOGGER.info(f"Setting mode to manual for switch {self._blnet_id}")
        if self._activated == "EIN":
            self.communication.turn_on(self._id)
        else:
            self.communication.turn_off(self._id)
        self._state = STATE_OFF
        self._assumed_state = True

    @property
    def assumed_state(self) -> bool:
        return self._assumed_state
