"""Data model for Cubes, including the data about where in the spreadsheet to save them."""

from typing import Sequence
from collections import UserDict
from json import JSONEncoder

class CubeSubmissionInfo:
    """The set of spreadsheet locations to which
    to save information about drafts of this cube."""

    def __init__(self, spreadsheet_id: str, maindeck: str, sideboard: str, draftlog: str):
        self.spreadsheet_id = spreadsheet_id
        self.maindeck = maindeck
        self.sideboard = sideboard
        self.draftlog = draftlog
    @classmethod
    def from_json(cls, data: dict):
        """Given a cubes.json file, creates a new CubeSubmissionInfo object from that json file."""
        return cls(**data)

class Cube:
    """A list of cards in a cube,
    Along with directions about which speadsheets locations to save to."""
    def __init__(self, cardList: Sequence[str], submission_info: CubeSubmissionInfo):
        self.cards = cardList
        self.submission_info = submission_info
    def contains(self, card_list: Sequence[str]):
        """Does this cube have all the cards in card_list?"""
        draftable_cards = set(card_list) - set(["Plains", "Island", "Swamp", "Mountain", "Forest"])
        return draftable_cards.issubset(set(self.cards))

    @classmethod
    def from_json(cls, data: dict):
        """Given a cubes.json file, creates a new Cube object from that json file."""
        return cls(data["cards"], CubeSubmissionInfo.from_json(data["submission_info"]))

class CubeList(UserDict):
    """A dictionary of cubes organized by name.
    This class extends UserDict, which means it's literally a dict
    (and can do everything a dict can do)."""
    def get_matches(self, card_list: Sequence[str]):
        """Given a list of cards, returns a list of the names of cubes
        in this CubeList that contain all the cards in the list."""
        return [cubeName for cubeName, cube in self.items()
                if cube.contains(card_list)]

    @classmethod
    def from_json(cls, data: dict):
        """Given a cubes.json file, creates a new CubeList object from that json file."""
        return cls({k: Cube.from_json(v) for k, v in data.items()})

class CubeListEncoder(JSONEncoder):
    """JSON encoder for a CubeList."""
    def default(self, o):
        return o.__dict__

if __name__ == "__main__":
    import json
    CUBE_LIST = None
    with open("config/cubes.json", 'r') as cubes_file:
        CUBE_LIST = CubeList.from_json(json.load(cubes_file))
    print(CUBE_LIST.get_matches(["Shock"]))
    print(CUBE_LIST.get_matches(["Imperial Aerosaur"]))
    