import time

import discord
from discord.ext import commands, tasks
from card_database import CardDatabase
from card import Card
from scryfall_interface import ScryfallBulkUpdater
from image_combiner import combine_images


class CardSearcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bulk_updater = ScryfallBulkUpdater()
        self.card_database = CardDatabase(self.bulk_updater.bulk_data)
        self._last_member = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("CardSearcher loaded successfully!")

    @commands.command()
    async def hello(self, ctx, *, member: discord.Member = None):
        """Says hello"""
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send(f'Hello {member.name}~')
        else:
            await ctx.send(f'Hello {member.name}... This feels familiar.')
        self._last_member = member

    def check_message_content(self, message_content, debug=False) -> list[int]:
        """
        Checks message for any MTG card names.
        :return:
        """
        start_time = time.time()
        words = message_content.replace(" // ", " ").split(" ")
        word_count = len(words)
        card_indexes_found = []
        if debug:
            print(f"\tTotal Words: {word_count}")
        for i in range(word_count):
            if debug:
                print(f"\t\tCurrent Index: {i}")
            for j in range(i + 1, min(word_count + 1, i + 10)):
                word_set = words[i:j]
                index = self.card_database.find_card_index_by_name(" ".join(word_set))
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

        print(f"Found {len(card_indexes_found)} card names in the message. Elapsed Time: {time.time() - start_time:.2f}s")
        print(f"\t{card_indexes_found}")
        return [index for index, start, end in card_indexes_found]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if "hello" in message.content.lower():
            await message.channel.send("Hello!")

        print(f"Searching for card matches in message from \"{message.author}\"!")
        cards_to_post: list[int] = self.check_message_content(message.content)
        card_uris = []
        for card_index in cards_to_post:
            card: Card = self.card_database.get_card_by_index(card_index)
            if card.image_uris and "large" in card.image_uris:
                card_uris.append(card.image_uris["large"])
            if card.card_faces:
                for card_face in card.card_faces:
                    if "image_uris" in card_face:
                        if "large" in card_face["image_uris"]:
                            card_uris.append(card_face["image_uris"]["large"])

        # Generate an image containing all the cards
        buffer = combine_images(card_uris)
        if buffer is not None:
            await message.channel.send(
                "Here are cards mentioned in the previous message!",
                file=discord.File(buffer, filename="SolRingShouldBeBannedInCommander.png")
            )
        else:
            await message.channel.send(
                "Here are cards mentioned in the previous message!\n" + "\n".join(card_uris)
            )

    # @commands.Cog.listener()
    # async def on_message_edit(self, before, after):
    #     if message.author.bot:
    #         return
    #     if before and after:
    #         if before.content != after.content:
    #             ...

    @tasks.loop(seconds=60 * 15)
    async def refresh_database(self):
        # This checks to make sure we are up-to-date with scryfall every 15 minutes.
        if self.bulk_updater.check_if_bulk_data_is_old():
            self.bulk_updater.load_bulk_data()

        self.card_database = CardDatabase(self.bulk_updater.bulk_data)

