"""Data model for Cubes, including the data about where in the spreadsheet to save them."""

from typing import Sequence
from collections import UserDict

class CubeSubmissionInfo:
    """The set of spreadsheet locations to which
    to save information about drafts of this cube."""

    def __init__(self, maindeck: str, sideboard: str, draftlogs: str):
        self.maindeck = maindeck
        self.sideboard = sideboard
        self.draftlog = draftlogs
    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

class Cube:
    def __init__(self, cardList: Sequence[str], subinfo: CubeSubmissionInfo):
        self.cards = cardList
        self.subinfo = subinfo
    def contains(self, card_list: Sequence[str]):
        """Does this cube have all the cards in card_list?"""
        return set(card_list).issubset(set(self.cards))

    @classmethod
    def from_json(cls, data: dict):
        return cls(data["cards"], CubeSubmissionInfo.from_json(data["submissionInfo"]))

class CubeList(UserDict):

    def get_matches(self, card_list: Sequence[str]):
        return [cubeName for cubeName, cube in self.items() 
                if cube.contains(card_list)]
    
    @classmethod
    def from_json(cls, data: dict):
        return cls({k: Cube.from_json(v) for k, v in data.items()})

if __name__ == "__main__":
    import json
    cube_list = None
    with open("config/cubes.json", 'r') as cubes_file:
        cube_list = CubeList.from_json(json.load(cubes_file))
    print(cube_list.get_matches(["Shock"]))