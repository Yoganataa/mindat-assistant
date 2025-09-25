"""
Handles all user commands (e.g., /start) and main menu button presses.

This module is responsible for the primary user interactions that
are not part of a specific data-input flow. It displays welcome
messages, help text, and initiates more complex flows like
header and data management.
"""
from pyrogram import Client
from pyrogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from state_manager import StateManager
from services.gsheet_service import GSheetService
from config import Config

# Inline keyboard to cancel the input mode right after activation.
cancel_input_mode_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("❌ Cancel and Return to Menu", callback_data="stop_input")]]
)

class CommandHandler:
    """A class to handle all bot commands and main menu interactions."""
    
    def __init__(self, state_manager: StateManager, gsheet_service: GSheetService):
        """Initializes the command handler with necessary services."""
        self.state_manager = state_manager
        self.gsheet_service = gsheet_service

    def get_main_menu_keyboard(self) -> ReplyKeyboardMarkup:
        """Creates and returns the main ReplyKeyboardMarkup."""
        keyboard = [
            [KeyboardButton("🆘 Help"), KeyboardButton("🗒️ Input")],
            [KeyboardButton("📝 Header"), KeyboardButton("📒 Sheets")],
            [KeyboardButton("🗃️ Spreadsheets")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    async def start_command(self, client: Client, message: Message):
        """Handles the /start command, showing a welcome message and main menu."""
        user_id = message.from_user.id
        await self.state_manager.get_user_state(user_id) # Initialize state
        await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE)
        
        welcome_text = "🤖 **Welcome to the Admin Bot!**\n\nPlease select an option from the menu below to get started."
        await message.reply(welcome_text, reply_markup=self.get_main_menu_keyboard())
    
    async def help_command(self, client: Client, message: Message):
        """Handles the /help command or 'Help' button, showing usage instructions."""
        help_text = (
            "📖 **Bot Usage Guide**\n\n"
            "**🗒️ Input Menu:**\n"
            "• Press '🗒️ Input' to open the data menu.\n"
            "• You can **Add**, **View**, **Edit**, or **Delete** entries.\n"
            "• When adding/editing, type data naturally, e.g., 'Laptop sold 2 units for 15jt'.\n\n"
            "**📝 Header Management:**\n"
            "• View, add, rename, or delete columns. The 'timestamp' header is mandatory and cannot be changed."
        )
        await message.reply(help_text)

    async def handle_menu_buttons(self, client: Client, message: Message):
        """Routes main menu button presses to the correct handler."""
        text = message.text.strip()
        
        if text == "🆘 Help":
            await self.help_command(client, message)
        elif text == "🗒️ Input":
            await self._handle_input_menu_start(client, message)
        elif text == "📝 Header":
            await self._handle_header_menu(client, message)
        else:
            await message.reply(f"'{text}' feature is not yet implemented.")

    async def _handle_input_menu_start(self, client: Client, message: Message):
        """Displays the data CRUD menu."""
        user_id = message.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        try:
            await self.gsheet_service.ensure_mandatory_header_is_first(spreadsheet_id, sheet_name)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add New Entry", callback_data="data_add_start")],
                [InlineKeyboardButton("📄 View Recent Entries", callback_data="data_view_recent")],
                [InlineKeyboardButton("✏️ Edit an Entry", callback_data="data_edit_start")],
                [InlineKeyboardButton("🗑️ Delete an Entry", callback_data="data_delete_start")]
            ])
            
            await message.reply(
                f"🗒️ **Data Input Menu**\n\n"
                f"You are working on sheet: **'{sheet_name}'**.\n\n"
                f"Please choose an action:",
                reply_markup=keyboard
            )
        except Exception as e:
            await message.reply(f"❌ Error accessing sheet: {e}")

    async def _handle_header_menu(self, client: Client, message: Message):
        """Displays the initial header management menu with inline buttons."""
        user_id = message.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        try:
            await self.gsheet_service.ensure_mandatory_header_is_first(spreadsheet_id, sheet_name)
            
            headers = await self.gsheet_service.get_headers(spreadsheet_id, sheet_name)
            headers_text = f"📝 **Headers in '{sheet_name}':**\n- " + "\n- ".join(headers) if headers else f"📝 **Sheet '{sheet_name}' has no headers yet.**"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Header", callback_data="header_add")],
                [InlineKeyboardButton("✏️ Rename Header", callback_data="header_rename_start")],
                [InlineKeyboardButton("🗑️ Delete Header", callback_data="header_delete_start")],
            ])
            
            await message.reply(f"{headers_text}\n\nSelect an option:", reply_markup=keyboard)
        except Exception as e:
            await message.reply(f"❌ Error accessing headers: {e}")