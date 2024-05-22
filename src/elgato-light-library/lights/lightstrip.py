from scene import Scene
from light import Light
class LightStrip(Light):
    """
    LightStrip language.
    data: json object,  can be retrieved by making a get request to
    light.full_addr/elgato/lights
            always has two keys:
                'numberOfLights': int
                'lights'         : list
            each item in 'lights' is a dict that always has two keys:
                'on'            : int
                'brightness'    : int
            however, the lights have two (known) modes: individual colors, and scenes
                for individual colors, the dictionary additionally has 'hue' and
                'saturation' keys (both are of type `float`)
                for scenes:
                    'id'                        : str
                    'name'                      : str
                    'numberOfSceneElements'     : int
                    'scene'                     : list
                each 'scene' is a list of dictionaries containing the following keys:
                    'hue'                       : float
                    'saturation'                : float
                    'brightness'                : float
                    'durationMs'                : int
                    'transitionMs'              : int
            when there is a 'scene', the light loops through each item in the scene
    """

    def __init__(self, addr, port, name=""):
        """Initialize the light."""
        super().__init__('lightstrip', addr, port, name)
        self.is_scene = False
        if 'scene' in self.data['lights'][0]:
            self.is_scene = True
            self.scene = Scene(self.data['lights'][0]['scene'])
        elif 'name' in self.data['lights'][0]:
            self.is_scene = True
  
    def from_light(light: Light):
        """Create a lightstrip from a Light object"""
        return LightStrip(light.addr, light.port, light.name)
    
    def get_strip_color(self):
        """
        Return the color of the light.

            If the light is not set to a specific color
            (i.e. when it is in a scene) then the tuple is empty
        """
        try:
            light_color = self.get_strip_data()['lights'][0]
            return (
                light_color['on'],
                light_color['hue'],
                light_color['saturation'],
                light_color['brightness'])
        except Exception:
            return ()  # the light strip is not set to a static color

    def update_color(self, on, hue, saturation, brightness) -> bool:
        """User friendly way to interact with json data to change the color."""
        self.data = {
            'numberOfLights': 1,
            'lights': [
                {'on': on,
                 'hue': hue,
                 'saturation': saturation,
                 'brightness': brightness}
            ]
        }
        return self.set_strip_data(self.data)

    def update_scene_data(self, scene,
                          scene_name="transition-scene",
                          scene_id="",
                          brightness: float = 100.0):
        """Update just the scene data."""
        print("updating scene data")
        if not self.is_scene:
            print("light strip is not currently assigned to a scene, autogenerating")
            self.make_scene(scene_name, scene_id)

        if not scene:
            print("assigining scene by name")
            self.data['lights'][0]['name'] = scene_name
            if scene_id:
                print("also assigining scene by id")
                self.data['lights'][0]['id'] = scene_id
            print("purging scene data")
            if not self.data['lights'][0].pop('scene'):
                print("scene was not specified")
            if not self.data['lights'][0].pop('numberOfSceneElements'):
                print("number of scene elements was not specified")
        else:
            print("scene:", scene)
            assert type(scene) is Scene, "scene is not a list"
            self.data['lights'][0]['scene'] = scene.data
            self.data['lights'][0]['numberOfSceneElements'] = len(scene.data)

    def make_scene(self,
                   name: str,
                   scene_id: str,
                   brightness: float = 100.0):
        """Create a scene."""
        # print("making the light a scene")
        self.data = {
            'numberOfLights': 1,
            'lights': [
                {'on': 1,
                 'id': scene_id,
                 'name': name,
                 'brightness': brightness,
                 'numberOfSceneElements': 0,
                 'scene': []
                 }
            ]
        }
        self.is_scene = True
        # if you do not specify an empty scene,
        # it might copy old scene data... annoying
        self.scene = Scene([])

    def transition_start(self,
                         colors: list,
                         name='transition-scene',
                         scene_id='transition-scene-id') -> tuple[int, bool]:
        """
        Non-blocking for running multiple scenes.

        returns how long to wait
        TODO: add ability to transition to a new scene

        TODO: see if scenes are callable by name
        TODO: make asyncronous function to replace this one

        TODO: see if you can pick a different way to cycle between colors in a scene
        """
        # print("---------transition starting")
        self.make_scene(name, scene_id, 100)
        wait_time_ms = 0
        # check if the light has already been set to a color,
        # and if it has, make that color the start of the transition scene
        if current_color := self.get_strip_color():
            _, hue, saturation, brightness = current_color
            self.scene.add_scene(
                hue,
                saturation,
                brightness,
                colors[0][3],
                colors[0][4])
            wait_time_ms += colors[0][4] + colors[0][3]
        # add the colors in the new scene
        for color in colors:
            hue, saturation, brightness, durationMs, transitionMs = color
            self.scene.add_scene(
                hue,
                saturation,
                brightness,
                durationMs,
                transitionMs)
            wait_time_ms += durationMs + transitionMs
        # update the light with the new scene
        self.update_scene_data(self.scene, scene_name=name, scene_id=scene_id)
        self.set_strip_data(self.data)
        # return the wait time
        return (wait_time_ms - colors[-1][3] - colors[-1][4]) / 1000

    def transition_end(self,
                       end_scene: list,
                       end_scene_name='end-scene',
                       end_scene_id='end-scene-id') -> bool:
        """
        End the transition scene and replace it with a new scene.

        used after transition_start is called
        sets the scene to the end_color
        almost identical to lightStrip.update_color - primarily used to keep code readable
        """
        # print("--------transition ending")
        assert type(end_scene) is list, f"TypeError: {end_scene} is type: {type(end_scene)} not type: list"
        # print("scene passed into transition_end:", end_scene)
        if not end_scene:  # TODO: make this cleaner
            # print("missing end scene, using scene name")
            self.update_scene_data(None, scene_name=end_scene_name, scene_id=end_scene_id)
            return self.set_strip_data(self.data)
        elif len(end_scene) == 1:
            # print("setting light to single color")
            hue, saturation, brightness, _, _ = end_scene[0]
            is_on = 1 if brightness > 0 else 0
            return self.update_color(is_on, hue, saturation, brightness)
        else:
            # the end scene is an actual scene
            # TODO: make scene brightness variable
            # print("setting transition to end on a scene")
            self.make_scene(end_scene_name, end_scene_id, 100)
            self.scene = Scene([])
            for item in end_scene:
                hue, saturation, brightness, durationMs, transitionMs = item
                self.scene.add_scene(
                    hue, saturation, brightness, durationMs, transitionMs)
            self.update_scene_data(
                self.scene, scene_name=end_scene_name, scene_id=end_scene_id)
            return self.set_strip_data(self.data)