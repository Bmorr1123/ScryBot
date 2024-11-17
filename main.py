import discord
from discord.ext import commands
import scry_cog
import dotenv, os

# https://discord.com/oauth2/authorize?client_id=1307766400416354324&permissions=412317371456&integration_type=0&scope=bot
dotenv.load_dotenv()


class ScryBot(commands.Bot):
    async def on_ready(self):
        print(f"Logged in as {self.user} {self.user.id}")


def main():
    intents = discord.Intents.default()
    intents.message_content = True

    scry_bot = ScryBot(intents=intents)
    scry_bot.add_cog(scry_cog.Greetings(scry_bot))
    scry_bot.run(os.getenv("discord_token"))


if __name__ == '__main__':
    main()

