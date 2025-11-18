"""
Google Sheets Importer for Signal Statistics System
Imports signals from Google Sheets with channel_name, TP, SL fields
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class SheetsImporter:
    """Import signals from Google Sheets into the system"""

    def __init__(self, storage):
        """
        Initialize Google Sheets importer

        Args:
            storage: Storage instance (JSONStorage)
        """
        self.storage = storage
        self.service = None
        self.spreadsheet_id = None
        self._initialize()

    def _initialize(self):
        """Initialize Google Sheets API connection"""
        try:
            # Get credentials from environment
            creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not creds_json:
                logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not found - Sheets import unavailable")
                return

            # Parse JSON credentials
            creds_dict = json.loads(creds_json)

            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )

            # Build service
            self.service = build('sheets', 'v4', credentials=credentials)

            # Get spreadsheet ID
            self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
            if not self.spreadsheet_id:
                logger.warning("GOOGLE_SHEETS_SPREADSHEET_ID not found")
                return

            logger.info(f"✅ Google Sheets API initialized for spreadsheet {self.spreadsheet_id}")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets API: {e}", exc_info=True)

    def read_signals_from_sheet(self, sheet_name: str = "Signals") -> List[Dict[str, Any]]:
        """
        Read signals from Google Sheets

        Expected columns:
        - name: Signal name (optional, auto-generated if missing)
        - channel_name: Telegram channel name (REQUIRED)
        - symbol: Trading pair like BTCUSDT (REQUIRED)
        - exchange: binance/bybit/coinbase (optional, default: binance)
        - take_profit: TP price (REQUIRED)
        - stop_loss: SL price (REQUIRED)
        - target_price: Entry target (optional, uses TP if missing)
        - condition: above/below/equal (optional, default: above)
        - active: TRUE/FALSE (optional, default: TRUE)

        Args:
            sheet_name: Sheet name (default: "Signals")

        Returns:
            List of signal dictionaries
        """
        if not self.service or not self.spreadsheet_id:
            logger.error("Google Sheets API not initialized")
            return []

        try:
            # Read data from sheet (first 200 rows)
            range_name = f"{sheet_name}!A1:J200"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                logger.warning("No data found in Google Sheets")
                return []

            # First row = headers
            headers = [h.lower().strip() for h in values[0]]
            logger.info(f"Found headers: {headers}")

            # Parse rows
            signals = []
            for i, row in enumerate(values[1:], start=2):
                if len(row) < 3:
                    logger.debug(f"Skipping row {i}: not enough columns")
                    continue

                # Create signal dictionary
                signal = {}
                for j, header in enumerate(headers):
                    if j < len(row):
                        signal[header] = row[j].strip() if isinstance(row[j], str) else row[j]
                    else:
                        signal[header] = None

                # Check if active
                active = str(signal.get('active', 'TRUE')).upper()
                if active not in ['TRUE', 'YES', '1', 'Y', '']:
                    logger.debug(f"Skipping inactive signal on row {i}")
                    continue

                # Validate required fields
                if not signal.get('channel_name'):
                    logger.warning(f"Row {i}: Missing channel_name - SKIPPED")
                    continue

                if not signal.get('symbol'):
                    logger.warning(f"Row {i}: Missing symbol - SKIPPED")
                    continue

                if not signal.get('take_profit'):
                    logger.warning(f"Row {i}: Missing take_profit - SKIPPED")
                    continue

                if not signal.get('stop_loss'):
                    logger.warning(f"Row {i}: Missing stop_loss - SKIPPED")
                    continue

                # Convert prices to float
                try:
                    signal['take_profit'] = float(signal['take_profit'])
                    signal['stop_loss'] = float(signal['stop_loss'])

                    # Target price (optional, use TP if not specified)
                    if signal.get('target_price'):
                        signal['target_price'] = float(signal['target_price'])
                    else:
                        signal['target_price'] = signal['take_profit']

                except (ValueError, TypeError) as e:
                    logger.warning(f"Row {i}: Invalid price values - {e}")
                    continue

                # Validate TP > SL
                if signal['take_profit'] <= signal['stop_loss']:
                    logger.warning(f"Row {i}: TP must be > SL - SKIPPED")
                    continue

                # Set defaults
                if not signal.get('exchange'):
                    signal['exchange'] = 'binance'

                if not signal.get('condition'):
                    signal['condition'] = 'above'

                if not signal.get('name'):
                    # Auto-generate name
                    signal['name'] = f"{signal['symbol']} - {signal['channel_name']}"

                signals.append(signal)
                logger.debug(f"Parsed signal from row {i}: {signal['name']}")

            logger.info(f"✅ Successfully read {len(signals)} signals from Google Sheets")
            return signals

        except Exception as e:
            logger.error(f"Failed to read signals from Google Sheets: {e}", exc_info=True)
            return []

    async def import_signals(self, sheet_name: str = "Signals", auto_create_channels: bool = True) -> Dict[str, Any]:
        """
        Import signals from Google Sheets into storage

        Args:
            sheet_name: Sheet name to read from
            auto_create_channels: Automatically create channels if they don't exist

        Returns:
            Dictionary with import results
        """
        from ..models.signal import SignalTarget, SignalCondition, ExchangeType
        from ..services.channel_manager import ChannelManager

        result = {
            'success': False,
            'total_rows': 0,
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'channels_created': []
        }

        try:
            # Read signals from sheet
            signals_data = self.read_signals_from_sheet(sheet_name)
            result['total_rows'] = len(signals_data)

            if not signals_data:
                result['errors'].append("No signals found in sheet")
                return result

            # Initialize channel manager
            channel_manager = ChannelManager(self.storage)

            # Import each signal
            for signal_data in signals_data:
                try:
                    # Check/create channel
                    if auto_create_channels:
                        channel = await channel_manager.get_channel(signal_data['channel_name'])
                        if not channel:
                            channel = await channel_manager.add_channel(
                                name=signal_data['channel_name'],
                                description=f"Auto-imported from Google Sheets"
                            )
                            if channel:
                                result['channels_created'].append(channel.name)
                                logger.info(f"Created channel: {channel.name}")

                    # Map condition
                    condition_map = {
                        'above': SignalCondition.ABOVE,
                        'below': SignalCondition.BELOW,
                        'equal': SignalCondition.EQUAL,
                        '>': SignalCondition.ABOVE,
                        '<': SignalCondition.BELOW,
                        '=': SignalCondition.EQUAL
                    }
                    condition = condition_map.get(
                        signal_data['condition'].lower(),
                        SignalCondition.ABOVE
                    )

                    # Map exchange
                    exchange_map = {
                        'binance': ExchangeType.BINANCE,
                        'bybit': ExchangeType.BYBIT,
                        'coinbase': ExchangeType.COINBASE
                    }
                    exchange = exchange_map.get(
                        signal_data['exchange'].lower(),
                        ExchangeType.BINANCE
                    )

                    # Create signal
                    signal = SignalTarget(
                        name=signal_data['name'],
                        symbol=signal_data['symbol'].upper(),
                        exchange=exchange,
                        target_price=signal_data['target_price'],
                        condition=condition,
                        channel_name=signal_data['channel_name'],
                        take_profit=signal_data['take_profit'],
                        stop_loss=signal_data['stop_loss']
                    )

                    # Save to storage
                    success = await self.storage.save_signal(signal)

                    if success:
                        result['imported'] += 1
                        logger.info(f"Imported: {signal.name}")
                    else:
                        result['skipped'] += 1
                        result['errors'].append(f"Failed to save: {signal.name}")

                except Exception as e:
                    result['skipped'] += 1
                    result['errors'].append(f"Error importing {signal_data.get('name', 'unknown')}: {str(e)}")
                    logger.error(f"Error importing signal: {e}")

            result['success'] = result['imported'] > 0
            logger.info(f"Import complete: {result['imported']} imported, {result['skipped']} skipped")

            return result

        except Exception as e:
            result['errors'].append(f"Import failed: {str(e)}")
            logger.error(f"Import process failed: {e}", exc_info=True)
            return result

    def test_connection(self) -> bool:
        """Test Google Sheets connection"""
        if not self.service or not self.spreadsheet_id:
            return False

        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            title = spreadsheet.get('properties', {}).get('title', 'Unknown')
            logger.info(f"✅ Connected to spreadsheet: {title}")
            return True

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
