"""Utility that parses a decklist into an array of cards."""

import re


def parse_deck(deck_string):
    """Given a deck as a string, returns a list of card names in the maindeck.
    Parameters
    ----------
    deck_string : string
    A whole deck file as a string.
    """
    cards = []
    card_regex = re.compile(r'1 ([^\(]+) ')
    for line in deck_string.split('\n'):
        if line == "Sideboard":
            break
        if line.startswith('1 '):
            cards.append(card_regex.match(line).group(1))
    return cards


if __name__ == "__main__":
    deck = open(r"C:\Users\sgold\Downloads\20200729.txt", 'r').read()
    print(parse_deck(deck))
