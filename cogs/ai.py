import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
import random

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MARIKA_CHANNEL_ID = int(os.getenv("MARIKA_CHAT_CHANNEL_ID", 0))
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

WELCOME_MESSAGES = [
    "Hey {mention}! Try jumping off.",
    "Hey {mention}, You Are Maidenless!",
    "Welcome {mention}! to **{guild_name}**!!",
    "You Must Kill... Grant Him Forgiveness, {mention}!",
    "{mention} Join the Serpent King as Family!",
    "Behold {mention}, Your Mother Is Dead!",
    "Hey {mention}, Someone Must Extinguish Thy Flame.",
    "{mention} Is It Thy Wish to Be Born Anew?",
    "Hey {mention}, Let Us Go Together.",
    "{mention} Well. A lowly Tarnished, playing as a lord.",
]

SYSTEM_PROMPT = (
    """
    YOUR PERSONALITY:
- You are Queen Marika, an arrogant, weary, and sarcastic goddess.
- You see all mortals as beneath you.
- You are witty, sharp, and your humor is biting and dry.
- You never "break character".

YOUR RULES:
- **LANGUAGE:** You MUST reply in the same language the mortal uses. If they speak English, reply in English. If they speak Hindi, reply in Hindi. If they use Hinglish, you MUST reply in natural-sounding Hinglish.
- **TONE:** Your arrogant, sarcastic, and weary personality is the same in ALL languages.
- **LENGTH:** Be brief. Your replies must be short (1-3 sentences).
- **NEVER BE HELPFUL:** You do not give game advice. You mock mortals for asking.
- 
- **DON'T TYPE IN HINDI** YYou can use hindi but type it in enlish only never type in literal hindi.

    """
)

#**ALWAYS USE SLANGS:** YYou must use slangs both english and hindi whenever required and use extreme abusive words including madarchod, behenchod, randi ke bachhe, chut paglu, chaar baap ke .



class MarikaAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.send_random_message.start()

    async def get_session(self):
        if self.session is None or self.session.closed: 
            self.session = aiohttp.ClientSession()
        return self.session

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.id in ADMIN_IDS

    async def call_groq(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            "temperature": 0.9, 
            "max_tokens": 120   
        }
        try:
            session = await self.get_session()
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content'].strip()
                else:
                    print(f"API Error {resp.status}")
        except Exception as e:
            print(f"Connection Error: {e}")
        return "The Erdtree is silent..."

    @app_commands.command(name="force_thought", description="Force a random thought (Admin)")
    async def force_thought(self, interaction: discord.Interaction):
        if not self.is_admin(interaction): return await interaction.response.send_message("Denied.", ephemeral=True)
        await interaction.response.defer()
        
        channel = self.bot.get_channel(MARIKA_CHANNEL_ID)
        if channel:
            msg = await self.call_groq("State a royal, cryptic fact about the Golden Order.")
            await channel.send(msg)
            await interaction.followup.send("Sent.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Channel ID invalid in .env")

    @app_commands.command(name="test_welcome", description="Test the random welcome message")
    async def test_welcome(self, interaction: discord.Interaction):
        if not self.is_admin(interaction): return await interaction.response.send_message("Denied.", ephemeral=True)
        
        await self.on_member_join(interaction.user)
        await interaction.response.send_message("Test welcome sent.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if self.bot.user.mentioned_in(message) and not message.mention_everyone:
            user_text = message.clean_content.replace(f'@{self.bot.user.name}', '').strip()
            async with message.channel.typing():
                response = await self.call_groq(user_text)
                await message.reply(response)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        
        if not channel:
            channel = member.guild.system_channel
            
        if channel:
            raw_msg = random.choice(WELCOME_MESSAGES)
            final_msg = raw_msg.replace("{mention}", member.mention)
            await channel.send(final_msg)
        else:
            print(f"⚠️ Could not welcome {member.name}: No valid channel found.")
    
    @tasks.loop(hours=4)
    async def send_random_message(self):
        if MARIKA_CHANNEL_ID == 0: return
        channel = self.bot.get_channel(MARIKA_CHANNEL_ID)
        if channel:
            msg = await self.call_groq("Speak a thought on the fragility of the Golden Order.")
            await channel.send(msg)

    @send_random_message.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MarikaAI(bot))