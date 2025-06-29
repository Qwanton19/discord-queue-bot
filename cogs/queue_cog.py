# cogs/queue_cog.py
import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import emoji

# default emojis to use
DEFAULT_JOIN_EMOJI = '⭐'
DEFAULT_ADVANCE_EMOJI = '✅'


class QueueCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}


    # yoinked search for emojis, also make sure that bot can use it
    def _can_use_emoji(self, emoji_str: str) -> bool:
        if emoji.is_emoji(emoji_str):
            return True
        match = re.search(r'<a?:.+?:(\d+)>$', emoji_str)
        if match:
            emoji_id = int(match.group(1))
            return discord.utils.get(self.bot.emojis, id=emoji_id) is not None
        return False

    # standardized error handling message
    async def send_error(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(f"❌ **Error:** {message}", ephemeral=True)


    # admin commands

    # set emoji to join the queue
    @app_commands.command(name="joinemoji", description="Sets the join emoji for the next queue in this channel.")
    @app_commands.describe(emoji="The emoji users will react with to join.")
    @app_commands.checks.has_permissions(administrator=True)
    async def joinemoji(self, interaction: discord.Interaction, emoji: str):
        if not self._can_use_emoji(emoji):
            await self.send_error(interaction, f"Invalid emoji `{emoji}`. Make sure it is a standard emoji.")
            return
        channel_id = interaction.channel.id
        if self.queues.get(channel_id, {}).get('queue_message_id'):
            await self.send_error(interaction, "You can only set the join emoji *before* creating a queue with `/newqueue`.")
            return
        self.queues.setdefault(channel_id, {})['join_emoji'] = emoji
        await interaction.response.send_message(f"✅ The join emoji for this channel has been set to {emoji}. Use `/newqueue` to create the queue with this emoji.", ephemeral=True)

    # set emoji to advance queue
    @app_commands.command(name="nextemoji", description="Sets the emoji needed to advannce the queue for this channel.")
    @app_commands.describe(emoji="The emoji the current person will react with to advance the queue.")
    @app_commands.checks.has_permissions(administrator=True)
    async def nextemoji(self, interaction: discord.Interaction, emoji: str):
        if not self._can_use_emoji(emoji):
            await self.send_error(interaction, f"Invalid emoji `{emoji}`. Make sure it is a standard emoji.")
            return
        channel_id = interaction.channel.id
        queue = self.queues.get(channel_id)
        if not queue or not queue.get('queue_message_id'):
            await self.send_error(interaction, "A queue must be created with `/newqueue` before you can set the 'next' emoji.")
            return
        if queue.get('is_active'):
            await self.send_error(interaction, "You cannot change the 'next' emoji after the queue has been started with `/startqueue`.")
            return
        queue['advance_emoji'] = emoji
        await interaction.response.send_message(f"✅ The 'next person' emoji has been updated to {emoji}.", ephemeral=True)

    # troubleshoot command to go back a person in queue
    @app_commands.command(name="queueback", description="Reverts the queue to the previous person.")
    @app_commands.checks.has_permissions(administrator=True)
    async def queueback(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        queue = self.queues.get(channel_id)
        if not queue or not queue.get('is_active'):
            await self.send_error(interaction, "The queue must be active to use this command.")
            return
        if not queue['users']:
            await self.send_error(interaction, "The queue is empty, cannot go back.")
            return
        num_users = len(queue['users'])
        queue['current_index'] = (queue['current_index'] - 1 + num_users) % num_users
        await interaction.response.send_message("⏪ Reverting to the previous person in the queue...", ephemeral=True)
        await self._advance_queue(channel_id)

    # troubleshoot command to go forward a person in queue
    @app_commands.command(name="queuenext", description="Manually advances the queue to the next person.")
    @app_commands.checks.has_permissions(administrator=True)
    async def queuenext(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        queue = self.queues.get(channel_id)
        if not queue or not queue.get('is_active'):
            await self.send_error(interaction, "The queue must be active to use this command.")
            return
        if not queue['users']:
            await self.send_error(interaction, "The queue is empty, cannot advance.")
            return
        queue['current_index'] = (queue['current_index'] + 1) % len(queue['users'])
        await interaction.response.send_message("⏩ Manually advancing to the next person in the queue...", ephemeral=True)
        await self._advance_queue(channel_id)

    # setup a queue in a channel
    @app_commands.command(name="newqueue", description="Creates a new queue in this channel.")
    @app_commands.describe(description="The main message/description for your queue.")
    @app_commands.checks.has_permissions(administrator=True)
    async def newqueue(self, interaction: discord.Interaction, description: str):
        channel_id = interaction.channel.id
        if self.queues.get(channel_id, {}).get('queue_message_id'):
            await self.send_error(interaction, "A queue already exists in this channel. Use `/deletequeue` first.")
            return
        join_emoji = self.queues.get(channel_id, {}).get('join_emoji', DEFAULT_JOIN_EMOJI)
        embed = discord.Embed(
            title="A New Queue has Started!",
            description=f"{description}\n\nReact with {join_emoji} to join the queue.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        queue_message = await interaction.original_response()
        try:
            await queue_message.add_reaction(join_emoji)
        except (discord.HTTPException, discord.Forbidden):
            await self.send_error(interaction, f"Invalid emoji `{join_emoji}`. Make sure it is a standard emoji.")
            await queue_message.delete()
            if 'join_emoji' in self.queues.get(channel_id, {}):
                del self.queues[channel_id]['join_emoji']
            return
        try:
            await queue_message.pin()
            async for msg in interaction.channel.history(limit=10):
                if msg.type == discord.MessageType.pins_add and msg.reference and msg.reference.message_id == queue_message.id:
                    await msg.delete()
                    break
        except discord.Forbidden:
            await interaction.followup.send("⚠️ **Warning:** Make sure to allow pinning and managing messages.", ephemeral=True)

        self.queues.setdefault(channel_id, {})
        self.queues[channel_id].update({
            "queue_message_id": queue_message.id,
            "users": [],
            "is_active": False,
            "current_index": -1,
            "ping_message": None,
            "turn_message_id": None,
            "join_emoji": join_emoji,
            "advance_emoji": self.queues[channel_id].get('advance_emoji', DEFAULT_ADVANCE_EMOJI)
        })

    # command to start running the queue
    @app_commands.command(name="startqueue",
                          description="Starts the queue, randomizing the order and pinging the first person.")
    @app_commands.checks.has_permissions(administrator=True)
    async def startqueue(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        queue = self.queues.get(channel_id)
        if not queue or not queue.get('queue_message_id'):
            await self.send_error(interaction, "No queue found in this channel to start.")
            return
        if queue["is_active"]:
            await self.send_error(interaction, "The queue is already active.")
            return
        if not queue["users"]:
            await self.send_error(interaction, "Cannot start an empty queue. Wait for users to join.")
            return
        random.shuffle(queue["users"])
        queue["is_active"] = True
        queue["current_index"] = 0
        await interaction.response.send_message("✅ Queue started and randomized!", ephemeral=True)
        await self._advance_queue(channel_id)

    # command to change queue message
    @app_commands.command(name="queuemessage",
                          description="Sets the custom message shown in the embed on a user's turn.")
    @app_commands.describe(message="The custom message for the embed (e.g., 'your build is ready!').")
    @app_commands.checks.has_permissions(administrator=True)
    async def queuemessage(self, interaction: discord.Interaction, message: str):
        channel_id = interaction.channel.id
        queue = self.queues.get(channel_id)
        if not queue:
            await self.send_error(interaction, "No queue found in this channel.")
            return
        queue["ping_message"] = message
        await interaction.response.send_message(f"✅ Custom embed message updated to: `{message}`", ephemeral=True)

    # command to delete the queue
    @app_commands.command(name="deletequeue", description="Deletes the current queue in this channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def deletequeue(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        if channel_id not in self.queues:
            await self.send_error(interaction, "There is no queue to delete in this channel.")
            return
        await interaction.response.defer(ephemeral=True)
        try:
            queue_message_id = self.queues[channel_id].get("queue_message_id")
            if queue_message_id:
                queue_message = await interaction.channel.fetch_message(queue_message_id)
                if queue_message.pinned:
                    await queue_message.unpin()
                await queue_message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await interaction.followup.send("⚠️ **Warning:** Make sure to allow pinning and managing messages.", ephemeral=True)
        del self.queues[channel_id]
        await interaction.followup.send("✅ The queue has been successfully deleted.", ephemeral=True)

    # listeners and helpers

    # listener for adding reactions
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id: return
        queue = self.queues.get(payload.channel_id)
        if not queue: return
        user = self.bot.get_user(payload.user_id) or await self.bot.fetch_user(payload.user_id)
        if payload.message_id == queue.get("queue_message_id") and str(payload.emoji) == queue.get("join_emoji"):
            if user.id not in [u.id for u in queue["users"]]:
                if queue["is_active"]:
                    next_pos = (queue["current_index"] + 1) % (len(queue["users"]) + 1)
                    queue["users"].insert(next_pos, user)
                else:
                    queue["users"].append(user)
        elif payload.message_id == queue.get("turn_message_id") and queue.get("is_active"):
            current_user = queue["users"][queue["current_index"]]
            if payload.user_id == current_user.id and str(payload.emoji) == queue.get("advance_emoji"):
                queue["current_index"] = (queue["current_index"] + 1) % len(queue["users"])
                await self._advance_queue(payload.channel_id)
            else:
                try:
                    channel = self.bot.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    await message.remove_reaction(payload.emoji, user)
                except (discord.Forbidden, discord.NotFound):
                    pass

    # listener for removing reactions
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id: return

        if payload.channel_id not in self.queues: return
        queue = self.queues[payload.channel_id]

        if payload.message_id == queue.get("queue_message_id") and str(payload.emoji) == queue.get("join_emoji"):
            user_to_remove_index = next((i for i, user in enumerate(queue["users"]) if user.id == payload.user_id), -1)

            if user_to_remove_index != -1:
                is_current_user = queue["is_active"] and queue["current_index"] == user_to_remove_index
                queue["users"].pop(user_to_remove_index)

                if not queue["users"]:
                    channel = self.bot.get_channel(payload.channel_id)
                    if channel:
                        try:
                            queue_message = await channel.fetch_message(queue.get("queue_message_id"))
                            if queue_message.pinned:
                                await queue_message.unpin()
                            await queue_message.delete()
                        except (discord.NotFound, discord.Forbidden):
                            pass

                    del self.queues[payload.channel_id]
                    await channel.send("👋 Everyone has left the queue, so the queue has been deleted.")
                    return

                if is_current_user:
                    queue["current_index"] %= len(queue["users"])
                    await self._advance_queue(payload.channel_id)
                elif queue["is_active"] and user_to_remove_index < queue["current_index"]:
                    queue["current_index"] -= 1

    # helper to advance queue
    async def _advance_queue(self, channel_id: int):
        queue = self.queues.get(channel_id)
        if not queue or not queue.get("is_active") or not queue.get("users"):
            if queue: queue["is_active"] = False
            return
        channel = self.bot.get_channel(channel_id)
        current_user = queue["users"][queue["current_index"]]
        advance_emoji = queue['advance_emoji']
        custom_message = queue.get("ping_message")
        content_text = f"{current_user.mention}, you are at the front of the queue!"
        embed_description_parts = []
        if custom_message:
            embed_description_parts.append(custom_message)
        embed_description_parts.append(f"React with {advance_emoji} to advance the queue to the next person!")
        embed = discord.Embed(
            description="\n\n".join(embed_description_parts),
            color=discord.Color.green()
        )
        try:
            turn_message = await channel.send(content=content_text, embed=embed)
            await turn_message.add_reaction(advance_emoji)
            queue["turn_message_id"] = turn_message.id
        except (discord.HTTPException, discord.Forbidden):
            await channel.send(
                f"⚠️ **Critical Error:** I can't use the 'next' emoji `{advance_emoji}`. The queue is paused. Please set a new one with `/nextemoji` and use `/queueback` or `/queuenext` to restart.")
            queue['is_active'] = False


async def setup(bot: commands.Bot):
    await bot.add_cog(QueueCog(bot))