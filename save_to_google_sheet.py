"""Utilities to communicate with Google Sheet."""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from draftdata import DraftData


class GoogleDraftDataSaver:
    """Appends deck data to a given spreadsheet's 'Data' page."""

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheetId):
        """Logs into the Google API app. Returns a service object that will let us interact
        with the spreadsheet.
        """

        self.spreadsheet_id = spreadsheetId

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def write_to_sheet(self, data: DraftData):
        """Given a DraftData, saves the contents of the DraftData
        to a Google spreadsheet in a manner that matches its data type.
        If the DraftData's dataType is 'deck', the DraftData's data is
        a deck's maindeck and sideboard. We will save the maindeck to the Decks sheet,
        and the sideboard to the Sideboards sheet."""
        sheet = self.service.spreadsheets()

        if data.type == "deck":
            #write the main deck
            #placeholders for colors and record
            deck_metadata = [data.user, "", "", data.timestamp]
            cell_data = deck_metadata + data.data[0]
            body = {"values": [cell_data]}
            sheet.values().append(body=body,
                                  spreadsheetId=self.spreadsheet_id,
                                  range="Decks!a1",
                                  includeValuesInResponse=False,
                                  valueInputOption="RAW").execute()
            #write the sideboard
            #(no placeholders - no need to fill in that info twice)
            sb_metadata = [data.user, data.timestamp]
            cell_data = sb_metadata + data.data[1]
            body = {"values": [cell_data]}
            sheet.values().append(body=body,
                                  spreadsheetId=self.spreadsheet_id,
                                  range="Sideboards!A1",
                                  includeValuesInResponse=False,
                                  valueInputOption="RAW").execute()


        if data.type == "draft":
            #write the draft seats
            cell_values = []
            for user_representation in data.data:
                cell_values.append([data.timestamp, user_representation["name"]] + user_representation["picks"])
            cell_values.append([""])
            body = {"values": cell_values}
            sheet.values().append(body=body,
                                  spreadsheetId=self.spreadsheet_id,
                                  range="Draft Logs!A1",
                                  includeValuesInResponse=False,
                                  valueInputOption="RAW").execute()

if __name__ == "__main__":
    from dotenv import load_dotenv
    import chardet

    load_dotenv()
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

    # Call the Sheets API
    service = GoogleDraftDataSaver(SPREADSHEET_ID)

    DECK_FILE_PATH = r"C:\Users\sgold\Documents\Arena Cube Drafts\take_me_to_church.txt"
    LOG_FILE_PATH = r"C:\Users\sgold\Downloads\DraftLog_APCd.txt"

    deck_bytes = open(DECK_FILE_PATH, 'rb').read()
    deck = deck_bytes.decode(chardet.detect(deck_bytes)["encoding"])
    deck_data = DraftData(deck, "Deck Submitter", 1)
    service.write_to_sheet(deck_data)

    log_bytes = open(LOG_FILE_PATH, 'rb').read()
    log = log_bytes.decode(chardet.detect(deck_bytes)["encoding"])
    log_data = DraftData(log, "Log Submitter", 2)
    service.write_to_sheet(log_data)
