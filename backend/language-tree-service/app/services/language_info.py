from __future__ import annotations

import re
import urllib.parse
from typing import Optional, Dict, Tuple

import requests
from bs4 import BeautifulSoup  # type: ignore

from app.models.language import LanguageInfo
from app.services.classification_service import LanguageResolver
from app.services.wikipedia_service import get_wikipedia_language_page_title

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
	"User-Agent": "GenealogyTreeLanguageService/1.0 (language-info)",
	"Accept": "application/json",
}


# -----------------------------
# Helpers: Wikidata lookups
# -----------------------------
def _wikidata_get_entity(qid: str) -> Optional[dict]:
	params = {
		"action": "wbgetentities",
		"ids": qid,
		"format": "json",
		"props": "sitelinks|claims",
	}
	try:
		resp = requests.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=20)
		resp.raise_for_status()
		data = resp.json()
		return data.get("entities", {}).get(qid)
	except Exception as exc:  # pragma: no cover
		print(f"[language_info] Error fetching entity for {qid}: {exc}")
		return None


def _get_enwiki_url_from_entity(entity: dict) -> Optional[str]:
	if not entity:
		return None
	sitelinks = entity.get("sitelinks", {})
	enwiki = sitelinks.get("enwiki") or {}
	title = enwiki.get("title")
	if not title:
		return None
	return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"


def _get_distribution_map_filename(entity: dict) -> Optional[str]:
	"""
	Wikidata property P1846 (distribution map) is usually a Commons media filename.
	Return the filename (e.g., 'File:English language distribution.svg') if present.
	"""
	if not entity:
		return None
	claims = entity.get("claims", {})
	p1846 = claims.get("P1846")
	if not p1846:
		return None
	try:
		for snak in p1846:
			mainsnak = snak.get("mainsnak", {})
			datavalue = mainsnak.get("datavalue", {})
			value = datavalue.get("value")
			if isinstance(value, str) and value:
				return value if value.lower().startswith("file:") else f"File:{value}"
	except Exception:
		pass
	return None


def _commons_file_url(filename: str) -> Optional[str]:
	"""
	Resolve a Commons filename to a full URL via the Commons API.
	"""
	params = {
		"action": "query",
		"format": "json",
		"prop": "imageinfo",
		"titles": filename,
		"iiprop": "url",
	}
	try:
		resp = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=20)
		resp.raise_for_status()
		data = resp.json()
		pages = data.get("query", {}).get("pages", {})
		for page in pages.values():
			info = (page.get("imageinfo") or [{}])[0]
			url = info.get("url")
			if url:
				return url
	except Exception as exc:  # pragma: no cover
		print(f"[language_info] Error resolving Commons file '{filename}': {exc}")
	return None


def get_distribution_map_image(qid: str) -> Optional[str]:
	entity = _wikidata_get_entity(qid)
	filename = _get_distribution_map_filename(entity) if entity else None
	if not filename:
		return None
	return _commons_file_url(filename)


# -----------------------------
# Helpers: Wikipedia infobox parsing
# -----------------------------
def extract_infobox_data(url: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
	headers = {
		"User-Agent": (
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
			"AppleWebKit/537.36 (KHTML, like Gecko) "
			"Chrome/115.0 Safari/537.36"
		)
	}
	try:
		response = requests.get(url, headers=headers, timeout=20)
		if response.status_code != 200:
			print(f"[language_info] Failed to fetch page, status code: {response.status_code}")
			return None, None
		soup = BeautifulSoup(response.text, "html.parser")
		# Try short description from meta first, then og:description
		short_desc = None
		try:
			
			shortdesc_div = soup.find("div", class_="shortdescription")
			if shortdesc_div:
				short_desc = shortdesc_div.get_text(strip=True)
			if not short_desc:
				og_desc = soup.find("meta", attrs={"name": "description"})
				if og_desc and og_desc.get("content"):
					short_desc = og_desc.get("content").strip()
		except Exception:
			short_desc = None
		infobox = soup.find("table", {"class": "infobox"})
		if not infobox:
			# Some language pages may use variant classes like 'infobox vevent' etc.
			infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
		if not infobox:
			return None, short_desc
		data: Dict[str, str] = {}
		for row in infobox.find_all("tr"):
			header = row.find("th")
			cell = row.find("td")
			if header and cell:
				key = header.get_text(strip=True)
				value = cell.get_text(separator=" ", strip=True)
				if key:
					data[key] = value
		return data, short_desc
	except Exception as exc:  # pragma: no cover
		print(f"[language_info] Error parsing infobox from {url}: {exc}")
		return None, None


def _extract_speakers(infobox: Optional[Dict[str, str]]) -> Optional[str]:
	if not infobox:
		return None
	# Only return native speaker counts. Prefer exact keys in order.
	native_keys_exact = [
		"Native speakers",   # Primary label for native speakers
		"L1 speakers",       # Sometimes explicitly marked
		"Signers",           # For sign languages when speakers_label is Signers
	]
	for k in native_keys_exact:
		for infok, val in infobox.items():
			if infok.strip().lower() == k.lower():
				return _normalize_number_like(val)
	# No native-specific label found; do not fall back to total/L2 to avoid showing non-native counts
	return None


def _normalize_number_like(text: str) -> str:
	# keep digits and common separators; strip references like [1]
	clean = re.sub(r"\[\d+\]", "", text)
	clean = re.sub(r"\s+", " ", clean).strip()
	return clean


def _extract_iso_code(infobox: Optional[Dict[str, str]]) -> Optional[str]:
	if not infobox:
		return None
	# Prefer ISO 639-3 if present, else 639-1, else 639-2
	preferences = ["ISO 639-3", "ISO 639-1", "ISO 639-2"]
	for pref in preferences:
		for k, v in infobox.items():
			if k.lower().startswith(pref.lower()):
				return v
	# fallback: any key starting with ISO 639-
	for k, v in infobox.items():
		if k.lower().startswith("iso 639-"):
			return v
	return None


# -----------------------------
# Public API
# -----------------------------
resolver = LanguageResolver()


def get_wikipedia_url_for_qid(qid: str) -> Optional[str]:
	entity = _wikidata_get_entity(qid)
	return _get_enwiki_url_from_entity(entity) if entity else None


def resolve_qid_for_name(name: str) -> Optional[str]:
	try:
		res = resolver.resolve_languages([name])
		info = res.get(name)
		if isinstance(info, dict):
			qid = info.get("qid")
			if isinstance(qid, str):
				return qid
	except Exception as exc:
		print(f"[language_info] Error resolving QID for name '{name}': {exc}")
	return None


def get_wikipedia_url_for_name(name: str) -> Optional[str]:
	title = get_wikipedia_language_page_title(name)
	if not title:
		return None
	return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"


def get_language_info_by_qid(qid: str) -> LanguageInfo:
	distribution = get_distribution_map_image(qid)
	wiki_url = get_wikipedia_url_for_qid(qid)
	infobox, short_desc = extract_infobox_data(wiki_url) if wiki_url else (None, None)
	speakers = _extract_speakers(infobox)
	iso_code = _extract_iso_code(infobox)
	return LanguageInfo(
		speakers=speakers,
		iso_code=iso_code,
		distribution_map_url=distribution,
		short_description=short_desc,
	)


def get_language_info_by_name(name: str) -> Tuple[LanguageInfo, Optional[str]]:
	"""Return LanguageInfo and resolved QID (if found)."""
	qid = resolve_qid_for_name(name)
	if qid:
		info = get_language_info_by_qid(qid)
		return info, qid

	# Fallback: no QID -> try wikipedia by name, infobox only
	wiki_url = get_wikipedia_url_for_name(name)
	infobox, short_desc = extract_infobox_data(wiki_url) if wiki_url else (None, None)
	speakers = _extract_speakers(infobox)
	iso_code = _extract_iso_code(infobox)
	return LanguageInfo(speakers=speakers, iso_code=iso_code, distribution_map_url=None, short_description=short_desc), None

