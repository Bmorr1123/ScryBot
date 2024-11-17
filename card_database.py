import json
from card import Card
from unidecode import unidecode
import re, time


class CardDatabase:
    def __init__(self, data: list):

        # Removing non-cards
        data = list(filter(lambda x: x["object"] == "card", data))

        # Converting to card objects
        self.cards: list[Card] = []
        self._load_cards(data)

        # Create a data structure to quickly search for any card by name.
        self.indexed_cards = {}
        self._index_cards()

    def find_card_index_by_name(self, card_name) -> None | int:
        non_alphanumeric_or_space = re.compile("[^a-zA-Z0-9 ]*")
        card_name = non_alphanumeric_or_space.sub("", unidecode(card_name)).lower()

        words = card_name.split(" ")
        word_count = len(words)

        current_index = self.indexed_cards
        for i in range(word_count):  # Recursive insertion
            if words[i] not in current_index:  # If not in current index
                return
            current_index = current_index[words[i]]  # Go deeper

        if None in current_index:
            return current_index[None]

    def get_card_by_index(self, card_index: int) -> Card | None:
        if 0 <= card_index < len(self.cards):
            return self.cards[card_index]

    def _load_cards(self, data):
        for card in data:
            try:
                if "object" in card:
                    del card["object"]
                card_object = Card(**card)
                card_object.legalities = {  # Converting the strings to bools
                    format: legality == "not_legal"
                    for format, legality in card_object.legalities.items()
                }

                if card_object.set_type == "minigame":
                    continue

                if any(card_object.legalities.values()):
                    # If the card is legal in any format
                    self.cards.append(card_object)
            except TypeError as t:
                print(t)
                print(card)

    def _index_cards(self):
        start_time = time.time()
        print("Creating card name indexes.")

        non_alphanumeric_or_space = re.compile("[^a-zA-Z0-9 ]*")

        for card_index, card in enumerate(self.cards):
            # if card_index > 10000:
            #     break
            names = [name.strip() for name in unidecode(card.name).lower().split("//")]
            for name in names:
                name = non_alphanumeric_or_space.sub("", name)
                words = name.split(" ")
                word_count = len(words)

                current_index = self.indexed_cards
                for i in range(word_count):  # Recursive insertion
                    if words[i] not in current_index:  # If not in current index
                        current_index[words[i]] = {}  # Make a new dict
                    current_index = current_index[words[i]]  # Go deeper

                current_index[None] = card_index  # Insert the card index
        # print(json.dumps(self.cards_by_word_count, indent=4))
        print(f"Finished creating card indexes. Time Elapsed: {time.time() - start_time:.2f}s")

