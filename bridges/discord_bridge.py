"""Discord bridge — exposes Legion to Discord servers.

Requires: pip install discord.py
Setup:
  1. Create a Discord bot at https://discord.com/developers/applications
  2. Set DISCORD_BOT_TOKEN in .env
  3. Invite bot with scopes: bot + applications.commands
  4. Run: python bridges/discord_bridge.py

Or run alongside Telegram in main.py:
    from bridges.discord_bridge import start_discord_bridge
    asyncio.create_task(start_discord_bridge())
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


async def start_discord_bridge() -> None:
    """Start the Discord bot. Runs as a background asyncio task."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.info("DISCORD_BOT_TOKEN not set — Discord bridge disabled")
        return

    try:
        import discord
    except ImportError:
        logger.warning("discord.py not installed — run: pip install discord.py")
        return

    try:
        import llm_client
        from core.multi_user import MultiUserAuth
    except ImportError as e:
        logger.error("Legion imports failed for Discord bridge: %s", e)
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    auth = MultiUserAuth()

    # Map Discord user_id -> thread_id
    _discord_threads: dict[int, str] = {}

    @client.event
    async def on_ready():
        logger.info("Discord bridge connected as %s (id=%d)", client.user, client.user.id)

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        content = message.content.strip()
        if not content:
            return

        # Only respond to DMs or messages that mention the bot or start with !
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = client.user in (message.mentions or [])
        is_command = content.startswith("!")

        if not (is_dm or is_mention or is_command):
            return

        # Strip bot mention and ! prefix
        if is_mention:
            content = content.replace(f"<@{client.user.id}>", "").strip()
        if is_command:
            content = content.lstrip("!").strip()

        if not content:
            await message.reply("Legion AI ready. Ask me anything!")
            return

        async with message.channel.typing():
            try:
                thread_id = _discord_threads.get(message.author.id)
                response, model_used = await llm_client.chat(
                    content,
                    agent_key="general",
                    thread_id=thread_id,
                    user_id=str(message.author.id),
                )
                # Split response for Discord 2000-char limit
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
            except Exception as e:
                await message.reply(f"\u274c Error: {str(e)[:200]}")
                logger.error("Discord bridge error: %s", e)

    await client.start(token)
