"""class that creates and holds draft data (decks/draft logs) and some properties"""

import re
import time
import json


class DraftData:
    """A parsed file from the #txt channel - either a deck, or a draft log."""

    def __init__(self, data_stream, user, timestamp):
        self.type = ""       #once evaluated, will provide if this is a deck, a draft log, or other
        self.user = user     #holds the user from whom the data was scraped
        self.data = ""       #holds the parced data
        self.timestamp = str(timestamp)
        self.number_of_players = 0

        self.parse(data_stream)


    def parse_deck(self, deck_string):
        """Given a deck as a string, returns a list of card names in the maindeck.
        Parameters
        ----------
        deck_string : string
        A whole deck file as a string.
        """

        cards = [[], []]
        card_regex = re.compile(r'1 ([^\(]+)')
        i = 0
        for line in [l.rstrip() for l in deck_string.split('\n')]:
            if line == "Sideboard":
                i = 1
            if line.startswith('1 '):
                cards[i].append(card_regex.match(line).group(1).rstrip())
        self.data = cards

    def parse_draft(self, draft_log_string):
        """Given a draft log as a string, returns players and the picked cards in pick order
        Parameters
        ----------
        draft_log_string : string
        a downloaded draft log from mtgadraft.herokuapp.com/
        """
        draft_log = json.loads(draft_log_string)

        timestamp_local_time = time.localtime(int(draft_log["time"])/1000)
        self.timestamp = time.strftime('%Y-%m-%d %H:%M', timestamp_local_time)

        user_representations = []
        number_of_players = 0
        for _, user in draft_log["users"].items():
            try:
                name = user["userName"]
                picks = DraftData(user["exportString"], "", "").data[0]
                user_representation = {"name":user["userName"], "picks":picks}
                user_representations.append(user_representation)
                number_of_players += 1
            except DraftDataParseError as inner_ex:
                inner_ex.message += f" This occurred while parsing a draft log, \
                in the exportString for user {name}."
                raise
        self.data = user_representations
        self.number_of_players = number_of_players



    def parse(self, input_string):
        """Given an input string, looks at first character to see if it's a draft log or deck,
        then runs the right fuction to create data.
        Parameters
        ----------
        file : string
        contents of a file downloaded from discord dump channel
        """

        if input_string[0] == "{":
            self.type = 'draft'
            self.parse_draft(input_string)
        elif input_string[0] == "D":
            self.type = 'deck'
            self.parse_deck(input_string)
        else:
            self.type = 'error'
            raise DraftDataParseError(input_string[0])

class DraftDataParseError(Exception):
    """Raised when a DraftData doesn't recognize the first character of a given input.
    first_char : string
    The character we failed to parse."""
    def __init__(self, first_char):
        super().__init__()
        self.first_char = first_char
        self.message = f"Could not determine data type from beginning character {first_char}."

if __name__ == "__main__":
    import chardet

    DECK_FILE_PATH = r"C:\Users\sgold\Documents\Arena Cube Drafts\take_me_to_church.txt"
    LOG_FILE_PATH = r"C:\Users\sgold\Downloads\DraftLog_APCd.txt"

    deck_bytes = open(DECK_FILE_PATH, 'rb').read()
    deck = deck_bytes.decode(chardet.detect(deck_bytes)["encoding"])
    deck_data = DraftData(deck, "Deck Submitter", 1)
    print(deck_data.data)
    log_bytes = open(LOG_FILE_PATH, 'rb').read()
    log = log_bytes.decode(chardet.detect(deck_bytes)["encoding"])
    log_data = DraftData(log, "Log Submitter", 2)
    print(log_data.data)
