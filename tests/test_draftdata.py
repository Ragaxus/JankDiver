import datetime
from draftdata import DraftData
import chardet

def make_draft_data_from_file(file_name: str):
    data_bytes = open(file_name, 'rb').read()
    data = data_bytes.decode(chardet.detect(data_bytes)["encoding"])
    return DraftData.create(data, "Submitter", datetime.datetime.now())

if __name__ == "__main__":
    log = make_draft_data_from_file("sample_DraftLog.json")
    print(log.deck_lists)
