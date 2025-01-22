import discord, json


class SettingsManager:
    settings_manager = None

    @classmethod
    def get_settings_manager(cls):
        if not cls.settings_manager:
            cls.settings_manager = SettingsManager()
        return cls.settings_manager

    def __init__(self):
        self.settings_changed = False
        try:
            with open("scrybot_data/settings_data.json", "r") as settings_file:
                self.settings_data = json.load(settings_file)
        except FileNotFoundError:
            self.settings_data = {}
            self.save_settings(ignore_change_check=True)

    def get_settings_for_user(self, user: discord.User | discord.Member | int):
        if isinstance(user, discord.User) or isinstance(user, discord.Member):
            user = user.id
        user = str(user)
        if user not in self.settings_data:
            self.settings_data[user] = {
                "detection_mode": "auto-detect"
            }

        return self.settings_data[user]

    def set_settings_for_user(self, user: discord.User | discord.Member | int, detection_mode: str):
        if isinstance(user, discord.User) or isinstance(user, discord.Member):
            user = user.id

        user = str(user)
        if user not in self.settings_data:
            self.settings_data[user] = {
                "detection_mode": None
            }
        self.settings_data[user]["detection_mode"] = detection_mode
        self.settings_changed = True

    def save_settings(self, ignore_change_check=False):
        if not ignore_change_check and not self.settings_changed:
            return
        with open("scrybot_data/settings_data.json", "w+") as settings_file:
            json.dump(self.settings_data, settings_file, indent=4, sort_keys=True)
        print("Saved settings data to settings_data.json")
        self.settings_changed = False


class DetectionSettingsView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.settings_manager = SettingsManager.get_settings_manager()

    async def disable_button_and_enable_other_buttons(self, custom_id: str, interaction: discord.Interaction):
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                if button.custom_id == custom_id:
                    button.disabled = True
                else:
                    button.disabled = False

        await interaction.response.edit_message(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            print("Blocked other user.")
            await interaction.response.send_message(
                "You can't use those buttons. If you would like to change your settings, please use /settings.",
                ephemeral=True
            )
            return False

        print("Allowed user to change settings.")
        return True

    @discord.ui.button(
        label="Enable Auto-detection",
        style=discord.ButtonStyle.green,
        custom_id="all-detection"
    )
    async def all_detection(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self.interaction_check(interaction):
            return
        print("All Detection")

        self.settings_manager.set_settings_for_user(interaction.user, "auto-detect")
        await self.disable_button_and_enable_other_buttons(button.custom_id, interaction)

    @discord.ui.button(
        label="Square Bracket Detection",
        style=discord.ButtonStyle.blurple,
        custom_id="square-bracket-detection"
    )
    async def square_bracket_detection(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self.interaction_check(interaction):
            return
        print("Square Bracket Detection Only")

        self.settings_manager.set_settings_for_user(interaction.user, "square-brackets")
        await self.disable_button_and_enable_other_buttons(button.custom_id, interaction)

    @discord.ui.button(
        label="Disable Card Detection",
        style=discord.ButtonStyle.red,
        custom_id="disable-card-detection"
    )
    async def disable_all_detection(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self.interaction_check(interaction):
            return
        print("Detection disabled")

        self.settings_manager.set_settings_for_user(interaction.user, "no-detection")
        await self.disable_button_and_enable_other_buttons(button.custom_id, interaction)

    @discord.ui.button(
        label="Non-single Auto-detection",
        style=discord.ButtonStyle.gray,
        custom_id="non-single-auto"
    )
    async def non_single_word(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self.interaction_check(interaction):
            return
        print("Non-single Word Detection")

        self.settings_manager.set_settings_for_user(interaction.user, "non-single-auto")
        await self.disable_button_and_enable_other_buttons(button.custom_id, interaction)


class SettingsButtonView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            print("Blocked other user.")
            await interaction.response.send_message(
                "You can't use those buttons. If you would like to change your settings, please use /detection.",
                ephemeral=True
            )
            return False

        print("Allowed user to open settings.")
        return True

    @discord.ui.button(
        label="Detection Settings ⚙️",
        style=discord.ButtonStyle.grey
    )
    async def send_detection_options(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.edit_message(view=DetectionSettingsView(self.user_id))

