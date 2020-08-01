"""A Discord bot that listens for posts in a particular channel. If the post contains an
attachment, the bot assumes that attachment is a deck, and saves that deck to a given
Google spreadsheet."""

import os
import discord
from dotenv import load_dotenv
import chardet

from save_to_google_sheet import GoogleDeckSaver
from parse_deck import parse_deck

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('CHANNEL')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Call the Sheets API
service = GoogleDeckSaver(SPREADSHEET_ID)

client = discord.Client()


@client.event
async def on_ready():
    """The function that handles the 'bot is connected' event."""
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(msg):
    """The function that handles the 'a message was posted' event."""
    if msg.channel.name == CHANNEL:
        if msg.content == "$dive":
            channel = msg.channel
            old_messages_list = await channel.history(limit=200).flatten()
            decks_found = await save_decks_from_messages(reversed(old_messages_list))
            spreadsheet_link = "https://docs.google.com/spreadsheets/d/"+SPREADSHEET_ID
            await msg.channel.send(f'{decks_found} decks saved to sheet. {spreadsheet_link}')
        else:
            await save_decks_from_messages([msg])


async def save_decks_from_messages(msg_list):
    """Given a set of messages in the deck-dump channel, for each message,
       determines if it has a file attached. If it does, parse it as a deck file
       and save that file to the Google Sheet.
       Returns the number of decks."""
    decks_found=0
    all_deck_data = []
    for msg in msg_list:
        if len(msg.attachments) > 0:
            try:
                deck_bytes = await msg.attachments[0].read()
                deck_metadata = [msg.author.name, "",
                                msg.created_at.date().isoformat()]
                deck = deck_bytes.decode(chardet.detect(deck_bytes)["encoding"])
                deck_data = parse_deck(deck)
                all_deck_data.append(deck_metadata + deck_data)
                decks_found += 1
            except print(0):
                pass
    service.save_deck(all_deck_data)
    return decks_found


client.run(DISCORD_TOKEN)
