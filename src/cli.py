import argparse
import os
from typing import List

from dotenv import load_dotenv

from .linkedin import LinkedInClient
from .sheets import read_urls, write_column


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Check if LinkedIn profiles mention Singapore and write results to Google Sheets")
	parser.add_argument("--sheet-id", required=True, help="Google Sheet ID")
	parser.add_argument("--read-range", default="Sheet1!A2:A", help="A1 range for input URLs, e.g., 'Sheet1!A2:A'")
	parser.add_argument("--write-start", default="Sheet1!B2", help="A1 start cell to write results, e.g., 'Sheet1!B2'")
	parser.add_argument("--service-account-file", default=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"), help="Path to Google service account JSON")
	parser.add_argument("--li-at", default=os.getenv("LINKEDIN_LI_AT"), help="LinkedIn li_at session cookie")
	parser.add_argument("--limit", type=int, default=None, help="Process only the first N URLs")
	parser.add_argument("--delay-ms", type=int, default=None, help="Delay between requests in ms (default random 1000-2000)")
	parser.add_argument("--headless", dest="headless", action="store_true", help="Run browser headless (default)")
	parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run browser with UI")
	parser.set_defaults(headless=True)
	return parser.parse_args()


def main() -> None:
	load_dotenv()
	args = parse_args()

	urls: List[str] = read_urls(args.sheet_id, args.read_range, args.service_account_file)
	if args.limit is not None:
		urls = urls[: args.limit]
	if not urls:
		print("No URLs to process.")
		return

	if not args.li_at:
		raise SystemExit("Missing LinkedIn li_at cookie. Provide --li-at or set LINKEDIN_LI_AT.")

	results: List[str] = []
	with LinkedInClient(li_at_cookie=args.li_at, headless=args.headless, delay_ms=args.delay_ms) as client:
		for url in urls:
			res = client.check_profile_singapore(url)
			if res.is_singapore is True:
				results.append("Yes")
			elif res.is_singapore is False:
				results.append("No")
			else:
				results.append("Unknown")

	write_column(args.sheet_id, args.write_start, results, args.service_account_file)
	print(f"Processed {len(urls)} URLs. Results written starting at {args.write_start}.")


if __name__ == "__main__":
	main()