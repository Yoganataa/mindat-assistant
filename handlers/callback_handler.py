"""
Handles all callback queries from inline keyboard buttons.

This module is the central router for any action triggered by an inline button,
including data/header CRUD operations, cancellations, and confirmations.
"""
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from state_manager import StateManager
from services.gsheet_service import GSheetService
from config import Config

# Keyboard for a generic cancel button
cancel_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]
)

class CallbackHandler:
    """Manages all callback query logic."""

    def __init__(self, state_manager: StateManager, gsheet_service: GSheetService):
        """Initializes the callback handler with necessary services."""
        self.state_manager = state_manager
        self.gsheet_service = gsheet_service

    async def handle(self, client: Client, cb: CallbackQuery):
        """Routes callback queries to the appropriate method."""
        data = cb.data
        
        # General Actions
        if data == "stop_input":
            await self._handle_stop_input(client, cb)
        elif data == "cancel_action":
            await self._handle_cancel_action(client, cb)
        
        # Header CRUD Flow
        elif data == "header_menu":
            await self._show_header_menu(client, cb)
        elif data == "header_add":
            await self._handle_header_add_start(client, cb)
        elif data == "header_rename_start":
            await self._show_headers_for_rename(client, cb)
        elif data.startswith("rename_header_"):
            await self._handle_header_rename_start(client, cb)
        elif data == "header_delete_start":
            await self._show_headers_for_delete(client, cb)
        elif data.startswith("delete_header_"):
            await self._handle_header_delete(client, cb)

        # Data CRUD Flow
        elif data == "data_add_start":
            await self._handle_data_add_start(client, cb)
        elif data == "data_view_recent":
            await self._handle_data_view_recent(client, cb)
        elif data == "data_edit_start":
            await self._show_rows_for_editing(client, cb)
        elif data.startswith("edit_row_"):
            await self._handle_row_edit_start(client, cb)
        elif data == "data_delete_start":
            await self._show_rows_for_deleting(client, cb)
        elif data.startswith("delete_row_"):
            await self._handle_row_delete_confirmation(client, cb)
        elif data.startswith("confirm_delete_"):
            await self._handle_row_delete_confirmed(client, cb)
            
    async def _handle_stop_input(self, client: Client, cb: CallbackQuery):
        """Handles the 'Stop Input Mode' button press."""
        from .command_handler import CommandHandler
        user_id = cb.from_user.id
        await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE)
        await cb.answer("Input mode stopped.")
        temp_command_handler = CommandHandler(self.state_manager, self.gsheet_service)
        await client.send_message(
            chat_id=user_id,
            text="🛑 **Input mode has been stopped.** You are back to the main menu.",
            reply_markup=temp_command_handler.get_main_menu_keyboard()
        )
        await cb.message.edit_reply_markup(reply_markup=None)

    async def _handle_cancel_action(self, client: Client, cb: CallbackQuery):
        """Handles any 'cancel' button press, resetting the user's state."""
        user_id = cb.from_user.id
        await self.state_manager.update_user_state(user_id, mode=Config.IDLE_MODE)
        await cb.message.edit_text("❌ **Action has been cancelled.**")
        await cb.answer("Cancelled.")

    # --- Header CRUD Methods ---
    async def _show_header_menu(self, client: Client, cb: CallbackQuery):
        """Displays the main header management menu."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Header", callback_data="header_add")],
            [InlineKeyboardButton("✏️ Rename Header", callback_data="header_rename_start")],
            [InlineKeyboardButton("🗑️ Delete Header", callback_data="header_delete_start")],
        ])
        await cb.message.edit_text("📝 **Header Management**\n\nSelect an option:", reply_markup=keyboard)

    async def _handle_header_add_start(self, client: Client, cb: CallbackQuery):
        """Prompts user to enter a name for the new header, with a cancel button."""
        await self.state_manager.update_user_state(cb.from_user.id, mode=Config.AWAITING_HEADER_ADD)
        await cb.message.edit_text(
            "Please type the name for the new header column:",
            reply_markup=cancel_keyboard
        )
        await cb.answer()

    async def _show_headers_for_rename(self, client: Client, cb: CallbackQuery):
        """Shows a list of current headers (excluding mandatory) as buttons to be renamed."""
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        headers = await self.gsheet_service.get_headers(spreadsheet_id, sheet_name)
        
        editable_headers = [h for h in headers if h.lower() != Config.MANDATORY_HEADER]
        
        if not editable_headers:
            await cb.answer("No other headers are available to rename.", show_alert=True)
            return

        buttons = [[InlineKeyboardButton(h, callback_data=f"rename_header_{h}")] for h in editable_headers]
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")])
        await cb.message.edit_text("Select the header you want to rename:", reply_markup=InlineKeyboardMarkup(buttons))
    
    async def _handle_header_rename_start(self, client: Client, cb: CallbackQuery):
        """Sets state to await the new name for the selected header, with a cancel button."""
        old_name = cb.data.replace("rename_header_", "")
        await self.state_manager.update_user_state(
            cb.from_user.id,
            mode=Config.AWAITING_HEADER_RENAME_NEW_NAME,
            header_to_rename=old_name
        )
        await cb.message.edit_text(
            f"What is the new name for **'{old_name}'**?",
            reply_markup=cancel_keyboard
        )
        await cb.answer()
        
    async def _show_headers_for_delete(self, client: Client, cb: CallbackQuery):
        """Shows a list of current headers (excluding mandatory) as buttons to be deleted."""
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        headers = await self.gsheet_service.get_headers(spreadsheet_id, sheet_name)
        
        deletable_headers = [h for h in headers if h.lower() != Config.MANDATORY_HEADER]
        
        if not deletable_headers:
            await cb.answer("No other headers are available to delete.", show_alert=True)
            return

        buttons = [[InlineKeyboardButton(f"🗑️ {h}", callback_data=f"delete_header_{h}")] for h in deletable_headers]
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")])
        await cb.message.edit_text(
            "Select the header you want to **delete permanently**:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def _handle_header_delete(self, client: Client, cb: CallbackQuery):
        """Deletes the selected header."""
        header_to_delete = cb.data.replace("delete_header_", "")
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        success = await self.gsheet_service.delete_header(spreadsheet_id, sheet_name, header_to_delete)
        if success:
            await cb.message.edit_text(f"✅ Header **'{header_to_delete}'** and its column have been deleted.")
            await cb.answer("Header deleted!", show_alert=True)
        else:
            await cb.message.edit_text(f"❌ Failed to delete header **'{header_to_delete}'**.")
            await cb.answer("Error!", show_alert=True)
        
    # --- Data CRUD Methods ---
    async def _handle_data_add_start(self, client: Client, cb: CallbackQuery):
        """Activates the data input mode for the user."""
        user_id = cb.from_user.id
        await self.state_manager.update_user_state(user_id, mode=Config.INPUT_MODE)
        await cb.message.edit_text(
            "✅ **Input Mode Activated**\n\n"
            "Start typing your entries. Press 'Cancel' if you change your mind.",
            reply_markup=cancel_keyboard
        )

    async def _handle_data_view_recent(self, client: Client, cb: CallbackQuery):
        """Fetches and displays the last 5 entries."""
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        recent_rows = await self.gsheet_service.get_recent_rows(spreadsheet_id, sheet_name, limit=5)

        if not recent_rows:
            await cb.answer("No recent data found.", show_alert=True)
            return

        response_text = f"📄 **5 Recent Entries in '{sheet_name}':**\n\n"
        for row in recent_rows:
            preview = " | ".join(row['data'][:3])
            response_text += f"`Row {row['row_number']}`: {preview[:50]}...\n"
        
        await cb.message.edit_text(response_text, reply_markup=cancel_keyboard)
        await cb.answer()

    async def _show_rows_for_editing(self, client: Client, cb: CallbackQuery):
        """Shows recent rows as buttons for the user to select for editing."""
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        recent_rows = await self.gsheet_service.get_recent_rows(spreadsheet_id, sheet_name, limit=5)

        if not recent_rows:
            await cb.answer("No recent data to edit.", show_alert=True)
            return
        
        buttons = []
        for row in recent_rows:
            preview = f"Row {row['row_number']}: {row['data'][1][:30]}..."
            buttons.append([InlineKeyboardButton(preview, callback_data=f"edit_row_{row['row_number']}")])
        
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")])
        await cb.message.edit_text("✏️ Select an entry to edit:", reply_markup=InlineKeyboardMarkup(buttons))

    async def _handle_row_edit_start(self, client: Client, cb: CallbackQuery):
        """Sets state to await the updated text for the selected row."""
        row_number = int(cb.data.replace("edit_row_", ""))
        await self.state_manager.update_user_state(
            cb.from_user.id,
            mode=Config.AWAITING_UPDATED_ROW_TEXT,
            row_to_edit=row_number
        )
        await cb.message.edit_text(
            f"Please send the new, complete text for **Row {row_number}**.",
            reply_markup=cancel_keyboard
        )

    async def _show_rows_for_deleting(self, client: Client, cb: CallbackQuery):
        """Shows recent rows as buttons for the user to select for deletion."""
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        recent_rows = await self.gsheet_service.get_recent_rows(spreadsheet_id, sheet_name, limit=5)

        if not recent_rows:
            await cb.answer("No recent data to delete.", show_alert=True)
            return
        
        buttons = []
        for row in recent_rows:
            preview = f"Row {row['row_number']}: {row['data'][1][:30]}..."
            buttons.append([InlineKeyboardButton(f"🗑️ {preview}", callback_data=f"delete_row_{row['row_number']}")])

        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")])
        await cb.message.edit_text("🗑️ Select an entry to delete:", reply_markup=InlineKeyboardMarkup(buttons))
        
    async def _handle_row_delete_confirmation(self, client: Client, cb: CallbackQuery):
        """Asks the user to confirm the deletion of the selected row."""
        row_number = int(cb.data.replace("delete_row_", ""))
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("‼️ YES, DELETE THIS ROW", callback_data=f"confirm_delete_{row_number}")],
            [InlineKeyboardButton("⬅️ No, go back", callback_data="data_delete_start")]
        ])
        await cb.message.edit_text(f"⚠️ Are you sure you want to permanently delete **Row {row_number}**?", reply_markup=keyboard)

    async def _handle_row_delete_confirmed(self, client: Client, cb: CallbackQuery):
        """Performs the deletion after user confirmation."""
        row_number = int(cb.data.replace("confirm_delete_", ""))
        user_id = cb.from_user.id
        spreadsheet_id, sheet_name = await self.state_manager.get_current_sheet_info(user_id)
        
        success = await self.gsheet_service.delete_row(spreadsheet_id, sheet_name, row_number)
        if success:
            await cb.message.edit_text(f"✅ **Row {row_number}** has been deleted successfully.")
            await cb.answer("Row deleted!", show_alert=True)
        else:
            await cb.message.edit_text(f"❌ Failed to delete **Row {row_number}**.")
            await cb.answer("Error!", show_alert=True)