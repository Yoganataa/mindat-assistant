"""
Handles all non-command text messages sent to the bot.

This module is responsible for routing messages based on the user's
current state. It processes natural language for data logging or for
handling multi-step flows like header creation and renaming.
"""
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from state_manager import StateManager
from services.gsheet_service import GSheetService
from services.nlp_parser import NLPParser
from config import Config
import datetime

# Inline keyboard for the "Stop" button that appears after a successful data entry.
stop_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🛑 Stop Input Mode", callback_data="stop_input")]]
)

class MessageHandler:
    """Handles all text message logic based on user state."""

    def __init__(self, state_manager: StateManager, gsheet_service: GSheetService):
        """Initializes the message handler with required services."""
        self.state_manager = state_manager
        self.gsheet_service = gsheet_service
        self.nlp_parser = NLPParser()

    async def handle_text_message(self, client: Client, message: Message):
        """Routes incoming text messages based on the current user state."""
        user_id = message.from_user.id
        user_state = await self.state_manager.get_user_state(user_id)
        current_mode = user_state.get("mode")
        
        if current_mode == Config.INPUT_MODE:
            await self._handle_input_data(client, message)
        elif current_mode == Config.AWAITING_HEADER_ADD:
            await self._handle_header_add_receive(client, message)
        elif current_mode == Config.AWAITING_HEADER_RENAME_NEW_NAME:
            await self._handle_header_rename_receive(client, message, user_state)
        elif current_mode == Config.AWAITING_UPDATED_ROW_TEXT:
            await self._handle_row_update_receive(client, message, user_state)
        else: # IDLE mode
            await message.reply("💡 Please use the menu buttons to interact with the bot.")
            
    async def _handle_input_data(self, client: Client, message: Message):
        """Processes a user's text message as new data to be logged."""
        user_id = message.from_user.id
        text = message.text.strip()
        
        try:
            spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
            headers = await self.gsheet_service.get_headers(spreadsheet_id, sheet_name)
            
            if not headers:
                await message.reply("⚠️ **Error:** Sheet has no headers!")
                return
            
            # Pass the headers to the parser so it knows what to look for
            parsed_data = self.nlp_parser.parse_transaction(text, headers)
            row_data = self.nlp_parser.to_row_data(parsed_data, headers)
            
            success = await self.gsheet_service.add_row(spreadsheet_id, sheet_name, row_data)
            
            if success:
                # Build a more detailed confirmation message
                response_text = "✅ **Data saved successfully!**\n\n**Detected Values:**\n"
                for key, value in parsed_data.items():
                    if value and key not in ['raw_text']:
                        # Format numbers nicely for readability
                        if isinstance(value, (int, float)):
                            response_text += f"- **{key.replace('_', ' ').title()}:** `{value:,.0f}`\n"
                        else:
                            response_text += f"- **{key.replace('_', ' ').title()}:** `{value}`\n"
                
                response_text += f"\n📊 **Saved to:** {sheet_name}"
                await message.reply(response_text, reply_markup=stop_keyboard)
            else:
                await message.reply("❌ **Failed to save data!**")
                
        except Exception as e:
            await message.reply(f"❌ **Error processing data:**\n`{str(e)}`")

    async def _handle_header_add_receive(self, client: Client, message: Message):
        """Receives and adds the new header name from the user."""
        user_id = message.from_user.id
        new_header = message.text.strip()
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        success = await self.gsheet_service.add_header(spreadsheet_id, sheet_name, new_header)
        if success:
            await message.reply(f"✅ Header **'{new_header}'** has been added successfully.")
        else:
            await message.reply(f"❌ Failed to add header **'{new_header}'**.")
        
        await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE)

    async def _handle_header_rename_receive(self, client: Client, message: Message, user_state: dict):
        """Receives and renames the header with the new name."""
        user_id = message.from_user.id
        new_name = message.text.strip()
        old_name = user_state.get("header_to_rename")
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        if not old_name:
            await message.reply("❌ An error occurred. Please start over from the Header menu.")
            await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE)
            return
            
        success = await self.gsheet_service.rename_header(spreadsheet_id, sheet_name, old_name, new_name)
        if success:
            await message.reply(f"✅ Header **'{old_name}'** has been renamed to **'{new_name}'**.")
        else:
            await message.reply(f"❌ Failed to rename header. Make sure the header exists.")
        
        await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE, header_to_rename=None)

    async def _handle_row_update_receive(self, client: Client, message: Message, user_state: dict):
        """Receives and processes the updated text for a specific row."""
        user_id = message.from_user.id
        new_text = message.text.strip()
        row_number = user_state.get("row_to_edit")
        
        if not row_number:
            await message.reply("❌ An error occurred. Please start the edit process again.")
            await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE)
            return

        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        try:
            headers = await self.gsheet_service.get_headers(spreadsheet_id, sheet_name)
            # Pass headers to the parser for context
            parsed_data = self.nlp_parser.parse_transaction(new_text, headers)
            new_row_data = self.nlp_parser.to_row_data(parsed_data, headers)
            
            success = await self.gsheet_service.update_row(spreadsheet_id, sheet_name, row_number, new_row_data)
            
            if success:
                await message.reply(f"✅ **Row {row_number}** has been successfully updated.")
            else:
                await message.reply(f"❌ Failed to update **Row {row_number}**.")
        
        except Exception as e:
            await message.reply(f"Error processing updated data: {e}")
        
        finally:
            # Reset state after operation
            await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE, row_to_edit=None)