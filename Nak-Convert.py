import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from PIL import Image
import io
from dotenv import load_dotenv
import os


load_dotenv()


TOKEN_BOT = os.getenv("TOKEN_BOT")  
CHANNEL_ID = os.getenv("CHANNEL_ID")  


if not TOKEN_BOT:
    raise ValueError("Le token du bot (TOKEN_BOT) est introuvable dans le fichier .env.")
if not CHANNEL_ID:
    raise ValueError("L'ID du channel (CHANNEL_ID) est introuvable dans le fichier .env.")

CHANNEL_ID = int(CHANNEL_ID)  


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)



class FormatSelectionMenu(View):
    def __init__(self):
        super().__init__(timeout=None)  

    
        select = Select(
            placeholder="Choisissez un format...",
            custom_id="format_selection_unique",  
            options=[
                discord.SelectOption(label="JPG", description="Convertir en JPG"),
                discord.SelectOption(label="PNG", description="Convertir en PNG"),
                discord.SelectOption(label="GIF", description="Convertir en GIF"),
                discord.SelectOption(label="WEBP", description="Convertir en WEBP"),
                discord.SelectOption(label="BMP", description="Convertir en BMP")
            ]
        )

        select.callback = self.select_callback  
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_format = interaction.data['values'][0].upper()
        await interaction.response.send_message(
            content=f"Format sélectionné : **{selected_format}**.\nVeuillez maintenant envoyer une image dans le chat.",
            ephemeral=False
        )
        self.stop()
        await wait_for_image(interaction.channel, selected_format)



class CleanButton(View):
    def __init__(self):
        super().__init__(timeout=None)  

       
        clean_button = Button(
            label="Nettoyer le channel",
            style=discord.ButtonStyle.red,
            custom_id="clean_channel_unique" 
        )
        clean_button.callback = self.clean_callback
        self.add_item(clean_button)

    async def clean_callback(self, interaction: discord.Interaction):
        await clean_channel(interaction.channel)



async def wait_for_image(channel, selected_format):
    def check(message):
        return message.channel == channel and message.attachments

    try:
        message = await bot.wait_for("message", timeout=60.0, check=check)
        attachment = message.attachments[0]
        await convert_image(channel, attachment, selected_format)
    except Exception as e:
        await channel.send("Temps écoulé ou erreur. Veuillez recommencer.", delete_after=10)



async def convert_image(channel, attachment, format):
    try:
        
        if format == "JPG":
            format = "JPEG"  

        img_data = await attachment.read()
        img = Image.open(io.BytesIO(img_data))

        
        if format == "JPEG":
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

        
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=format)
        output_buffer.seek(0)

        
        await channel.send(
            content=f"L'image a été convertie en **{format}**.",
            file=discord.File(fp=output_buffer, filename=f"converted_image.{format.lower()}"),
            view=CleanButton()
        )
    except Exception as e:
        await channel.send(f"Erreur lors de la conversion : {e}", delete_after=10)



async def clean_channel(channel):
    await channel.purge()
    await send_menu(channel)



async def send_menu(channel):
    embed = discord.Embed(
        title="Menu Principal - ImageBot",
        description="Bienvenue dans **ImageBot**, votre assistant de conversion d'images.\n\n"
                    "Choisissez un format parmi le menu déroulant pour commencer.\n\n",
        color=discord.Color.blue()
    )
    embed.set_footer(text="ImageBot | Par Nakwi")
    await channel.send(embed=embed, view=FormatSelectionMenu())


@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await send_menu(channel)


# Lancer le bot
bot.run(TOKEN_BOT)