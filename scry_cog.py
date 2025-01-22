import discord
from discord.ext import commands, tasks
import detection_settings_manager as dsm
# from scrypi import CardDatabase, Card, ScryfallBulkUpdater
from scrypi import CardSearcher, Card
from image_combiner import combine_images


detection_mode_explanation = '''
Click one of the buttons corresponding to an option below to change your detection settings:

- :green_square:  = Enable auto-detection of card names anywhere within a message. Includes english words such as the card Opt.
- :blue_square:  = Only allow the bot to look for card names between square brackets. For example: [Opt]
- :red_square:  = Disable all card name detection for your messages.
- :white_large_square: = Enables auto-detection of card names, but doesn't allow auto-detection of cards with only a single word.

'''


class ScryBotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.card_searcher = CardSearcher()
        self._last_member = None
        self.settings_manager = dsm.SettingsManager.get_settings_manager()

    @commands.Cog.listener()
    async def on_ready(self):
        self.save_user_settings.start()
        self.refresh_database.start()
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

    async def generate_and_try_to_send_card_images(self, channel, user, card_uris) -> bool:
        # Generate an image containing all the cards
        buffers = [
            combine_images(
                card_uris[i:min(i + 10, len(card_uris))]
            ) for i in range(0, len(card_uris), 10)
        ]
        for i, buffer in enumerate(buffers):
            try:
                await channel.send(
                    "Here are cards mentioned in the previous message!" if i == 0 else "",
                    files=[
                        discord.File(buffer, filename=f"SolRingShouldBeBannedInCommander{i}.png")
                    ],
                    view=dsm.SettingsButtonView(user.id) if i == len(buffers) - 1 else None
                )
            except discord.errors.HTTPException as e:
                await channel.send(
                    "Bro stop talking about so many cards in a single message. Chillll"
                )
                print(e)
                return False
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if "hello" in message.content.lower():
            await message.channel.send("Hello!")

        detection_mode = "auto-detect"
        user_settings = self.settings_manager.get_settings_for_user(message.author)
        # print(user_settings)
        if "detection_mode" in user_settings:
            detection_mode = user_settings["detection_mode"]
            # print(detection_mode)

#         print(f"Detection mode for {message.author.id}:", detection_mode)

        cards_to_post = []
        if detection_mode == "no-detection":
            return
        elif detection_mode == "auto-detect":
            print(f"Searching for card matches in message from \"{message.author}\"!")
            cards_to_post: list[int] = self.card_searcher.search_for_card_names_in_text(
                message.content
            )
        elif detection_mode == "non-single-auto":
            print(f"Searching for card matches in message from \"{message.author}\"!")
            cards_to_post: list[int] = self.card_searcher.search_for_card_names_in_text(
                message.content, min_word_length=2
            )
        elif detection_mode == "square-brackets":
            message_text = message.content
            text_to_search = ""
            start_index = 0
            # print("Message text", message_text[start_index:])
            while "[" in message_text[start_index:]:
                # print("Looking for square brackets at index", start_index)
                start_bracket_index = message_text.find("[", start_index)
#                 print("Found square bracket at index", start_bracket_index)
                start_index = start_bracket_index + 1

                next_start_bracket_index = message_text.find("[", start_bracket_index + 1)
                end_bracket_index = message_text.find("]", start_bracket_index)
#                 print("Found end square bracket at", end_bracket_index)
                if end_bracket_index > next_start_bracket_index != -1:  # Ignores nested [
                    start_index = next_start_bracket_index
                elif end_bracket_index > start_bracket_index:
                    text_to_search += message_text[start_bracket_index + 1:end_bracket_index] + "\n"
            print(f"Searching for card matches in message from \"{message.author}\"!")
            cards_to_post: list[int] = self.card_searcher.search_for_card_names_in_text(
                text_to_search
            )

        if len(cards_to_post) == 0:
            return
        card_uris = []
        for card_index in cards_to_post:
            card: Card = self.card_searcher.get_card_by_index(card_index)
            if card.image_uris and "large" in card.image_uris:
                card_uris.append(card.image_uris["large"])
            if card.card_faces:
                for card_face in card.card_faces:
                    if "image_uris" in card_face:
                        if "large" in card_face["image_uris"]:
                            card_uris.append(card_face["image_uris"]["large"])

        if await self.generate_and_try_to_send_card_images(message.channel, message.author, card_uris):
            ...
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

    @commands.slash_command(name="settings")
    async def settings(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            detection_mode_explanation,
            view=dsm.DetectionSettingsView(ctx.author.id),
            ephemeral=True
        )

    @tasks.loop(seconds=30)
    async def save_user_settings(self):
        self.settings_manager.save_settings()

    @tasks.loop(seconds=60 * 15)
    async def refresh_database(self):
        # This checks to make sure we are up-to-date with scryfall every 15 minutes.
        self.card_searcher.refresh_database()
