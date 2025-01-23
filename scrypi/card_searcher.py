import time
from .scryfall_interface import ScryfallBulkUpdater, CardDatabase, Card


class CardSearcher:
    def __init__(self):
        self.bulk_updater = ScryfallBulkUpdater()
        self.card_database = CardDatabase(self.bulk_updater.bulk_data)

    def search_for_card_names_in_text(
            self,
            message_content,
            get_all_printings=False,
            print_search_results=False,
            return_string_indexes=False,
            return_card_names=False,
            debug=False,
            min_word_length=1
    ) -> list[int] | list[list[int]] | list[tuple[int, int]] | list[str]:
        start_time = time.time()
        words = message_content.replace(" // ", " ").replace("\n", " ").split(" ")
        word_count = len(words)
        card_indexes_found = []
        if debug:
            print(f"\tTotal Words: {word_count}")
        for i in range(word_count):
            if debug:
                print(f"\t\tCurrent Index: {i}")
            for j in range(i + min_word_length, min(word_count + 1, i + 10)):
                word_set = words[i:j]
                index = self.card_database.find_card_index_by_name(" ".join(word_set), return_multiple=get_all_printings)
                index_with_s_e = (index, i, j + 1)
                if index is not None and index_with_s_e not in card_indexes_found:  # Check if it was found and isn't a duplicate
                    card_indexes_found.append(index_with_s_e)
        if debug:
            print(f"\tCard indexes found: {len(card_indexes_found)} Removing card names within other card names.")
        # Removing card names within card names
        card_indexes_found.sort(key=lambda x: x[2] - x[1])

        # Bubble search
        i = 0
        while i < len(card_indexes_found):
            if debug:
                print(f"\t\tCurrent Index: {i}")
            index, start, end = card_indexes_found[i]
            word_count = end - start
            index_range = range(start, end)
            j = i + 1

            found_within_another_card_name = False
            while j < len(card_indexes_found):
                if debug:
                    print(f"\t\t\tCurrent Index: {j}")
                later_index, later_start, later_end = card_indexes_found[j]
                later_word_count = later_end - later_start
                later_index_range = range(later_start, later_end)
                intersection = [value for value in index_range if value in later_index_range]
                if intersection and later_word_count > word_count:
                    found_within_another_card_name = True
                    break
                if index == later_index:
                    found_within_another_card_name = True
                    break
                j += 1

            if found_within_another_card_name:
                card_indexes_found.pop(i)
            else:
                i += 1

        card_indexes_found.sort(key=lambda x: x[1])

        if print_search_results:
            print(
                f"Found {len(card_indexes_found)} card names in the message. Elapsed Time: {time.time() - start_time:.2f}s")
            print(f"\t{card_indexes_found}")
        if return_string_indexes:
            return [
                (message_content.find(words[start]), message_content.find(words[end - 1]))
                for index, start, end in card_indexes_found
            ]
        elif return_card_names:
            return [" ".join(words[start:end - 1]) for index, start, end in card_indexes_found]
        return [index for index, start, end in card_indexes_found]

    def get_card_by_index(self, card_index: int) -> Card | None:
        return self.card_database.get_card_by_index(card_index)

    def refresh_database(self):
        if self.bulk_updater.check_if_bulk_data_is_old():
            self.bulk_updater.load_bulk_data()
            self.card_database = CardDatabase(self.bulk_updater.bulk_data)
            print(f"{time.strftime("[%d/%m/%Y %H:%M:%S]", time.localtime())}: Refreshed Database")
        else:
            print(f"{time.strftime("[%d/%m/%Y %H:%M:%S]", time.localtime())}: Did not need to refresh Database")
