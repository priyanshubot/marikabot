import discord
from discord import app_commands
from discord.ext import commands
import psutil
import time
import os
import sys

ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

VC_STATE_FILE = "vc_state.txt"
START_TIME = time.time()

class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.id in ADMIN_IDS

    def get_help_embed(self):
        embed = discord.Embed(
            title="📜 The Golden Order Decrees", 
            description="Listen well, Tarnished. These are the tools granted to you.",
            color=0xD4AF37
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.add_field(name="🎶 Music", value="`/play`, `/skip`, `/queue`, `/stop`, `/seek`, `/volume`", inline=False)
        embed.add_field(name="🔮 AI Persona", value="`/force_thought`, `Mention Me`", inline=False)
        embed.add_field(name="⚖️ System", value=f"`!sync`, `!clear`, `/stats`, `/join`, `/leave`", inline=False)
        embed.set_footer(text="Kneel, or be broken.")
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        if os.path.exists(VC_STATE_FILE):
            try:
                with open(VC_STATE_FILE, "r") as f: 
                    cid = int(f.read().strip())
                channel = self.bot.get_channel(cid)
                if channel: 
                    await channel.connect(self_deaf=True, self_mute=True)
            except Exception as e: 
                print(f"VC Rejoin Failed: {e}")

    @commands.command(name="clear")
    async def clear_duplicates(self, ctx):
        if ctx.author.id not in ADMIN_IDS: return
        
        await ctx.send("🧹 Clearing duplicate commands for this server...")
        self.bot.tree.clear_commands(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ **Duplicates removed.** You may see no commands for a moment.\n🔁 **Restart Discord (Ctrl+R)** to see the clean list.")

    @commands.command(name="sync")
    async def text_sync(self, ctx):
        if ctx.author.id not in ADMIN_IDS: return
        
        await ctx.send("🌍 Syncing Global Commands... (This takes up to 1 hour to update everywhere)")
        await self.bot.tree.sync()
        await ctx.send("✅ Sync request sent to Discord.")

    @commands.command(name="help")
    async def text_help(self, ctx):
        await ctx.send(embed=self.get_help_embed())

        
    @app_commands.command(name="help", description="View commands")
    async def slash_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.get_help_embed())

    @app_commands.command(name="stats", description="System vitals")
    async def stats(self, interaction: discord.Interaction):
        if not self.is_admin(interaction): return await interaction.response.send_message("Begone.", ephemeral=True)
        
        uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - START_TIME))
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        embed = discord.Embed(title="System Status", color=0xD4AF37)
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="CPU", value=f"{cpu}%")
        embed.add_field(name="RAM", value=f"{ram}%")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="Restart bot")
    async def restart(self, interaction: discord.Interaction):
        if not self.is_admin(interaction): return await interaction.response.send_message("Denied.", ephemeral=True)
        await interaction.response.send_message("The Elden Ring shatters... and reforms.")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @app_commands.command(name="join", description="Enable 24/7 mode")
    async def join(self, interaction: discord.Interaction):
        if not self.is_admin(interaction): return await interaction.response.send_message("Denied.", ephemeral=True)
        
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            with open(VC_STATE_FILE, "w") as f: f.write(str(channel.id))
            
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.move_to(channel)
            else:
                await channel.connect(self_deaf=True, self_mute=True)
            await interaction.response.send_message(f"I shall remain in {channel.name}.")
        else:
            await interaction.response.send_message("You aren't in a VC.")

    @app_commands.command(name="leave", description="Disable 24/7 mode")
    async def leave(self, interaction: discord.Interaction):
        if not self.is_admin(interaction): return await interaction.response.send_message("Denied.", ephemeral=True)
        
        if interaction.guild.voice_client:
            if os.path.exists(VC_STATE_FILE): os.remove(VC_STATE_FILE)
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("I depart.")
        else:
            await interaction.response.send_message("I am not here.")

async def setup(bot):
    await bot.add_cog(System(bot))