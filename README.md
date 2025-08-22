## LinkedIn Singapore Checker

This tool reads LinkedIn profile URLs from a Google Sheet, visits each profile using Playwright (authenticated via your LinkedIn `li_at` session cookie), determines whether the profile mentions Singapore, and writes the result back to the sheet.

### Important
- Use responsibly. Automating LinkedIn may violate their Terms of Service. Ensure you have permission and comply with applicable laws and policies.
- Consider LinkedIn's official APIs or manual verification where appropriate.

### Requirements
- Python 3.9+
- A Google Cloud service account with access to Google Sheets API
- The target Google Sheet shared with your service account email
- Your LinkedIn session cookie `li_at` (from your browser while logged in)

### Setup
1. Create a Google Cloud Service Account and download its JSON key.
2. Share your target Google Sheet with the service account email (Viewer or Editor).
3. Save the JSON key file path and export environment variables (see below).
4. Install dependencies and Playwright browser binaries.

### Installation
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### Environment
Create a `.env` file or export variables in your shell:
```bash
# Path to your Service Account JSON
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service_account.json

# LinkedIn session cookie value (from your logged-in browser)
LINKEDIN_LI_AT=replace_with_your_li_at_cookie
```

Optional flags can also be provided via CLI arguments.

### Google Sheets Structure
- Column A: LinkedIn profile URLs (e.g., `https://www.linkedin.com/in/...`)
- Column B: Output result ("Yes"/"No"/"Unknown")

You can customize ranges via CLI flags.

### Usage
```bash
python -m src.cli \
  --sheet-id YOUR_SHEET_ID \
  --read-range "Sheet1!A2:A" \
  --write-start "Sheet1!B2" \
  --service-account-file "$GOOGLE_SERVICE_ACCOUNT_FILE" \
  --li-at "$LINKEDIN_LI_AT" \
  --headless
```

Options:
- `--sheet-id`: Google Sheet ID (from its URL)
- `--read-range`: A1 range with worksheet (e.g., `Sheet1!A2:A`)
- `--write-start`: A1 start cell for output (e.g., `Sheet1!B2`)
- `--service-account-file`: Path to service account JSON (or set `GOOGLE_SERVICE_ACCOUNT_FILE`)
- `--li-at`: LinkedIn `li_at` cookie (or set `LINKEDIN_LI_AT`)
- `--limit`: Process only the first N URLs (optional)
- `--delay-ms`: Delay between requests in ms (default random 1000-2000)
- `--headless/--no-headless`: Run browser headless or visible

### Notes
- Location extraction is heuristic: we search page text for the word "Singapore" (case-insensitive). LinkedIn UI changes can affect reliability.
- For best results, provide valid `li_at` and avoid running too fast (add delays).
- Network or authentication issues will mark entries as "Unknown".