import random
import re
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional, Tuple

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright


@dataclass
class LocationResult:
	is_singapore: Optional[bool]
	reason_snippet: str
	url: str
	status: str  # "ok" | "auth_failed" | "load_failed"


class LinkedInClient(AbstractContextManager):
	def __init__(self, li_at_cookie: str, headless: bool = True, delay_ms: Optional[int] = None):
		if not li_at_cookie:
			raise ValueError("li_at cookie is required")
		self.li_at_cookie = li_at_cookie
		self.headless = headless
		self.delay_ms = delay_ms
		self._playwright: Optional[Playwright] = None
		self._browser: Optional[Browser] = None
		self._context: Optional[BrowserContext] = None
		self._page: Optional[Page] = None

	def __enter__(self):
		self._playwright = sync_playwright().start()
		self._browser = self._playwright.chromium.launch(headless=self.headless)
		self._context = self._browser.new_context(
			user_agent=(
				"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
				"(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
			),
		)
		# Inject LinkedIn session cookie
		self._context.add_cookies([
			{
				"name": "li_at",
				"value": self.li_at_cookie,
				"domain": ".linkedin.com",
				"path": "/",
				"httpOnly": True,
				"secure": True,
			}
		])
		self._page = self._context.new_page()
		return self

	def __exit__(self, exc_type, exc, tb):
		try:
			if self._context:
				self._context.close()
			if self._browser:
				self._browser.close()
		finally:
			if self._playwright:
				self._playwright.stop()

	def _post_delay(self):
		if self.delay_ms is None:
			delay = random.randint(1000, 2000)
		else:
			delay = max(0, int(self.delay_ms))
		time.sleep(delay / 1000.0)

	def _ensure_authenticated(self) -> bool:
		assert self._page is not None
		try:
			self._page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
			# If redirected to login, URL will contain /login
			if "login" in (self._page.url or ""):
				return False
			return True
		except PlaywrightTimeoutError:
			return False

	def check_profile_singapore(self, url: str) -> LocationResult:
		assert self._page is not None
		# Ensure we are authenticated first (once per session)
		if not self._ensure_authenticated():
			return LocationResult(is_singapore=None, reason_snippet="Auth failed", url=url, status="auth_failed")
		try:
			self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
			# Wait a bit for dynamic content
			try:
				self._page.wait_for_selector("main", timeout=8000)
			except PlaywrightTimeoutError:
				pass
			# Extract visible text
			text = ""
			try:
				text = self._page.locator("main").inner_text(timeout=5000)
			except PlaywrightTimeoutError:
				try:
					text = self._page.inner_text("body", timeout=5000)
				except PlaywrightTimeoutError:
					text = ""
			lower = text.lower()
			match = re.search(r"singapore", lower)
			if match:
				start = max(0, match.start() - 40)
				end = min(len(text), match.end() + 40)
				snippet = text[start:end].replace("\n", " ")
				status = LocationResult(is_singapore=True, reason_snippet=snippet, url=url, status="ok")
			else:
				status = LocationResult(is_singapore=False, reason_snippet="No 'Singapore' found", url=url, status="ok")
		except Exception as e:  # Network or load failure
			status = LocationResult(is_singapore=None, reason_snippet=f"Load failed: {e}", url=url, status="load_failed")
		finally:
			self._post_delay()
		return status