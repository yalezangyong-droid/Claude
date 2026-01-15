#!/usr/bin/env python3
"""
Google Sheets Integration for LinkedIn Scraper (v2 - with Highlighting & Logs)

Features:
- Write scraped posts to Google Sheets
- Highlight new posts with light green background
- Maintain a Scrape Log sheet to track history
- Duplicate detection to avoid re-adding posts

Requirements:
- gspread
- google-auth
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class GoogleSheetsWriter:
    """
    Handles writing LinkedIn posts to Google Sheets with highlighting and logging.
    """

    def __init__(
        self,
        credentials_path: str,
        spreadsheet_id: str,
        sheet_name: str = "Sheet1"
    ):
        """
        Initialize the Google Sheets writer.

        Args:
            credentials_path: Path to the service account JSON file
            spreadsheet_id: The ID of the Google Sheet (from URL)
            sheet_name: Name of the worksheet to write to
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.worksheet: Optional[gspread.Worksheet] = None

        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API using service account."""
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Credentials file not found: {self.credentials_path}"
                )

            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=SCOPES
            )

            self.client = gspread.authorize(credentials)
            logger.info("Successfully authenticated with Google Sheets API")

        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            raise

    def _get_worksheet(self) -> gspread.Worksheet:
        """Get or create the worksheet."""
        try:
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info(f"Opened spreadsheet: {self.spreadsheet.title}")

            # Try to get existing worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet(self.sheet_name)
                logger.info(f"Using existing worksheet: {self.sheet_name}")
            except gspread.WorksheetNotFound:
                # Create new worksheet
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=self.sheet_name,
                    rows=1000,
                    cols=12
                )
                logger.info(f"Created new worksheet: {self.sheet_name}")

            return self.worksheet

        except gspread.SpreadsheetNotFound:
            logger.error(
                f"Spreadsheet not found. Make sure you shared it with: "
                f"the service account email"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to get worksheet: {e}")
            raise

    def _get_or_create_log_sheet(self) -> gspread.Worksheet:
        """Get or create the Scrape Log worksheet."""
        try:
            return self.spreadsheet.worksheet("Scrape Log")
        except gspread.WorksheetNotFound:
            log_sheet = self.spreadsheet.add_worksheet(
                title="Scrape Log",
                rows=1000,
                cols=6
            )
            # Add headers
            log_sheet.update('A1:F1', [[
                "Timestamp",
                "Posts Scraped",
                "New Posts Added",
                "Total in Sheet",
                "Days Back",
                "Status"
            ]])
            log_sheet.format('A1:F1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6}
            })
            log_sheet.format('A1:F1', {
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            logger.info("Created Scrape Log worksheet")
            return log_sheet

    def _setup_headers(self):
        """Set up column headers if they don't exist."""
        headers = [
            "Date",
            "Post URL",
            "Full Content",
            "Likes",
            "Comments",
            "Reposts",
            "Impressions",
            "Post ID",
            "Scraped At",
            "Status"  # NEW column to track new vs existing
        ]

        # Check if first row has headers
        first_row = self.worksheet.row_values(1)

        if not first_row or first_row[0] != headers[0]:
            # Insert headers
            self.worksheet.update('A1:J1', [headers])
            # Format header row (bold)
            self.worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.4}
            })
            self.worksheet.format('A1:J1', {
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            logger.info("Added column headers")

    def _get_existing_post_ids(self) -> set:
        """Get set of existing post IDs to avoid duplicates."""
        try:
            # Post ID is in column H (8th column)
            post_id_col = self.worksheet.col_values(8)
            # Skip header
            return set(post_id_col[1:]) if len(post_id_col) > 1 else set()
        except Exception as e:
            logger.warning(f"Could not get existing post IDs: {e}")
            return set()

    def _clear_previous_highlights(self):
        """Clear previous 'NEW' status and green highlights."""
        try:
            # Get all values in Status column (J)
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:
                return

            # Find rows with "NEW" status and clear them
            updates = []
            for i, row in enumerate(all_values[1:], start=2):  # Skip header
                if len(row) >= 10 and row[9] == "NEW":
                    updates.append({
                        'range': f'J{i}',
                        'values': [['']]
                    })

            if updates:
                self.worksheet.batch_update(updates)
                # Remove green highlighting from previously new rows
                # (keeping it simple - just clear the status)
                logger.info(f"Cleared {len(updates)} previous NEW markers")

        except Exception as e:
            logger.warning(f"Could not clear previous highlights: {e}")

    def _highlight_new_rows(self, start_row: int, end_row: int):
        """Highlight new rows with light green background."""
        try:
            if start_row > end_row:
                return

            # Light green background color
            self.worksheet.format(f'A{start_row}:J{end_row}', {
                'backgroundColor': {
                    'red': 0.85,
                    'green': 0.95,
                    'blue': 0.85
                }
            })
            logger.info(f"Highlighted rows {start_row}-{end_row} in green")

        except Exception as e:
            logger.warning(f"Could not highlight rows: {e}")

    def _add_log_entry(self, posts_scraped: int, new_posts: int, total_in_sheet: int, days_back: int = 30):
        """Add an entry to the Scrape Log sheet."""
        try:
            log_sheet = self._get_or_create_log_sheet()

            # Find next empty row
            all_values = log_sheet.get_all_values()
            next_row = len(all_values) + 1

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = "Success" if new_posts >= 0 else "Error"

            log_sheet.update(f'A{next_row}:F{next_row}', [[
                timestamp,
                posts_scraped,
                new_posts,
                total_in_sheet,
                days_back,
                status
            ]])

            # Color the row based on status
            if new_posts > 0:
                log_sheet.format(f'A{next_row}:F{next_row}', {
                    'backgroundColor': {'red': 0.85, 'green': 0.95, 'blue': 0.85}
                })
            elif new_posts == 0:
                log_sheet.format(f'A{next_row}:F{next_row}', {
                    'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8}
                })

            logger.info(f"Added log entry: {posts_scraped} scraped, {new_posts} new")

        except Exception as e:
            logger.warning(f"Could not add log entry: {e}")

    def write_posts(self, posts: List[Dict], append: bool = True, days_back: int = 30) -> int:
        """
        Write posts to Google Sheet with highlighting.

        Args:
            posts: List of post dictionaries
            append: If True, append to existing data; if False, overwrite
            days_back: Number of days that were scraped (for logging)

        Returns:
            Number of posts written
        """
        if not posts:
            logger.warning("No posts to write")
            self._add_log_entry(0, 0, 0, days_back)
            return 0

        try:
            worksheet = self._get_worksheet()
            self._setup_headers()

            # Clear previous "NEW" markers
            self._clear_previous_highlights()

            # Get existing post IDs to avoid duplicates
            existing_ids = self._get_existing_post_ids() if append else set()
            logger.info(f"Found {len(existing_ids)} existing posts in sheet")

            # Filter out duplicates
            new_posts = [
                p for p in posts
                if p.get('post_id', '') not in existing_ids
            ]

            # Get current total before adding
            all_values = worksheet.get_all_values()
            current_total = len(all_values) - 1 if len(all_values) > 1 else 0

            if not new_posts:
                logger.info("All posts already exist in sheet - no new posts to add")
                self._add_log_entry(len(posts), 0, current_total, days_back)
                return 0

            logger.info(f"Writing {len(new_posts)} new posts to sheet")

            # Prepare rows with "NEW" status
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows = []
            for post in new_posts:
                row = [
                    post.get('publish_date', ''),
                    post.get('post_url', ''),
                    post.get('full_content', ''),
                    post.get('likes', 0),
                    post.get('comments', 0),
                    post.get('reposts', 0),
                    post.get('impressions', 0),
                    post.get('post_id', ''),
                    timestamp,
                    'NEW'  # Mark as new
                ]
                rows.append(row)

            # Find the next empty row
            next_row = len(all_values) + 1 if len(all_values) > 0 else 2

            # Write data
            if rows:
                end_row = next_row + len(rows) - 1
                range_notation = f'A{next_row}:J{end_row}'
                worksheet.update(range_notation, rows)
                logger.info(f"Written {len(rows)} posts to rows {next_row}-{end_row}")

                # Highlight new rows in green
                self._highlight_new_rows(next_row, end_row)

            # Calculate new total
            new_total = current_total + len(rows)

            # Add log entry
            self._add_log_entry(len(posts), len(rows), new_total, days_back)

            return len(rows)

        except Exception as e:
            logger.error(f"Failed to write posts: {e}")
            raise

    def clear_sheet(self, keep_headers: bool = True):
        """Clear all data from the sheet."""
        try:
            worksheet = self._get_worksheet()

            if keep_headers:
                # Clear everything except first row
                worksheet.batch_clear(['A2:Z1000'])
            else:
                worksheet.clear()

            logger.info("Cleared sheet data")

        except Exception as e:
            logger.error(f"Failed to clear sheet: {e}")
            raise


def write_to_sheets(
    posts: List[Dict],
    credentials_path: str,
    spreadsheet_id: str,
    sheet_name: str = "Sheet1",
    append: bool = True,
    days_back: int = 30
) -> int:
    """
    Convenience function to write posts to Google Sheets.

    Args:
        posts: List of post dictionaries
        credentials_path: Path to service account JSON
        spreadsheet_id: Google Sheet ID
        sheet_name: Worksheet name
        append: Append to existing data (default True)
        days_back: Days scraped (for logging)

    Returns:
        Number of posts written
    """
    writer = GoogleSheetsWriter(
        credentials_path=credentials_path,
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name
    )
    return writer.write_posts(posts, append=append, days_back=days_back)


if __name__ == "__main__":
    # Test the integration
    import argparse

    parser = argparse.ArgumentParser(description='Test Google Sheets integration')
    parser.add_argument('--credentials', required=True, help='Path to credentials JSON')
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    parser.add_argument('--sheet-name', default='Sheet1', help='Worksheet name')
    parser.add_argument('--test', action='store_true', help='Write test data')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.test:
        # Test with sample data
        test_posts = [
            {
                'post_id': f'test{datetime.now().timestamp()}',
                'post_url': 'https://linkedin.com/feed/update/test123',
                'publish_date': '2024-01-15 10:00:00',
                'full_content': 'This is a test post #testing #linkedin',
                'likes': 42,
                'comments': 5,
                'reposts': 2,
                'impressions': 1000,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

        count = write_to_sheets(
            posts=test_posts,
            credentials_path=args.credentials,
            spreadsheet_id=args.sheet_id,
            sheet_name=args.sheet_name
        )
        print(f"Written {count} test posts")
    else:
        # Just test authentication
        writer = GoogleSheetsWriter(
            credentials_path=args.credentials,
            spreadsheet_id=args.sheet_id,
            sheet_name=args.sheet_name
        )
        print("Authentication successful!")
        print(f"Spreadsheet: {writer.spreadsheet.title}")
