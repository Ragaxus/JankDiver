"""Cube list maintenance utilities."""
import json
import requests
from models.cubelist import CubeList, CubeListEncoder

def update_cube_cards(cube_file_path: str = "config/cubes.json", cube_name: str=None):
    """Updates a given cube list
    with the current contents of the CubeCobra list."""
    with open(cube_file_path, 'r') as cubes_file:
        cube_list = CubeList.from_json(json.load(cubes_file))
        if cube_name: 
            update_cards_for_cube(cube_list, cube_name)
        else:
            for cube_name in cube_list:
                update_cards_for_cube(cube_list, cube_name)

    with open(cube_file_path, 'w') as cubes_file:
        cubes_file.write(json.dumps(cube_list.__dict__["data"],
                                    cls=CubeListEncoder,
                                    indent=4, separators=(',', ': ')))

def update_cards_for_cube(cube_list: CubeList, cube_name: str): 
    if not cube_name in cube_list:
        print(f"Couldn't find list {cube_name}")
        return
    cube_cobra_id = cube_list[cube_name].cube_cobra_id
    req = requests.get(f"https://cubecobra.com/cube/download/plaintext/{cube_cobra_id}")
    cube_list[cube_name].cards = req.text.splitlines()