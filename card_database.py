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

        if None not in current_index:
            return
        indexes = [(index, self.get_card_by_index(index)) for index in current_index[None]]

        def sort_func(_, card):
            date = card.released_at
            if card.digital or card.promo or card.set == "sld":
                date = "1900-0-0"
            return date
        indexes.sort(key=lambda x: sort_func(*x), reverse=True)

        # Returning the most recent, non-secret-lair, non-promo, non-digital art
        return indexes[0][0]

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
                if card_object.set_type == "token":
                    card_object.name = f"{card_object.name} Token"

                if any(card_object.legalities.values()):
                    # If the card is legal in any format
                    self.cards.append(card_object)
            except TypeError as t:
                print(t)
                print(card)

    def _index_cards(self):
        start_time = time.time()
        print("Creating card name indexes.")

        non_alphanumeric_or_space = re.compile("[^a-zA-Z0-9 /]*")

        for card_index, card in enumerate(self.cards):
            if card.digital:
                continue
            # if card_index > 10000:
            #     break

            names = [name.strip() for name in unidecode(card.name).lower().split("//")]
            if "//" in card.name and len(card.name.split(" ")) <= 4:
                names = [unidecode(card.name).lower().strip()]
                print(names)
            for name in names:
                name = non_alphanumeric_or_space.sub("", name)
                words = name.split(" ")
                word_count = len(words)

                current_index = self.indexed_cards
                for i in range(word_count):  # Recursive insertion
                    if words[i] not in current_index:  # If not in current index
                        current_index[words[i]] = {}  # Make a new dict
                    current_index = current_index[words[i]]  # Go deeper

                if None not in current_index:
                    current_index[None] = [card_index]  # Insert the card index
                else:
                    current_index[None].append(card_index)
        # print(json.dumps(self.cards_by_word_count, indent=4))
        print(f"Finished creating card indexes. Time Elapsed: {time.time() - start_time:.2f}s")

