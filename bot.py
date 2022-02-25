"""A Discord bot that listens for posts in a particular channel. If the post contains an
attachment, the bot assumes that attachment is a deck, and saves that deck to a given
Google spreadsheet."""

import os
import re
import json
from typing import Sequence
from datetime import datetime

import chardet
from dotenv import load_dotenv
import discord

from models.cubelist import CubeList
from save_to_google_sheet import GoogleDraftDataSaver
from draftdata import DraftData, DeckList, DraftDataParseError

CUBE_LIST = None
try:
    with open("config/cubes.json", 'r') as cubes_file:
        CUBE_LIST = CubeList.from_json(json.load(cubes_file))
except FileNotFoundError as ex:
    print("Couldn't find cube list.")
    quit()

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('CHANNEL')

service = GoogleDraftDataSaver()
disambiguation_holding_tank = {}
client = discord.Client()


@client.event
async def on_ready():
    """The function that handles the 'bot is connected' event."""
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(msg):
    """The function that handles the 'a message was posted' event."""
    # main channel processing -- handles users posting decklists
    if msg.channel.type != discord.ChannelType.text:
        return
    if msg.channel.name == CHANNEL and len(msg.attachments) > 0:
        try:
            await parse_submission(msg)
        except DraftDataParseError as ex:
            await msg.channel.send(ex.message)


async def parse_submission(msg):
    # Regex for Win-Loss YYYY-MM-DD HH:MM
    msg_re = re.compile(
        r'(.*\b(?P<wins>\d+)-\d+\b)?'
        r'\s?'
        r'(\b(?P<year>[0-9]{4})-(?P<month>1[0-2]|0[0-9])-(?P<day>0[1-9]|[1-2][0-9]|3[0-1])\b)?'
        r'\s?'
        r'(\b(?P<hour>[0-1][0-9]|2[0-4]):(?P<minute>[0-5][0-9])\b)?'
        )
    # Assign the parameters found.
    msg_params = msg_re.search(msg.content).groupdict(default="")
    wins = msg_params.pop("wins")
    if wins != "":
        wins = int(wins)
    date = msg.created_at
    date = date.replace(**{key: int(val) for key, val in msg_params.items() if val != ""})
    # Handle attached file.
    attachment = msg.attachments[0]
    if not attachment.size > 0:
        await send_empty_file_alert(msg.author, attachment.filename)
        return
    file_of_message = await attachment.read()
    stream = file_of_message.decode(chardet.detect(file_of_message)["encoding"])
    data = DraftData.create(stream, msg.author.name, date, wins)
    if (isinstance(data, DeckList) and data.commander):
        await send_commander_admonishment(msg.author)
        return
    candidate_cubes = data.match_cubes(CUBE_LIST)
    if len(candidate_cubes) == 0:
        await send_disambiguation_request(msg.author, CUBE_LIST.keys(), data)
    elif len(candidate_cubes) == 1:
        data.save_to_spreadsheet(service, CUBE_LIST[candidate_cubes[0]])
    else:  # len(candidate_cubes) > 1
        await send_disambiguation_request(msg.author, candidate_cubes, data)


async def send_empty_file_alert(member: discord.User, attachment_name: str):
    """Alerts submitter that their file was empty."""
    content = f"The file you most recently submitted, {attachment_name}, is empty!" \
              "\n\n"\
              "(If you feel you're receiving this message in error, please alert a server admin.)"
    channel = await member.create_dm()
    await channel.send(content)


async def send_commander_admonishment(member: discord.User):
    """We don't take kindly to your type around here."""
    content = "I can't help but notice that your most recent submission to the deck submission "\
              "channel was a deck that has a commander in it. None of our cubes are meant "\
              "for Commander play, so I don't understand why you'd submit a deck with "\
              "a commander to the deck submission channel. "\
              "\n\n"\
              "(If you feel you're receiving this message in error, please alert a server admin.)"
    channel = await member.create_dm()
    await channel.send(content)


async def send_disambiguation_request(member: discord.User, candidate_cubes: Sequence[str],
                                      data: DraftData):
    """Sends a message to a user asking them to specify which cube their submission belongs to."""
    channel = await member.create_dm()
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    header = "Couldn't determine the cube for your most recent submission. Please " \
             "react to this message with the emoji corresponding to the right cube: \n"
    emoji_cube_pairs = zip(emojis[0:len(candidate_cubes)], candidate_cubes)
    cube_reaction_map = {emoji: cubeName for emoji, cubeName in emoji_cube_pairs}
    cube_reaction_map_strings = [f"\t{emoji}: {name}" for emoji, name in cube_reaction_map.items()]
    content = header + "\n".join(cube_reaction_map_strings)
    message = await channel.send(content)
    disambiguation_holding_tank[message.id] = {"cube_reaction_map": cube_reaction_map, "data": data}


@client.event
async def on_raw_reaction_add(payload):  # pylint: disable=unused-argument
    """handler for a user disambiguating a deck submission
    that could have been from multiple cubes"""
    channel = client.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    emoji = payload.emoji.name #This is the unicode codepoint of the emoji
    if msg.channel.type == discord.ChannelType.private:
        if msg.id in disambiguation_holding_tank:
            disambiguation_data = disambiguation_holding_tank[msg.id]
            cube_reaction_map = disambiguation_data["cube_reaction_map"]
            if emoji in cube_reaction_map:
                correct_cube = CUBE_LIST[cube_reaction_map[emoji]]
                data = disambiguation_data["data"]
                data.save_to_spreadsheet(service, correct_cube)
                await msg.delete()
                del disambiguation_holding_tank[msg.id]

client.run(DISCORD_TOKEN)
