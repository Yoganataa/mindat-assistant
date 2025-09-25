"""
Service module for all interactions with the Google Sheets API.

This module abstracts the logic for connecting to Google Sheets and performing
CRUD operations on spreadsheets, worksheets, and headers. It uses `gspread`
and runs its synchronous methods in an asyncio-compatible way.
"""
import gspread
import asyncio
from google.oauth2.service_account import Credentials
from typing import List, Dict
from config import Config

class GSheetService:
    """A service class to manage all Google Sheets operations."""
    
    def __init__(self, credentials_file: str = None):
        """Initializes the gspread client using service account credentials."""
        self.credentials_file = credentials_file or Config.GOOGLE_CREDENTIALS_FILE
        self.gc = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Sets up the authorized gspread client instance."""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            self.gc = gspread.authorize(creds)
        except Exception as e:
            print(f"Error initializing Google Sheets client: {e}")
            raise

    async def ensure_mandatory_header_is_first(self, spreadsheet_id: str, sheet_name: str):
        """
        Checks and ensures the mandatory header exists and is in the first column.
        This method will fix the header row if necessary.
        """
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            headers = await self.get_headers(spreadsheet_id, sheet_name)
            mandatory_header = Config.MANDATORY_HEADER
            
            if not headers or headers[0].lower() != mandatory_header:
                print(f"Fixing headers for sheet '{sheet_name}'. Mandatory header rule not met.")
                new_headers = [mandatory_header]
                other_headers = [h for h in headers if h.lower() != mandatory_header]
                new_headers.extend(other_headers)
                
                loop = asyncio.get_event_loop()
                if headers:
                    await loop.run_in_executor(None, worksheet.delete_rows, 1)
                await loop.run_in_executor(None, worksheet.insert_row, new_headers, 1)
                print(f"Headers for sheet '{sheet_name}' have been corrected.")
        except Exception as e:
            print(f"Could not ensure mandatory header: {e}")
            pass

    async def get_worksheet(self, spreadsheet_id: str, sheet_name: str):
        """Asynchronously retrieves a specific worksheet object."""
        try:
            loop = asyncio.get_event_loop()
            spreadsheet = await loop.run_in_executor(None, self.gc.open_by_key, spreadsheet_id)
            return await loop.run_in_executor(None, spreadsheet.worksheet, sheet_name)
        except Exception as e:
            print(f"Error getting worksheet '{sheet_name}': {e}")
            raise

    async def get_headers(self, spreadsheet_id: str, sheet_name: str) -> List[str]:
        """Asynchronously gets the header values (first row) from a worksheet."""
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, worksheet.row_values, 1)
        except Exception as e:
            print(f"Error getting headers: {e}")
            return []

    async def get_recent_rows(self, spreadsheet_id: str, sheet_name: str, limit: int = 5) -> List[Dict]:
        """
        Fetches the most recent rows from the sheet, excluding the header.
        Returns a list of dictionaries, each containing the row number and data.
        """
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            all_values = await loop.run_in_executor(None, worksheet.get_all_values)
            
            data_rows = all_values[1:]
            recent_rows_data = data_rows[-limit:]
            total_rows = len(all_values)
            
            result = []
            for i, row in enumerate(recent_rows_data):
                row_number = total_rows - len(recent_rows_data) + i + 1
                result.append({'row_number': row_number, 'data': row})
            
            return result
        except Exception as e:
            print(f"Error getting recent rows: {e}")
            return []

    async def add_row(self, spreadsheet_id: str, sheet_name: str, row_data: List[str]) -> bool:
        """Asynchronously appends a new row to the specified worksheet."""
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, worksheet.append_row, row_data)
            return True
        except Exception as e:
            print(f"Error adding row: {e}")
            return False

    async def update_row(self, spreadsheet_id: str, sheet_name: str, row_number: int, row_data: List[str]) -> bool:
        """Asynchronously updates a specific row with new data."""
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, worksheet.update, f'A{row_number}', [row_data])
            return True
        except Exception as e:
            print(f"Error updating row {row_number}: {e}")
            return False

    async def delete_row(self, spreadsheet_id: str, sheet_name: str, row_number: int) -> bool:
        """Asynchronously deletes a specific row from the worksheet."""
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, worksheet.delete_rows, row_number)
            return True
        except Exception as e:
            print(f"Error deleting row {row_number}: {e}")
            return False

    async def add_header(self, spreadsheet_id: str, sheet_name: str, header_name: str) -> bool:
        """Adds a new header to the first empty column of the sheet."""
        try:
            await self.ensure_mandatory_header_is_first(spreadsheet_id, sheet_name)
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            headers = await self.get_headers(spreadsheet_id, sheet_name)
            next_col = len(headers) + 1
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, worksheet.update_cell, 1, next_col, header_name)
            return True
        except Exception as e:
            print(f"Error adding header: {e}")
            return False

    async def rename_header(self, spreadsheet_id: str, sheet_name: str, old_name: str, new_name: str) -> bool:
        """Renames an existing header, preventing mandatory header changes."""
        if old_name.lower() == Config.MANDATORY_HEADER:
            print(f"Attempted to rename mandatory header '{old_name}'. Operation denied.")
            return False
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            cell = await loop.run_in_executor(None, lambda: worksheet.find(old_name, in_row=1))
            if not cell:
                return False
            await loop.run_in_executor(None, worksheet.update_cell, 1, cell.col, new_name)
            return True
        except Exception as e:
            print(f"Error renaming header: {e}")
            return False
            
    async def delete_header(self, spreadsheet_id: str, sheet_name: str, header_name: str) -> bool:
        """Deletes a header and its column, preventing mandatory header deletion."""
        if header_name.lower() == Config.MANDATORY_HEADER:
            print(f"Attempted to delete mandatory header '{header_name}'. Operation denied.")
            return False
        try:
            worksheet = await self.get_worksheet(spreadsheet_id, sheet_name)
            loop = asyncio.get_event_loop()
            cell = await loop.run_in_executor(None, lambda: worksheet.find(header_name, in_row=1))
            if not cell:
                return False
            await loop.run_in_executor(None, worksheet.delete_columns, cell.col)
            return True
        except Exception as e:
            print(f"Error deleting header: {e}")
            return False