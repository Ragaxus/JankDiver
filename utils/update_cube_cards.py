"""Cube list maintenance utilities."""
import json
import requests
from models.cubelist import CubeList, CubeListEncoder

def update_cube_cards(cubecobra_id: str, cube_name: str):
    """Given a CubeCobra id, updates a given list
    with the current contents of the CubeCobra list."""
    req = requests.get(f"https://cubecobra.com/cube/download/plaintext/{cubecobra_id}")
    #print(req.text)
    with open("config/cubes.json", 'r') as cubes_file:
        cube_list = CubeList.from_json(json.load(cubes_file))
    cube_list[cube_name].cards = req.text.splitlines()
    with open("config/cubes.json", 'w') as cubes_file:
        cubes_file.write(json.dumps(cube_list.__dict__["data"],
                                    cls=CubeListEncoder,
                                    indent=4, separators=(',', ': ')))

# Run in interpreter at top-level dir:
# from utils.update_cube_cards import update_cube_cards
# update_cube_cards("5f3e8c827440640ffe679a5e", "Arena Rares Cube")
    