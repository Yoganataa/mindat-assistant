"""
Manages user state with persistence to a JSON file.

This module handles loading, saving, and updating user-specific data,
such as their current interaction mode or temporary information needed
for multi-step operations.
"""
import json
import asyncio
import aiofiles
from typing import Dict, Any
from config import Config

class StateManager:
    """A class to manage user states with JSON file persistence."""
    
    def __init__(self, state_file: str = None):
        """Initializes the StateManager."""
        self.state_file = state_file or Config.STATE_FILE
        self._states: Dict[int, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def load_states(self) -> None:
        """Loads states from the JSON file into memory."""
        try:
            async with aiofiles.open(self.state_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                self._states = {int(k): v for k, v in json.loads(content).items()} if content else {}
        except FileNotFoundError:
            self._states = {}
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not parse state file: {e}. Starting with empty state.")
            self._states = {}

    async def save_states(self) -> None:
        """Saves the current states from memory to the JSON file."""
        async with self._lock:
            try:
                async with aiofiles.open(self.state_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(self._states, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error saving states: {e}")

    async def get_user_state(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a user's state, creating a default one if it doesn't exist.
        """
        user_id_str = str(user_id)
        if user_id_str not in self._states:
            self._states[user_id_str] = {
                'mode': Config.IDLE_MODE,
                'current_spreadsheet_id': Config.DEFAULT_SPREADSHEET_ID,
                'current_sheet_name': Config.DEFAULT_SHEET_NAME,
            }
            await self.save_states()
        return self._states[user_id_str]

    async def update_user_state(self, user_id: int, **kwargs: Any) -> None:
        """
        Updates a user's state with any provided key-value pairs.
        This is a flexible method to change mode, store temp data, etc.
        
        Example:
            await state_manager.update_user_state(user_id, mode="input")
            await state_manager.update_user_state(user_id, mode="rename", item="old_name")
        """
        state = await self.get_user_state(user_id)
        state.update(kwargs)
        await self.save_states()
        
    async def is_input_mode(self, user_id: int) -> bool:
        """Checks if the user is currently in INPUT_MODE."""
        state = await self.get_user_state(user_id)
        return state.get('mode') == Config.INPUT_MODE
    
    async def get_current_sheet_info(self, user_id: int) -> tuple[str, str]:
        """Gets the user's currently active spreadsheet ID and sheet name."""
        state = await self.get_user_state(user_id)
        return state['current_spreadsheet_id'], state['current_sheet_name']