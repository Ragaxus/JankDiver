"""Utilities to communicate with Google Sheet."""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GoogleDeckSaver:
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

    def save_data(self, data, location):
        """Given an array and a Sheets location, saves that array 
        as a row or rows at that location."""
        sheet = self.service.spreadsheets()
        body = {"values": data}
        sheet.values().append(body=body,
                              spreadsheetId=self.spreadsheet_id,
                              range=location,
                              includeValuesInResponse=False,
                              valueInputOption="RAW").execute()
    def save_deck(self, data):
        """Wrapper on save_data that saves the data to the Decks sheet."""
        self.save_data(data, "Decks!C1")
    def save_draft_log(self, data):
        """Wrapper on save_data that saves the data to the Draft Logs sheet."""
        self.save_data(data, "Draft Logs!A1")
