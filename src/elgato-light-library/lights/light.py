"""
Light class that contains common elements of all lights

all other light classes (Keylight, Lightstrip, etc) should inherit this
"""
import requests
import json
import logging
from lightstrip import LightStrip
from keylight import KeyLight

class Light:
    # available subclasses that have custom features
    _subclasses = {'Strip': LightStrip, 'Key': KeyLight}
    def __init__(self, addr, port, name="") -> None:
        """
        All of the lights share these attributes
        """
        self.type = type
        self.addr = addr
        self.port = port
        self.name = name
        self.full_addr = self.addr + ':' + str(self.port)
        self.get_strip_data()  # fill in the data/info/settings of the light
        self.get_strip_info()
        self.get_strip_settings()
        self.type = self.info['productName']
    
    def detect_type(addr, port, name="") -> KeyLight | LightStrip:
        """
        Given an address, figure out which subclass should be made and return that subclass
        """
        log = logging.getLogger(__name__)
        info = requests.get(f'http://{addr}:{port}/elgato/accessory-info',
            verify=False).json()
        light_type = info['productName']
        if light_type in Light._subclasses:
            return Light._subclasses[light_type](addr, port, name=name)
        else:
            log.warning(f"A subclass was not found for product: {light_type}")
            return Light(addr, port, name=name)

    def get_strip_data(self):
        """
        Send a get request to the full addr.

            format:
            http://<IP>:<port>/elgato/lights
        """
        log = logging.getLogger(__name__)
        self.data = requests.get(
            'http://' + self.full_addr + '/elgato/lights',
            verify=False).json()
        log.info(f"recieved data on /elgato/lights:\n{self.data}")
        return self.data

    def get_strip_info(self):
        """Send a get request to the light."""
        log = logging.getLogger(__name__)
        self.info = requests.get(
            'http://' + self.full_addr + '/elgato/accessory-info',
            verify=False).json()
        log.info(f"recieved data on /elgato/accessory-info:\n{self.info}")
        return self.info

    def get_strip_settings(self):
        """Get the strip's settings."""
        log = logging.getLogger(__name__)
        self.settings = requests.get(
            'http://' + self.full_addr + '/elgato/lights/settings',
            verify=False).json()
        log.info(f"recieved data on /elgato/lights/settings:\n{self.settings}")
        return self.settings

    def set_strip_data(self) -> bool:
        """
        Send a put request to update the light data.

        Returns True if successful
        TODO: investigate if sending the entire JSON is necessary or if we can just send the things that need to be changed
        TODO: investigate just sending self.data
        """
        log = logging.getLogger(__name__)
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/lights',
                data=json.dumps(self.data))
            # if the request was accepted, modify self.data
            if r.status_code == requests.codes.ok:
                return True
        except Exception as e:
            log.warning(f"Error encountered when setting strip data for {self.full_addr}.\n{e}")
        return False

    def set_strip_settings(self) -> bool:
        """
        Send a put request to update the light settings.

        Returns True on success
        """
        log = logging.getLogger(__name__)
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/lights/settings',
                data=json.dumps(self.settings))
            if r.status_code == requests.codes.ok:
                return True
        except Exception as e:
            log.warning(f"Error encountered when setting strip settings for {self.full_addr}.\n{e}")
        return False

    def set_strip_info(self) -> bool:
        """Set the strip info."""
        log = logging.getLogger(__name__)
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/accessory-info',
                data=json.dumps(self.info))
            if r.status_code == requests.codes.ok:
                return True
            print(r.text)
        except Exception as e:
            log.warning(f"Error encountered when setting strip info for {self.full_addr}.\n{e}")
        return False