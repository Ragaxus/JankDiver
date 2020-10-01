"""A Discord bot that listens for posts in a particular channel. If the post contains an
attachment, the bot assumes that attachment is a deck, and saves that deck to a given
Google spreadsheet."""

import os
import json
from typing import Sequence

import chardet
from dotenv import load_dotenv
import discord

from cubelist import CubeList
from save_to_google_sheet import GoogleDraftDataSaver
from draftdata import DraftData, DraftDataParseError

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
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

service = GoogleDraftDataSaver(SPREADSHEET_ID)
disambiguation_holding_tank = {}
client = discord.Client()

@client.event
async def on_ready():
    """The function that handles the 'bot is connected' event."""
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(msg):
    """The function that handles the 'a message was posted' event."""
    #main channel processing -- handles users posting decklists
    if msg.channel.type != discord.ChannelType.text:
        return
    if msg.channel.name == CHANNEL and len(msg.attachments) > 0:
        #read the msg, put it into a stream for consumption
        try:
            file_of_message = await msg.attachments[0].read()
            stream = file_of_message.decode(chardet.detect(file_of_message)["encoding"])
            data = DraftData.create(stream, msg.author.name, msg.created_at)
            candidate_cubes = data.match_cubes(CUBE_LIST)
            if len(candidate_cubes) == 0:
                await sendDisambiguationRequest(msg.author, CUBE_LIST.keys(), data)
            elif len(candidate_cubes) == 1:
                data.save_to_spreadsheet(service, CUBE_LIST[candidate_cubes[0]])
            else: #len(candidate_cubes) > 1
                await sendDisambiguationRequest(msg.author, candidate_cubes, data)

        except DraftDataParseError as ex:
            await msg.channel.send(ex.message)

async def sendDisambiguationRequest(member: discord.User, candidate_cubes: Sequence[str],
                                    data: DraftData):
    channel = await member.create_dm()
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    header = "Couldn't determine the cube for your most recent submission. Please " \
             "react to this message with the emoji corresponding to the right cube: \n"
    cube_reaction_map = {emoji: cubeName for emoji, cubeName in zip(emojis[0:len(candidate_cubes)],candidate_cubes)}
    content = header + "\n".join([f"\t{emoji}: {cubeName}" for emoji, cubeName in cube_reaction_map.items()])
    message = await channel.send(content)
    disambiguation_holding_tank[message.id] = {"cube_reaction_map": cube_reaction_map, "data": data}

@client.event
async def on_reaction_add(rxn: discord.Reaction, user):
    """handler for a user disambiguating a deck submission
    that could have been from multiple cubes"""
    msg = rxn.message
    if msg.channel.type == discord.ChannelType.private:
        if msg.id in disambiguation_holding_tank:
            disambiguation_data = disambiguation_holding_tank[msg.id]
            cube_reaction_map = disambiguation_data["cube_reaction_map"]
            if rxn.emoji in cube_reaction_map:
                correct_cube = CUBE_LIST[cube_reaction_map[rxn.emoji]]
                data = disambiguation_data["data"]
                data.save_to_spreadsheet(service, correct_cube)
                await msg.delete()
                del disambiguation_holding_tank[msg.id]

client.run(DISCORD_TOKEN)
