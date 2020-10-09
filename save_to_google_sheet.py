"""Utilities to communicate with Google Sheet."""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GoogleDraftDataSaver:
    """Appends deck data to a given spreadsheet's 'Data' page."""

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self):
        """Logs into the Google API app. Returns a service object that will let us interact
        with the spreadsheet.
        """
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

    def write_to_sheet(self, cell_data, spreadsheet_id, location):
        """Saves a 2D array of data to the specified sheet location."""
        if not spreadsheet_id or not location:
            return
        sheet = self.service.spreadsheets()
        body = {"values": cell_data}
        sheet.values().append(body=body,
                              spreadsheetId=spreadsheet_id,
                              range=location,
                              includeValuesInResponse=False,
                              valueInputOption="RAW").execute()
