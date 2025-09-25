"""
Service module for Natural Language Processing.

This advanced parser uses a "Header-Driven" approach. It first understands
the columns of the target Google Sheet, then uses that context to extract
structured data from natural language, including performing calculations.
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class NLPParser:
    """An advanced, context-aware parser for dynamic record-keeping."""
    
    def __init__(self):
        """Initializes the parser with entity maps and regex patterns."""
        # Maps various header names (in lowercase) to a standardized entity key.
        self.entity_map = {
            'item_name': ['item', 'nama', 'barang', 'produk', 'deskripsi', 'keterangan'],
            'quantity': ['quantity', 'qty', 'jumlah', 'unit', 'buah'],
            'unit_price': ['harga satuan', 'harga/unit', 'harga per unit', 'satuan'],
            'total_price': ['total', 'total harga', 'harga total', 'amount', 'harga', 'jumlah pengeluaran'],
            'transaction_type': ['type', 'tipe', 'jenis', 'kategori'],
            'profit': ['laba', 'profit', 'keuntungan'],
        }

    def _get_active_entities(self, headers: List[str]) -> Dict[str, str]:
        """
        Determines which entities to look for based on the sheet's headers.
        Returns a map of {standard_entity_key: header_name_from_sheet}.
        """
        active = {}
        headers_lower = [h.lower().strip() for h in headers]
        for entity, synonyms in self.entity_map.items():
            for synonym in synonyms:
                if synonym in headers_lower:
                    # Find the original header name to use as the key
                    original_header = headers[headers_lower.index(synonym)]
                    active[entity] = original_header
                    break
        return active

    def _parse_price_part(self, price_str: str) -> Dict[str, float]:
        """
        Parses complex price strings like "3.6jt/1", "500rb", or "7200000".
        Determines if it's a unit price or total price.
        """
        if not price_str:
            return {}

        price_str = price_str.lower().replace(',', '')
        parts = price_str.split('/')
        
        main_price_str = parts[0]
        per_item_count = int(parts[1]) if len(parts) > 1 else 1

        multiplier = 1
        if 'jt' in main_price_str or 'juta' in main_price_str:
            multiplier = 1_000_000
            main_price_str = re.sub(r'jt|juta', '', main_price_str)
        elif 'rb' in main_price_str or 'ribu' in main_price_str or 'k' in main_price_str:
            multiplier = 1_000
            main_price_str = re.sub(r'rb|ribu|k', '', main_price_str)
            
        try:
            base_price = float(main_price_str.strip()) * multiplier
            # If the price is specified for more than one item, it's a total price.
            # Otherwise, it's a unit price.
            if per_item_count > 1:
                return {'total_price': base_price, 'unit_price': base_price / per_item_count}
            else:
                return {'unit_price': base_price}
        except (ValueError, TypeError):
            return {}

    def _parse_relative_date(self, text: str) -> (datetime, str):
        """Parses relative date phrases and cleans them from the text."""
        now = datetime.now()
        text_lower = text.lower()
        date_found = False
        
        # More complex patterns first
        match = re.search(r'(\d+)\s+hari\s+yang\s+lalu', text_lower)
        if match:
            days = int(match.group(1))
            date = now - timedelta(days=days)
            date_found = True
        elif 'kemarin' in text_lower:
            date = now - timedelta(days=1)
            date_found = True
        elif 'hari ini' in text_lower:
            date = now
            date_found = True
        
        if date_found:
            # Clean the date phrase from the text to avoid confusion
            text = re.sub(r'(\d+\s+hari\s+yang\s+lalu|kemarin|hari\s+ini)\s*', '', text, flags=re.IGNORECASE).strip()
            return date, text
        
        return now, text

    def parse_transaction(self, text: str, headers: List[str]) -> Dict[str, Any]:
        """

        Dynamically parses a text string based on the provided sheet headers.
        """
        active_entities = self._get_active_entities(headers)
        results = {}
        
        # 1. Parse Date first
        transaction_date, clean_text = self._parse_relative_date(text)
        results['timestamp'] = transaction_date.strftime("%Y-%m-%d %H:%M:%S")

        # 2. Extract major numerical parts: quantity and price
        # Regex to find quantity and price parts in various formats
        quantity_match = re.search(r'(\d+)\s*(?:unit|buah|pcs)', clean_text, re.IGNORECASE)
        price_match = re.search(r'(?:harga|seharga|senilai)\s+([\d.,]+(?:jt|juta|rb|ribu|k)?(?:\s*\/\s*\d+)?)', clean_text, re.IGNORECASE)

        if quantity_match:
            results['quantity'] = int(quantity_match.group(1))
            # Remove the found part to simplify item name extraction
            clean_text = clean_text.replace(quantity_match.group(0), '', 1)

        if price_match:
            price_data = self._parse_price_part(price_match.group(1))
            results.update(price_data)
            clean_text = clean_text.replace(price_match.group(0), '', 1)

        # 3. Infer transaction type
        if any(word in clean_text.lower() for word in ['terjual', 'dijual', 'laku']):
            results['transaction_type'] = 'sold'
        elif any(word in clean_text.lower() for word in ['beli', 'dibeli', 'membeli']):
            results['transaction_type'] = 'bought'
        elif any(word in clean_text.lower() for word in ['biaya', 'pengeluaran']):
            results['transaction_type'] = 'expense'

        # 4. Assume what's left is the item name
        # Also remove common action words to clean up the item name
        item_name = re.sub(r'terjual|dijual|laku|beli|dibeli|membeli|biaya|pengeluaran', '', clean_text, flags=re.IGNORECASE).strip()
        results['item_name'] = item_name

        # 5. Post-processing and Calculation
        qty = results.get('quantity')
        unit_price = results.get('unit_price')
        total_price = results.get('total_price')

        if qty and unit_price and 'total_price' in active_entities and not total_price:
            results['total_price'] = qty * unit_price
        if qty and total_price and 'unit_price' in active_entities and not unit_price:
            # Avoid division by zero
            results['unit_price'] = total_price / qty if qty > 0 else 0
            
        return results

    def to_row_data(self, parsed_data: Dict[str, Any], headers: List[str]) -> List[str]:
        """Maps the parsed data dictionary to a list in the correct header order."""
        row_data = [''] * len(headers) # Pre-fill with empty strings
        active_entities = self._get_active_entities(headers)
        
        # Create a reverse map for faster lookup {header_name: entity_key}
        header_to_entity_map = {}
        for entity_key, header_name in active_entities.items():
            header_to_entity_map[header_name] = entity_key

        for i, header in enumerate(headers):
            entity_key = header_to_entity_map.get(header)
            if entity_key and entity_key in parsed_data:
                row_data[i] = str(parsed_data[entity_key] or '')
        
        return row_data