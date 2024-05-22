"""
Library to interact with Elgato Lights

this file is full of helper functions and general things
"""
import socket
import logging
from time import sleep, time
from lights.lightstrip import LightStrip
from lights.light import Light
NUM_PORTS = 65536
ELGATO_PORT = 9123

class ServiceListener:
    """Listener for Zeroconf."""

    def __init__(self):
        """Init the listener."""
        self.services = []
        # useful if we want to leave the listener running by having future lists of lights just reference this one
        # so when this list is updated, the others should be updated as well
        self.lights = dict()

    def get_services(self):
        """Return the services."""
        return self.services
    def get_lights(self) -> dict:
        """
        Return the lights that are in the network
        Lights are stored in a dictionary that splits them by type
        """
        return self.lights

    def remove_service(self, zeroconf, type, name):
        """Remove a service."""
        info = zeroconf.get_service_info(type, name)
        self.services.remove(info)

    def update_service(self, zeroconf, type, name):
        """
        Update a service.
        
        I don't think this one will get called
        """
        log = logging.getLogger(__name__)
        log.warning("update service was called but is not handled")

    def add_service(self, zeroconf, type, name):
        """Called when a new thing is found"""
        log = logging.getLogger(__name__)
        info = zeroconf.get_service_info(type, name)
        self.services.append(info)
        # add the light
        for addr in info.addresses:
            try:
                prospect_light = Light.detect_type(socket.inet_ntoa(addr), info.port, info.get_name())
                if prospect_light.info['productName'] not in self.lights:
                    self.lights[prospect_light.info['productName']] = []
                logging.info(f"\tadding {prospect_light.info['productName']}: {prospect_light.info['displayName']}")
                self.lights[prospect_light.info['productName']].append(prospect_light)
            except Exception as e:
                log.warning("Failed to connect to light")
                log.warning(f"Caught exception:\n{e}")
                



def find_light_strips_zeroconf(service_type='_elg._tcp.local.', TIMEOUT=15) -> dict:
        """
        Use multicast to find all elgato light strips.
        Returns a dictionary where lights are separated by productName

        Parameters:
            the service type to search
            the timeout period to wait until you stop searching

        NOTE: this is not a rolling admission
        """
        # NOTE: need to put this in a try/except statement
        # just in case they have not imported zeroconf
        log = logging.getLogger(__name__)
        try:
            import zeroconf
        except Exception:
            log.warning("please install zeroconf to use this method")
            log.warning("$ pip install zeroconf")
            return {}

        lightstrips = dict()

        zc = zeroconf.Zeroconf()
        listener = ServiceListener()
        browser = zeroconf.ServiceBrowser(zc, service_type, listener)
        sleep(TIMEOUT)
        browser.cancel()
        return listener.get_lights()

def start_rolling_admission_zeroconf(
        service_type='_elg._tcp.local.') -> tuple:
    """
    Start a rolling admission for Zeroconf.
    Returns the dictionary of lights and the ServiceBrowser (which will need to be canceled later)
    """
    log = logging.getLogger(__name__)
    try:
        import zeroconf
    except Exception:
        log.warning("please install zeroconf to use this method")
        log.warning("$ pip install zeroconf")
        return (dict(), None)

    zc = zeroconf.Zeroconf()
    listener = ServiceListener()
    browser = zeroconf.ServiceBrowser(zc, service_type, listener)
    return (listener.get_lights(), browser)

    

def find_light_strips_manual(strips) -> dict:
    """
    Given a list of addr, port combinations, creates a dictionary of lights from them
    """
    log = logging.getLogger(__name__)
    lights = {}
    for (addr, port) in strips:
        try:
            prospect_light = Light.detect_type(addr, port)
            if prospect_light.info['productName'] not in lights:
                    lights[prospect_light.info['productName']] = []
            logging.info(f"\tadding {prospect_light.info['productName']}: {prospect_light.info['displayName']}")
            lights[prospect_light.info['productName']].append(prospect_light)
        except Exception as e:
            log.warning(f"Failed to add light {addr}:{port}")
            log.warning(f"Caught exception: {e}")
    return lights