"""Cube list maintenance utilities."""
import json
import requests
from models.cubelist import CubeList, CubeListEncoder

def update_cube_cards(cube_name: str):
    """Updates a given cube list
    with the current contents of the CubeCobra list."""
    with open("config/cubes.json", 'r') as cubes_file:
        cube_list = CubeList.from_json(json.load(cubes_file))
        if not cube_name in cube_list:
            print(f"Couldn't find list {cube_name}")
            return
        cube_cobra_id = cube_list[cube_name].cube_cobra_id
    req = requests.get(f"https://cubecobra.com/cube/download/plaintext/{cube_cobra_id}")
    cube_list[cube_name].cards = req.text.splitlines()
    with open("config/cubes.json", 'w') as cubes_file:
        cubes_file.write(json.dumps(cube_list.__dict__["data"],
                                    cls=CubeListEncoder,
                                    indent=4, separators=(',', ': ')))

# Run in interpreter at top-level dir:
# from utils.update_cube_cards import update_cube_cards
# update_cube_cards("Jank Diver Unlimited Cube")
# update_cube_cards("Jank Diver Peasant Cube")
    