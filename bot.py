"""A Discord bot that listens for posts in a particular channel. If the post contains an
attachment, the bot assumes that attachment is a deck, and saves that deck to a given
Google spreadsheet."""

import os
import discord
from dotenv import load_dotenv
import chardet

from save_to_google_sheet import GoogleDraftDataSaver
from draftdata import DraftData, DraftDataParseError

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('CHANNEL')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Call the Sheets API
service = GoogleDraftDataSaver(SPREADSHEET_ID)

client = discord.Client()

@client.event
async def on_ready():
    """The function that handles the 'bot is connected' event."""
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(msg):
    """The function that handles the 'a message was posted' event."""
    if msg.channel.name == CHANNEL and len(msg.attachments) > 0:
        #read the msg, put it into a stream for consumption
        try:
            file_of_message = await msg.attachments[0].read()
            stream = file_of_message.decode(chardet.detect(file_of_message)["encoding"])
            data = DraftData(stream, msg.author.name, msg.created_at.date())
            service.write_to_sheet(data)
        except DraftDataParseError as ex:
            await msg.channel.send(ex.message)


client.run(DISCORD_TOKEN)
