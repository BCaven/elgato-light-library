"""
Tasks:
[TODO] write a docstring
[TODO] transition to multicast instead of sending instructions to each light individually
[TODO] general clean this up
[TODO] handle dictionary that contains multiple light types instead of single list of LightStrips
"""
from _core import find_light_strips_zeroconf, start_rolling_admission_zeroconf
import logging
from time import time
class Room:
    """
    Collection of lights that are on the same network.
    
    Most users will probably only interact with rooms
    """
    log = logging.getLogger(__name__)
    def __init__(self, lights: list = []):
        """Init the room."""
        assert type(lights) is list, f"TypeError: {lights} is type: {type(lights)} not type: list"
        self.lights = lights

    def setup(self, service_type='_elg._tcp.local.', timeout=15):
        """
        Find all the lights.
        
        To use a rolling admission set timeout=None
        """
        if timeout:
            self.lights = find_light_strips_zeroconf(
                service_type, timeout)
            self.browser = None
        else:
            l, browser = start_rolling_admission_zeroconf(service_type)
            self.lights = l
            self.browser = browser
        return True if self.lights else False

    def room_color(self, on, hue, saturation, brightness):
        """Set color for the whole room."""
        for light in self.lights:
            light.update_color(on, hue, saturation, brightness)

    def room_scene(self, scene):
        """Set all lights in the room to a specific scene."""
        # TODO: write this method

    def room_transition(self,
                        colors: list,
                        name='transition-scene',
                        scene_id='transition-scene-id',
                        end_scene: list = [],
                        end_scene_name="end-scene",
                        end_scene_id="end-scene-id"):
        """
        Non blocking transition for all room lights.

        TODO: return status of https request
        """
        rescan = False
        if not colors:
            Room.log.warning("Cannot transition to an empty scene")
            return

        times = []
        for light in self.lights:
            times.append((
                light,
                light.transition_start(colors, name, scene_id),
                time()))

        while times:
            # TODO: check if this can be optimized to use less
            light, sleep_time, start_time = times.pop(0)
            # light, transition_start_output, start_time = times.pop(0)
            # print(transition_start_output)
            # sleep_time, success = transition_start_output
            if sleep_time + start_time < time():
                transition_status = light.transition_end(
                    end_scene, end_scene_name, end_scene_id)
                rescan = rescan or not transition_status
            else:
                times.append((light, sleep_time, start_time))
        if rescan and not self.browser:
            Room.log.info("Rescanning because a light failed - this is only useful when not using rolling admission")
            self.setup()
        elif rescan:
            Room.log.warning("A transition failed but rolling admission is active")
        return not rescan

    def light_transition(self,
                         addr: str,
                         colors: list,
                         name='transition-scene',
                         scene_id='transition-scene-id',
                         end_scene: list = [],
                         end_scene_name="end-scene",
                         end_scene_id="end-scene-id"):
        """Non blocking transition for specific light in the room."""
        rescan = False
        if not colors:
            # print("cannot transition an empty scene")
            return
        if not end_scene:
            end_scene = colors[-1]
        times = []
        for light in self.lights:
            if light.addr == addr:
                times.append((
                    light,
                    light.transition_start(colors, name, scene_id),
                    time()))

        while times:
            light, transition_start_output, start_time = times.pop(0)
            sleep_time, success = transition_start_output
            if sleep_time + start_time < time():
                rescan = rescan or light.transition_end(
                        end_scene, end_scene_name, end_scene_id)
            else:
                times.append((light, sleep_time, start_time))

        return
