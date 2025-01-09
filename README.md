# ScryBot
ScryBot is a pycord based discord bot that reads all messages of a discord server and detects MTG card names that are mentioned. It then generates images containing all mentioned cards and posts them in the discord. This allows people to have discussions about various cards without needing to constantly switch between Scryfall and Discord.

**Here is an example of the bot in action:**

![jayce_vraska_example.png](readme_images%2Fjayce_vraska_example.png)

## How it Works
The data is pulled from Scryfall, checking every 15 minutes to see if Scryfall has added a new bulk file. These are typically updated every 24 hours by Scryfall, so new leaks may take a while for Scrybot have access to them.
1) The bot reads each new message. It looks for all combinations of words that make a card name.
    > The bot does this in under a second by utilizing a structured hash table of all card names and their index in data file provided by Scryfall.
2) The bot filters out card names that are within other card names.
3) The bot finds the versions of the card that most recent, and tries to avoid Secret Lair Drop, promo, or specialty arts when possible, and downloads an image for each card.
    > These images are typically sorted in the order they are mentioned, but the ordering can be changed in the following step.
4) The bot then sorts the images by size, and attempts to stitch them all together. If the file gets too large to send through discord, it will split it into several images.
    > Cards with weird image sizes on Scryfall will be placed lower in the image.
5) The bot will then send each image back in the discord!

# How to Host it Yourself
Due to how Discord handles bots reading messages on discord, the bot must be hosted by you in order to be added to your discord server. In order to do this, you must start by making your own bot on the Discord Developers page. There are many tutorials on how to do this online, and the process does change, so I will let you find a tutorial.
1) After you've created a bot, you need to invite it to the server and make sure it has permissions to read the content of messages. This is located in the Bot settings: ![intents.png](readme_images%2Fintents.png)
2) Next, make sure you have Python 3.12 (or newer).
3) Git clone the repository onto your computer:

   ```git clone https://github.com/Bmorr1123/ScryBot.git```
4) CD into the ScryBot folder, and pip install the requirements.txt

   ```pip install -r requirements.txt```
5) Next, make a file named `.env` and add the following line with `my_token` replaced by your bot's token.

   ```
   discord_token=my_token
   ```
6) Finally, you can run `python main.py` in your terminal to start the bot! Make sure it's in your discord server with permissions.

I hope you enjoy using the bot!