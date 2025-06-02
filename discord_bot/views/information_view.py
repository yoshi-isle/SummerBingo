import discord

class InformationView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot=bot

    @discord.ui.button(label="Rules", style=discord.ButtonStyle.secondary, custom_id="rules_button",)
    async def rules_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"hi", ephemeral=True)