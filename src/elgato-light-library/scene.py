"""
TODO: write this doc string

Tasks:
[TODO] clean up project structure
[TODO] make type checks raise errors instead of using asserts
[TODO] add documentation
"""
class Scene:
    """
    Store and manipulate scenes at a high level.

    {
        'numberOfLights': 1,
        'lights': [
            {'on': 1,
            'id': 'com.corsair.cc.scene.sunrise',
            'name': 'Sunrise',
            'brightness': 100.0,
            'numberOfSceneElements': 4,
            'scene': []
            }
        ]
    }
    """

    def __init__(self, input_scene=[]):
        """Init the scene."""
        for item in input_scene:
            assert type(item) is dict, f"TypeError: item: {item} is type: {type(item)} not type: dict"
        self.data = input_scene

    def add_scene(self, hue, saturation, brightness, durationMs, transitionMs):
        """Add an item to the end of the list."""
        self.data.append(
            {'hue': hue,
             'saturation': saturation,
             'brightness': brightness,
             'durationMs': durationMs,
             'transitionMs': transitionMs})

    def insert_scene(self,
                     index,
                     hue,
                     saturation,
                     brightness,
                     durationMs,
                     transitionMs):
        """Insert a scene in the list."""
        self.data.insert(
            index,
            {'hue': hue,
             'saturation': saturation,
             'brightness': brightness,
             'durationMs': durationMs,
             'transitionMs': transitionMs})

    def delete_scene(self, index=0):
        """Remove a scene from the list."""
        return self.data.pop(index)

    def print_scenes(self):
        """Display every scene in the loop."""
        for scene in self.data:
            print(scene)

    def length(self):
        """Return the duration of the scene."""
        scene_length = 0
        for scene in self.data['scene']:
            scene_length += scene['durationMs']
            scene_length += scene['transitionMs']
        return scene_length
