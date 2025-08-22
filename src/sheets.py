import os
from typing import List, Optional, Tuple

import gspread


def _get_client(service_account_file: Optional[str] = None) -> gspread.Client:
	file_path = (
		service_account_file
		or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
		or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
	)
	if not file_path:
		raise RuntimeError(
			"Service account file path not provided. Set GOOGLE_SERVICE_ACCOUNT_FILE or pass --service-account-file."
		)
	return gspread.service_account(filename=file_path)


def _split_a1_range(a1_range: str) -> Tuple[str, str]:
	if "!" not in a1_range:
		raise ValueError("A1 range must include worksheet name, e.g., 'Sheet1!A2:A'")
	worksheet_title, range_in_sheet = a1_range.split("!", 1)
	return worksheet_title, range_in_sheet


def _split_a1_cell(a1_cell: str) -> Tuple[str, int]:
	col = ""
	row_str = ""
	for ch in a1_cell:
		if ch.isalpha():
			col += ch
		elif ch.isdigit():
			row_str += ch
		else:
			raise ValueError(f"Invalid A1 cell: {a1_cell}")
	if not col or not row_str:
		raise ValueError(f"Invalid A1 cell: {a1_cell}")
	return col.upper(), int(row_str)


def _a1_for_column(col: str, row: int) -> str:
	return f"{col}{row}"


def read_urls(sheet_id: str, a1_range: str, service_account_file: Optional[str] = None) -> List[str]:
	client = _get_client(service_account_file)
	ws_title, range_in_sheet = _split_a1_range(a1_range)
	sh = client.open_by_key(sheet_id)
	ws = sh.worksheet(ws_title)
	values = ws.get(range_in_sheet, value_render_option="UNFORMATTED_VALUE") or []
	urls: List[str] = []
	for row in values:
		if not row:
			continue
		val = str(row[0]).strip()
		if val:
			urls.append(val)
	return urls


def write_column(sheet_id: str, start_cell: str, values: List[str], service_account_file: Optional[str] = None) -> None:
	client = _get_client(service_account_file)
	if "!" not in start_cell:
		raise ValueError("start_cell must include worksheet, e.g., 'Sheet1!B2'")
	ws_title, cell = start_cell.split("!", 1)
	col, start_row = _split_a1_cell(cell)
	end_row = start_row + len(values) - 1
	end_cell = _a1_for_column(col, end_row)
	range_a1 = f"{ws_title}!{cell}:{end_cell}"
	data = [[v] for v in values]
	sh = client.open_by_key(sheet_id)
	ws = sh.worksheet(ws_title)
	ws.update(range_a1, data)