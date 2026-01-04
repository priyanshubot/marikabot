import discord
from discord import app_commands
from discord.ext import commands
import wavelink

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        nodes = [wavelink.Node(uri="http://127.0.0.1:2333", password="youshallnotpass")]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)
        print("Music Connected.")
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        if not player: return

        channel = getattr(player, "home", None)
        track = payload.track

        if channel:
            try:
                if hasattr(player, "last_msg") and player.last_msg:
                    await player.last_msg.delete()
            except:
                pass

            embed = discord.Embed(title="Now Playing", description=f"[{track.title}]({track.uri})", color=0xD4AF37)
            embed.add_field(name="Artist", value=track.author, inline=True)
            seconds = track.length // 1000
            embed.add_field(name="Duration", value=f"{seconds // 60}:{seconds % 60:02d}", inline=True)
            if track.artwork: embed.set_thumbnail(url=track.artwork)
            
            msg = await channel.send(embed=embed)

            controls = ["⏯️", "⏭️", "⏹️", "🔉", "🔊"]
            for emoji in controls:
                await msg.add_reaction(emoji)
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot: return 
        player = reaction.message.guild.voice_client
        if not player or not isinstance(player, wavelink.Player): return

        if not hasattr(player, "last_msg") or reaction.message.id != player.last_msg.id:
            return

        if not user.voice or user.voice.channel != player.channel:
            return

        emoji = str(reaction.emoji)

        if emoji == "⏯️":
            if player.paused: await player.pause(False)
            else: await player.pause(True)
        
        elif emoji == "⏭️":
            await player.skip(force=True)
        
        elif emoji == "⏹️":
            await player.queue.clear()
            await player.disconnect()
            await reaction.message.channel.send("Silence.")
        
        elif emoji == "🔉":
            vol = max(0, player.volume - 10)
            await player.set_volume(vol)
        
        elif emoji == "🔊":
            vol = min(100, player.volume + 10)
            await player.set_volume(vol)

        try:
            await reaction.remove(user)
        except:
            pass

    @app_commands.command(name="play", description="Play a hymn (Text or Link)")
    async def play(self, interaction: discord.Interaction, search: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("Join a voice channel first.", ephemeral=True)

        await interaction.response.defer()
        vc = interaction.guild.voice_client
        
        if not vc:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        elif not isinstance(vc, wavelink.Player):
            await vc.disconnect()
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            player = vc

        player.home = interaction.channel
        player.autoplay = wavelink.AutoPlayMode.enabled

        tracks = None
        try: tracks = await wavelink.Playable.search(search)
        except: pass
        if not tracks: tracks = await wavelink.Playable.search(search, source=wavelink.TrackSource.YouTubeMusic)
        if not tracks: return await interaction.followup.send("No hymns found.")

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks: await player.queue.put_wait(track)
            await interaction.followup.send(f"Added playlist **{tracks.name}**.")
        else:
            track = tracks[0]
            await player.queue.put_wait(track)
            await interaction.followup.send(f"Added **{track.title}**.")

        if not player.playing and not player.queue.is_empty:
            await player.play(player.queue.get())

    @app_commands.command(name="skip", description="Skip current hymn")
    async def skip(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client
        if player and isinstance(player, wavelink.Player) and player.playing:
            await player.skip(force=True)
            await interaction.response.send_message("Skipped.")
        else:
            await interaction.response.send_message("Nothing is playing.")

    @app_commands.command(name="queue", description="Show the queue")
    async def queue(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client
        if not player or not isinstance(player, wavelink.Player):
            return await interaction.response.send_message("Silence.")
        if player.queue.is_empty:
            return await interaction.response.send_message("Queue is empty (Autoplay active).")
        
        desc = ""
        for i, track in enumerate(player.queue[:10]):
            desc += f"{i+1}. {track.title}\n"
        embed = discord.Embed(title="Golden Queue", description=desc, color=0xD4AF37)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="seek", description="Seek to seconds")
    async def seek(self, interaction: discord.Interaction, seconds: int):
        player = interaction.guild.voice_client
        if player and isinstance(player, wavelink.Player):
            await player.seek(seconds * 1000)
            await interaction.response.send_message(f"Seeked to {seconds}s.")

    @app_commands.command(name="volume", description="Set volume 0-100")
    async def volume(self, interaction: discord.Interaction, level: int):
        player = interaction.guild.voice_client
        if player and isinstance(player, wavelink.Player):
            await player.set_volume(level)
            await interaction.response.send_message(f"Volume set to {level}%.")

    @app_commands.command(name="stop", description="Stop music")
    async def stop(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client
        if player:
            if isinstance(player, wavelink.Player): player.queue.clear()
            await player.disconnect()
            await interaction.response.send_message("Silence.")

async def setup(bot):
    await bot.add_cog(Music(bot))
