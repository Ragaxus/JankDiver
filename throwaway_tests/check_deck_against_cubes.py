import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 

from models.cubelist import CubeList
from draftdata import DraftData

import json
import chardet
import datetime
import save_to_google_sheet

with open("config/cubes.json", 'r') as cubes_file:
    CUBE_LIST = CubeList.from_json(json.load(cubes_file))

DECK_FILE_PATH = r"C:\Users\sgold\Downloads\Uusi_tekstiasiakirja.txt"
deck_bytes = open(DECK_FILE_PATH, 'rb').read()
deck = deck_bytes.decode(chardet.detect(deck_bytes)["encoding"])     
deck_data = DraftData.create(deck, "Deck Submitter", datetime.datetime.now())
candidates = deck_data.match_cubes(CUBE_LIST)
print(deck_data.card_list())
print(candidates)
#saver = save_to_google_sheet.GoogleDraftDataSaver()
#deck_data.save_to_spreadsheet(saver,CUBE_LIST[candidates[0]])
