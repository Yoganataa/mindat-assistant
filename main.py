"""
Main entry point for the Telegram Admin Bot.

This script initializes all components (Client, Services, Handlers),
registers all message, command, and callback handlers, and starts the bot.
"""
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, BotCommand

from config import Config
from state_manager import StateManager
from services.gsheet_service import GSheetService
from handlers.command_handler import CommandHandler
from handlers.message_handler import MessageHandler
from handlers.callback_handler import CallbackHandler

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """The main class for the Telegram Bot application."""
    
    def __init__(self):
        """Initializes the bot by validating config and setting up all components."""
        try:
            Config.validate()
            self.app = Client(
                "admin_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN
            )
            self.state_manager = StateManager()
            self.gsheet_service = GSheetService()
            self.command_handler = CommandHandler(self.state_manager, self.gsheet_service)
            self.message_handler = MessageHandler(self.state_manager, self.gsheet_service)
            self.callback_handler = CallbackHandler(self.state_manager, self.gsheet_service)
            self._register_handlers()
        except Exception as e:
            logger.critical(f"Bot initialization failed: {e}")
            raise

    def _register_handlers(self):
        """Registers all Pyrogram handlers for the application."""
        
        # Modified: This handler now ONLY listens for the /start command.
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_command(client: Client, message: Message):
            await self.command_handler.start_command(client, message)

        @self.app.on_message(
            filters.regex(r"^(🆘 Help|🗒️ Input|📝 Header|📒 Sheets|🗃️ Spreadsheets)$") 
            & filters.private
        )
        async def menu_buttons(client: Client, message: Message):
            await self.command_handler.handle_menu_buttons(client, message)

        @self.app.on_callback_query()
        async def handle_callbacks(client: Client, callback_query: CallbackQuery):
            """Main router for all callback queries."""
            try:
                await self.callback_handler.handle(client, callback_query)
            except Exception as e:
                logger.error(f"Error in callback handler: {e}")
                await callback_query.answer("An error occurred.", show_alert=True)

        @self.app.on_message(
            filters.text & filters.private & ~filters.command("start") &
            ~filters.regex(r"^(🆘 Help|🗒️ Input|📝 Header|📒 Sheets|🗃️ Spreadsheets)$")
        )
        async def text_messages(client: Client, message: Message):
            await self.message_handler.handle_text_message(client, message)
        
        logger.info("All handlers registered.")

    async def start(self):
        """Starts the bot, loads state, sets commands, and keeps it running."""
        try:
            await self.state_manager.load_states()
            logger.info("User states loaded.")
            
            await self.app.start()
            me = await self.app.get_me()
            logger.info(f"Bot started as @{me.username}")
            
            # Set bot commands on every startup
            logger.info("Setting bot commands...")
            try:
                # Modified: The command list now ONLY contains /start.
                commands = [
                    BotCommand("start", "▶️ Start the bot & show the main menu"),
                ]
                await self.app.set_bot_commands(commands)
                logger.info("Bot commands updated successfully.")
            except Exception as e:
                logger.error(f"Failed to set bot commands: {e}")

            # Keep the bot alive
            await idle()
            
        except Exception as e:
            logger.error(f"Error during bot startup: {e}")
            raise
        finally:
            await self.state_manager.save_states()
            logger.info("User states saved.")
            if self.app.is_connected:
                await self.app.stop()
            logger.info("Bot shutdown complete.")

async def main():
    """Asynchronous main function to run the bot."""
    try:
        bot = TelegramBot()
        await bot.start()
    except Exception as e:
        logger.critical(f"Failed to create or start the bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C).")