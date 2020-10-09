"""class that creates and holds draft data (decks/draft logs) and some properties"""

import re
import datetime
import json
from save_to_google_sheet import GoogleDraftDataSaver
from models.cubelist import CubeList, Cube


class DraftData:
    """A parsed file from the #txt channel - either a deck, or a draft log."""
    @staticmethod
    def create(input_string, user, timestamp):
        """Given an input string, looks at first character to see if it's a draft log or deck,
        then returns the proper implementer of DraftData
        Parameters
        ----------
        file : string
        contents of a file downloaded from discord dump channel
        """
        if input_string[0] in ["C", "D"]: #To account for companions
            return DeckList(input_string, user, timestamp)
        elif input_string[0] == "{":
            return DraftLog(input_string, user)
        else:
            raise DraftDataParseError(input_string[0])

    def __init__(self):
        self.timestamp = ""

    def set_timestamp(self, timestamp: datetime):
        """Sets the timestamps for the draft data using a standard format."""
        self.timestamp = timestamp.strftime('%Y-%m-%d %H:%M')

    #Abstract class method stubs -- don't change these
    def parse(self, data: str):
        """Abstract class method stub"""
        raise NotImplementedError
    def match_cubes(self, cube_list: CubeList):
        """Abstract class method stub"""
        raise NotImplementedError
    def save_to_spreadsheet(self, service: GoogleDraftDataSaver, cube: Cube):
        """Abstract class method stub"""
        raise NotImplementedError

class DeckList(DraftData):
    """A parsed deck from a file submitted in the Discord channel."""
    def __init__(self, data_stream, user, timestamp):
        super().__init__()

        self.user = user
        self.set_timestamp(timestamp)

        self.maindeck = []
        self.sideboard = []
        self.companion = ""
        self.commander = ""
        self.parse(data_stream)

    def parse(self, data: str):
        """Given a deck as a string, returns a list of card names in the maindeck.
        Parameters
        ----------
        data : string
        A whole deck file as a string.
        """

        card_regex = re.compile(r'1 ([^\(]+)')

        def add_card_to_maindeck(self, card_name):
            self.maindeck.append(card_name)

        def add_card_to_sideboard(self, card_name):
            if (card_name != self.companion) and (card_name != self.commander):
                self.sideboard.append(card_name)

        def add_card_as_companion(self, card_name):
            self.companion = card_name

        def add_card_as_commander(self, card_name):
            self.commander = card_name

        add_methods = {
            0: add_card_to_maindeck,
            1: add_card_to_sideboard,
            2: add_card_as_companion,
            3: add_card_as_commander
        }

        for line in [l.rstrip() for l in data.split('\n')]:
            if line == "Deck":
                i = 0
            elif line == "Sideboard":
                i = 1
            elif line == "Companion":
                i = 2
            elif line == "Commander":
                i = 3
            elif line.startswith('1 '):
                card_name = card_regex.match(line).group(1).rstrip().replace("////", "//")
                add_methods[i](self, card_name)

    def cards_in_deck(self):
        """Returns a list of all the cards in the deck."""
        cards_in_deck = self.maindeck + self.sideboard
        if self.companion:
            cards_in_deck.append(self.companion)
        if self.commander:
            cards_in_deck.append(self.commander)
        return cards_in_deck

    def match_cubes(self, cube_list: CubeList):
        return cube_list.get_matches(self.cards_in_deck())

    def save_to_spreadsheet(self, service: GoogleDraftDataSaver, cube: Cube):
        # maindeck
        # placeholders for colors and record
        # Leaving commanders out for now since no cube that we manage uses them
        deck_metadata = [self.user, "", "", self.companion, self.timestamp]
        cell_data = deck_metadata + self.maindeck
        service.write_to_sheet([cell_data],
                               cube.submission_info.spreadsheet_id,
                               cube.submission_info.maindeck)

        #sideboard
        #(no placeholders - no need to fill in that info twice)
        sb_metadata = [self.user, self.timestamp]
        cell_data = sb_metadata + self.sideboard
        service.write_to_sheet([cell_data],
                               cube.submission_info.spreadsheet_id,
                               cube.submission_info.sideboard)

class DraftLog(DraftData):
    """A parsed draft log from a file submitted in the Discord channel."""
    def __init__(self, data_stream, user):
        super().__init__()
        self.user = user     #holds the user from whom the data was scraped
        self.data = ""       #holds the parsed data
        self.number_of_players = 0

        self.parse(data_stream)

    def parse(self, data: str):
        """Given a draft log as a string, returns players and the picked cards in pick order
        Parameters
        ----------
        data : string
        a downloaded draft log from mtgadraft.herokuapp.com/
        """
        draft_log = json.loads(data)

        timestamp = datetime.datetime.fromtimestamp(int(draft_log["time"])*.001)
        self.set_timestamp(timestamp)

        user_representations = []
        number_of_players = 0
        for _, user in draft_log["users"].items():
            try:
                name = user["userName"]
                picks = DeckList(user["exportString"], "", timestamp).maindeck
                user_representation = {"name":user["userName"], "picks":picks}
                user_representations.append(user_representation)
                number_of_players += 1
            except DraftDataParseError as inner_ex:
                inner_ex.message += f" This occurred while parsing a draft log, \
                in the exportString for user {name}."
                raise
        self.data = user_representations
        self.number_of_players = number_of_players

    def match_cubes(self, cube_list: CubeList):
        card_list = [card for player in self.data for card in player["picks"]]
        return cube_list.get_matches(card_list)

    def save_to_spreadsheet(self, service: GoogleDraftDataSaver, cube: Cube):
        #write the draft seats
        cell_values = []
        for user_representation in self.data:
            cell_values.append([self.timestamp, user_representation["name"]] +
                               user_representation["picks"])
        cell_values.append([""])
        service.write_to_sheet(cell_values,
                               cube.submission_info.spreadsheet_id,
                               cube.submission_info.draftlog)

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
    deck_data = DraftData.create(deck, "Deck Submitter", datetime.datetime.now())
    print(deck_data.cards_in_deck())
    print(deck_data.timestamp)
    log_bytes = open(LOG_FILE_PATH, 'rb').read()
    log = log_bytes.decode(chardet.detect(log_bytes)["encoding"])
    log_data = DraftData.create(log, "Log Submitter", datetime.datetime.now())
    #print(log_data.data)
