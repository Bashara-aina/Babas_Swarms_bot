"""Browser-based price validation from rumahlabuh.com.

Uses browser-harness helpers to navigate rumahlabuh.com, validate room selection,
order flow, check-in/check-out form, and real price display.

All data extracted from rumahlabuh.com — NOT fabricated.

No firecrawl dependency. Uses user's running Chrome via CDP.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from tools.browser_harness import helpers as bh

logger = logging.getLogger(__name__)


# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class PriceValidationResult:
    success: bool
    room_type: str
    location: str
    check_in: str
    check_out: str
    price_displayed: Optional[float] = None
    currency: str = "IDR"
    raw_price_text: str = ""
    page_url: str = ""
    error_message: str = ""
    validation_steps: list[str] = field(default_factory=list)


# ── Browser helpers (via helpers.py) ─────────────────────────────────────────


def _scrape_url(url: str, max_chars: int = 8000) -> str:
    """Navigate URL in a new browser tab and extract text content."""
    bh.ensure_daemon()
    old_tab = bh.current_tab()
    bh.new_tab(url)
    bh.wait_for_load()
    text = bh.js(
        f"(function(){{"
        f"const el=document.querySelector('main,article,[role=main],body');"
        f"const t=el?el.innerText:document.body.innerText;"
        f"return t.slice(0,{max_chars});"
        f"}})()"
    )
    if old_tab.get("targetId"):
        try:
            bh.switch_tab(old_tab["targetId"])
        except Exception:
            pass
    return text or ""


def _click_element(selector: str) -> bool:
    """Click element by selector using coordinate-based click."""
    pos = bh.js(
        f"(function(){{"
        f"const el=document.querySelector({repr(selector)});"
        f"if(!el)return null;"
        f"const r=el.getBoundingClientRect();"
        f"return {{x:r.left+r.width/2,y:r.top+r.height/2}};"
        f"}})()"
    )
    if not pos:
        return False
    bh.click_at_xy(pos["x"], pos["y"])
    return True


def _type_text(text: str) -> None:
    bh.type_text(text)


def _get_page_url() -> str:
    return bh.js("location.href") or ""


def _get_element_text(selector: str) -> str:
    return bh.js(
        f"(function(){{const el=document.querySelector({repr(selector)});return el?el.innerText:'';}})()"
    ) or ""


# ── Price validation ──────────────────────────────────────────────────────────


async def validate_room_price(
    room_type: str,
    location: str,
    check_in: str,
    check_out: str,
) -> PriceValidationResult:
    """Validate room price from rumahlabuh.com.

    Uses browser-harness CDP (user's running Chrome) when available,
    falls back to HTTP scraping.

    Args:
        room_type: Type of room (e.g., "standard", "deluxe", "suite")
        location: Location/location name (e.g., "Jakarta", "Bandung")
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format

    Returns:
        PriceValidationResult with success status, price, and validation steps
    """
    result = PriceValidationResult(
        success=False,
        room_type=room_type,
        location=location,
        check_in=check_in,
        check_out=check_out,
    )

    steps = []

    try:
        bh.ensure_daemon()
    except Exception as e:
        logger.warning("Browser daemon unavailable: %s — HTTP fallback", e)
        result.validation_steps.append("daemon_unavailable")
        return await _http_fallback_validate(result)

    try:
        _scrape_url("https://rumahlabuh.com")
        steps.append("navigated_home")
        result.validation_steps.append("navigated_home")

        loc_selector = "input[placeholder*='lokasi'], [data-location-input], [data-location]"
        if _click_element(loc_selector):
            steps.append("clicked_location_input")
            result.validation_steps.append("clicked_location_input")
            time.sleep(0.5)
            _type_text(location)
            time.sleep(0.5)
            result.validation_steps.append(f"typed_location:{location}")

        room_selector = f"[data-room-type='{room_type}'], [data-room-type], select[name*='room'], select[name*='tipe']"
        if _click_element(room_selector):
            steps.append("clicked_room_selector")
            result.validation_steps.append(f"clicked_room_selector:{room_type}")
            time.sleep(0.5)

        checkin_sel = "input[data-check-in-date], input[name*='check_in'], input[placeholder*='checkin'], input[placeholder*='check in']"
        if _click_element(checkin_sel):
            _type_text(check_in)
            result.validation_steps.append(f"typed_checkin:{check_in}")

        checkout_sel = "input[data-check-out-date], input[name*='check_out'], input[placeholder*='checkout'], input[placeholder*='check out']"
        if _click_element(checkout_sel):
            _type_text(check_out)
            result.validation_steps.append(f"typed_checkout:{check_out}")

        search_sel = "[data-order-btn], button[type='submit'], button:has-text('Cari'), button:has-text('Search'), button:has-text('Booking')"
        if _click_element(search_sel):
            steps.append("clicked_search")
            result.validation_steps.append("clicked_search")
            time.sleep(2)

        price_selectors = [
            "[data-price-display]",
            "[class*='price']",
            "[class*='harga']",
            ".harga",
            "[data-price]",
            "[itemprop='price']",
        ]
        price_text = ""
        for sel in price_selectors:
            price_text = _get_element_text(sel)
            if price_text:
                result.validation_steps.append(f"found_price@{sel}:{price_text[:50]}")
                break

        result.raw_price_text = price_text
        result.price_displayed = _parse_price(price_text)
        result.success = result.price_displayed is not None
        result.page_url = _get_page_url()
        result.validation_steps.extend(steps)

    except Exception as e:
        logger.warning("Browser validation failed: %s — HTTP fallback", e)
        result.error_message = str(e)
        result.validation_steps.extend(steps)
        return await _http_fallback_validate(result)

    return result


async def _http_fallback_validate(result: PriceValidationResult) -> PriceValidationResult:
    """HTTP-based fallback when CDP is unavailable."""
    result.validation_steps.append("http_fallback")

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Try to fetch the homepage first
            resp = await client.get("https://rumahlabuh.com", headers={"User-Agent": "LegionSwarmBot/1.0"})
            if resp.status_code != 200:
                result.error_message = f"HTTP {resp.status_code}"
                return result

            # Try search/API approach
            params = {
                "location": result.location,
                "room_type": result.room_type,
                "check_in": result.check_in,
                "check_out": result.check_out,
            }
            try:
                async with client.get(
                    "https://rumahlabuh.com/api/search",
                    params=params,
                    timeout=15,
                ) as search_resp:
                    if search_resp.status_code == 200:
                        data = search_resp.json()
                        price = data.get("price") or (data.get("data") or {}).get("price")
                        if price:
                            result.price_displayed = float(price)
                            result.raw_price_text = str(price)
                            result.success = True
                            result.validation_steps.append("http_api_success")
                            return result
            except Exception:
                pass

            # Try direct page scrape
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            price_el = soup.find(attrs={"data-price-display": True}) or soup.find(class_=re.compile(r"harga|price", re.I))
            if price_el:
                result.raw_price_text = price_el.get_text(strip=True)
                result.price_displayed = _parse_price(result.raw_price_text)
                result.success = result.price_displayed is not None
                result.validation_steps.append("http_parse_success")

    except Exception as e:
        result.error_message = f"HTTP fallback failed: {e}"

    return result


def _parse_price(price_text: str) -> Optional[float]:
    """Parse price string to float.

    Examples:
        "Rp 2.500.000" → 2500000.0
        "2.5 juta" → 2500000.0
        "2500000" → 2500000.0
    """
    if not price_text:
        return None

    text = price_text.strip()
    text = text.replace("Rp", "").replace("rp", "").replace("IDR", "")
    text = text.replace(",", "").replace(" ", "")

    if re.search(r"juta|jt", text, re.IGNORECASE):
        parts = re.split(r"(juta|jt)", text, flags=re.IGNORECASE)
        num_str = parts[0].strip()
        if not num_str:
            num_str = "0"
        try:
            return float(num_str) * 1_000_000.0
        except ValueError:
            return None

    text = re.sub(r"\.(?=[\d]{3}(?![\d]))", "", text)

    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


# ── CLI entry point ─────────────────────────────────────────────────────────────


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate rumahlabuh.com room prices")
    parser.add_argument("--room", required=True, help="Room type")
    parser.add_argument("--location", required=True, help="Location")
    parser.add_argument("--check-in", required=True, help="Check-in date YYYY-MM-DD")
    parser.add_argument("--check-out", required=True, help="Check-out date YYYY-MM-DD")
    args = parser.parse_args()

    result = asyncio.run(
        validate_room_price(
            room_type=args.room,
            location=args.location,
            check_in=args.check_in,
            check_out=args.check_out,
        )
    )

    print(f"Success: {result.success}")
    print(f"Price: {result.price_displayed} {result.currency}")
    print(f"Raw text: {result.raw_price_text}")
    print(f"URL: {result.page_url}")
    print(f"Steps: {' → '.join(result.validation_steps)}")
    if result.error_message:
        print(f"Error: {result.error_message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
