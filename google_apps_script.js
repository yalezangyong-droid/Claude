/**
 * LinkedIn Scraper - Google Apps Script
 *
 * This script adds a custom menu to your Google Sheet to trigger
 * the LinkedIn scraper with one click.
 *
 * SETUP:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Delete any existing code and paste this entire file
 * 4. Update the SCRAPER_URL below with your ngrok URL
 * 5. Save and refresh your Google Sheet
 * 6. A new "LinkedIn Scraper" menu will appear
 */

// ============================================================
// CONFIGURATION - UPDATE THIS WITH YOUR NGROK URL
// ============================================================
const SCRAPER_URL = "https://YOUR-NGROK-URL.ngrok.io";  // e.g., "https://abc123.ngrok.io"
// ============================================================


/**
 * Creates the custom menu when the spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('LinkedIn Scraper')
    .addItem('Fetch Last 30 Days', 'scrape30Days')
    .addItem('Fetch Last 60 Days', 'scrape60Days')
    .addSeparator()
    .addItem('Check Status', 'checkStatus')
    .addItem('Health Check', 'healthCheck')
    .addToUi();
}


/**
 * Fetch posts from the last 30 days
 */
function scrape30Days() {
  triggerScraper(30);
}


/**
 * Fetch posts from the last 60 days
 */
function scrape60Days() {
  triggerScraper(60);
}


/**
 * Trigger the scraper with specified days
 */
function triggerScraper(days) {
  const ui = SpreadsheetApp.getUi();

  // Validate configuration
  if (SCRAPER_URL === "https://YOUR-NGROK-URL.ngrok.io" || SCRAPER_URL === "") {
    ui.alert(
      'Configuration Required',
      'Please update SCRAPER_URL in the script with your ngrok URL.\n\n' +
      'Go to Extensions > Apps Script and update the SCRAPER_URL variable.',
      ui.ButtonSet.OK
    );
    return;
  }

  try {
    // Show starting message
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `Starting scraper for last ${days} days...`,
      'LinkedIn Scraper',
      5
    );

    // Make API call to trigger scraper
    const response = UrlFetchApp.fetch(`${SCRAPER_URL}/scrape`, {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify({ days: days }),
      muteHttpExceptions: true
    });

    const responseCode = response.getResponseCode();
    const responseBody = JSON.parse(response.getContentText());

    if (responseCode === 200) {
      SpreadsheetApp.getActiveSpreadsheet().toast(
        `Scraper started! ${responseBody.message}`,
        'LinkedIn Scraper',
        10
      );

      // Start polling for status
      pollForCompletion();

    } else if (responseCode === 409) {
      ui.alert(
        'Scraper Busy',
        'The scraper is already running. Please wait for it to complete.',
        ui.ButtonSet.OK
      );
    } else {
      ui.alert(
        'Error',
        `Failed to start scraper: ${responseBody.message || 'Unknown error'}`,
        ui.ButtonSet.OK
      );
    }

  } catch (error) {
    ui.alert(
      'Connection Error',
      `Could not connect to scraper server.\n\n` +
      `Make sure:\n` +
      `1. The server is running (python scraper_server.py)\n` +
      `2. ngrok is running (ngrok http 5000)\n` +
      `3. SCRAPER_URL is correct\n\n` +
      `Error: ${error.message}`,
      ui.ButtonSet.OK
    );
  }
}


/**
 * Poll for scraper completion and show progress
 */
function pollForCompletion() {
  const maxAttempts = 60;  // Poll for up to 5 minutes (60 * 5 seconds)
  let attempts = 0;

  while (attempts < maxAttempts) {
    Utilities.sleep(5000);  // Wait 5 seconds between polls
    attempts++;

    try {
      const response = UrlFetchApp.fetch(`${SCRAPER_URL}/status`, {
        method: 'GET',
        muteHttpExceptions: true
      });

      const status = JSON.parse(response.getContentText());

      if (status.status === 'completed') {
        SpreadsheetApp.getActiveSpreadsheet().toast(
          `✅ Complete! Scraped ${status.posts_scraped} posts, wrote ${status.posts_written_to_sheets} new posts to sheet.`,
          'LinkedIn Scraper',
          30
        );
        return;

      } else if (status.status === 'failed') {
        SpreadsheetApp.getUi().alert(
          'Scraper Failed',
          `Error: ${status.error || 'Unknown error'}`,
          SpreadsheetApp.getUi().ButtonSet.OK
        );
        return;

      } else if (status.status === 'running') {
        SpreadsheetApp.getActiveSpreadsheet().toast(
          `⏳ Still running... (${attempts * 5}s elapsed)`,
          'LinkedIn Scraper',
          5
        );
      }

    } catch (error) {
      // Connection lost, stop polling
      SpreadsheetApp.getActiveSpreadsheet().toast(
        `Connection lost. Check server status manually.`,
        'LinkedIn Scraper',
        10
      );
      return;
    }
  }

  // Timeout
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Polling timeout. Scraper may still be running. Check status manually.`,
    'LinkedIn Scraper',
    10
  );
}


/**
 * Check the current scraper status
 */
function checkStatus() {
  const ui = SpreadsheetApp.getUi();

  if (SCRAPER_URL === "https://YOUR-NGROK-URL.ngrok.io" || SCRAPER_URL === "") {
    ui.alert('Configuration Required', 'Please update SCRAPER_URL first.', ui.ButtonSet.OK);
    return;
  }

  try {
    const response = UrlFetchApp.fetch(`${SCRAPER_URL}/status`, {
      method: 'GET',
      muteHttpExceptions: true
    });

    const status = JSON.parse(response.getContentText());

    let message = `Status: ${status.status.toUpperCase()}\n`;
    message += `Last Run: ${status.last_run || 'Never'}\n`;
    message += `Posts Scraped: ${status.posts_scraped}\n`;
    message += `Posts Written: ${status.posts_written_to_sheets}\n`;

    if (status.error) {
      message += `\nError: ${status.error}`;
    }

    ui.alert('Scraper Status', message, ui.ButtonSet.OK);

  } catch (error) {
    ui.alert(
      'Connection Error',
      `Could not connect to server: ${error.message}`,
      ui.ButtonSet.OK
    );
  }
}


/**
 * Check if the server is healthy
 */
function healthCheck() {
  const ui = SpreadsheetApp.getUi();

  if (SCRAPER_URL === "https://YOUR-NGROK-URL.ngrok.io" || SCRAPER_URL === "") {
    ui.alert('Configuration Required', 'Please update SCRAPER_URL first.', ui.ButtonSet.OK);
    return;
  }

  try {
    const response = UrlFetchApp.fetch(`${SCRAPER_URL}/health`, {
      method: 'GET',
      muteHttpExceptions: true
    });

    if (response.getResponseCode() === 200) {
      const data = JSON.parse(response.getContentText());
      ui.alert(
        'Server Healthy ✅',
        `Server is running!\nTimestamp: ${data.timestamp}`,
        ui.ButtonSet.OK
      );
    } else {
      ui.alert('Server Error', `Server returned: ${response.getResponseCode()}`, ui.ButtonSet.OK);
    }

  } catch (error) {
    ui.alert(
      'Server Offline ❌',
      `Could not connect to server.\n\n` +
      `Make sure the server is running:\n` +
      `1. Run: python scraper_server.py\n` +
      `2. Run: ngrok http 5000\n\n` +
      `Error: ${error.message}`,
      ui.ButtonSet.OK
    );
  }
}
