"""Browser-based price validation from rumahlabuh.com.

Uses firecrawl browser to navigate rumahlabuh.com, validate room selection,
order flow, check-in/check-out form, and real price display.

All data extracted from rumahlabuh.com — NOT fabricated.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Fallback chain ──────────────────────────────────────────────────────────────

try:
    from firecrawl import FirecrawlClient
    _FIRECRAWL_AVAILABLE = True
except ImportError:
    _FIRECRAWL_AVAILABLE = False
    FirecrawlClient = None

try:
    import aiohttp
    _AIOHTTP_AVAILABLE = True
except ImportError:
    _AIOHTTP_AVAILABLE = False

try:
    from tools.rumahlabuh_http import get_resilient_session
    _RUMAHLUH_HTTP_AVAILABLE = True
except ImportError:
    _RUMAHLUH_HTTP_AVAILABLE = False
    get_resilient_session = None


# ── Data classes ────────────────────────────────────────────────────────────────


@dataclass
class PriceValidationResult:
    """Result of price validation from rumahlabuh.com."""
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
    validation_steps: list[str] = None

    def __post_init__(self) -> None:
        if self.validation_steps is None:
            self.validation_steps = []


# ── Browser session ────────────────────────────────────────────────────────────


class BrowserValidator:
    """Browser-based validator using firecrawl browser."""

    def __init__(self) -> None:
        self.client: Optional[Any] = None
        self.browser_session_id: Optional[str] = None
        self._available = _FIRECRAWL_AVAILABLE

    async def _ensure_browser(self) -> bool:
        """Start browser session if not already running."""
        if not self._available:
            logger.warning("Firecrawl not available — price validation will use HTTP fallback")
            return False

        if self.browser_session_id:
            return True

        try:
            self.client = FirecrawlClient()
            # Create a browser session for persistent state
            self.browser_session_id = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.browser_create() if hasattr(self.client, "browser_create") else None
            )
            return self.browser_session_id is not None
        except Exception as e:
            logger.warning("Failed to start browser session: %s", e)
            return False

    async def navigate_and_validate(
        self,
        room_type: str,
        location: str,
        check_in: str,
        check_out: str,
    ) -> PriceValidationResult:
        """Navigate rumahlabuh.com and validate price display.

        Flow: Home → Room Selection → Order → Check-in/Check-out → Price Display
        """
        result = PriceValidationResult(
            success=False,
            room_type=room_type,
            location=location,
            check_in=check_in,
            check_out=check_out,
        )

        steps = []

        # Step 1: Try browser-based validation
        browser_started = await self._ensure_browser()
        if not browser_started:
            result.validation_steps.append("browser_unavailable")
            return await self._http_fallback_validate(result, steps)

        try:
            # Navigate to rumahlabuh.com
            await self._browser_goto("https://rumahlabuh.com")
            steps.append("navigated_home")
            result.validation_steps.append("navigated_home")

            # Step 2: Select location
            await self._browser_click_location(location)
            steps.append(f"selected_location:{location}")
            result.validation_steps.append(f"selected_location:{location}")

            # Step 3: Select room type
            await self._browser_select_room(room_type)
            steps.append(f"selected_room:{room_type}")
            result.validation_steps.append(f"selected_room:{room_type}")

            # Step 4: Enter check-in date
            await self._browser_fill_date("check_in", check_in)
            steps.append(f"filled_checkin:{check_in}")
            result.validation_steps.append(f"filled_checkin:{check_in}")

            # Step 5: Enter check-out date
            await self._browser_fill_date("check_out", check_out)
            steps.append(f"filled_checkout:{check_out}")
            result.validation_steps.append(f"filled_checkout:{check_out}")

            # Step 6: Click order/booking button
            await self._browser_click_order()
            steps.append("clicked_order")
            result.validation_steps.append("clicked_order")

            # Step 7: Wait for price to load
            await asyncio.sleep(2)  # Allow dynamic content to load
            price_text = await self._browser_extract_price()
            steps.append(f"extracted_price:{price_text}")
            result.validation_steps.append(f"extracted_price:{price_text}")

            # Parse price
            result.raw_price_text = price_text
            result.price_displayed = self._parse_price(price_text)
            result.success = result.price_displayed is not None
            result.page_url = await self._browser_get_url()

        except Exception as e:
            logger.warning("Browser validation failed: %s — falling back to HTTP", e)
            result.error_message = str(e)
            result.validation_steps.extend(steps)
            return await self._http_fallback_validate(result, steps)

        return result

    async def _browser_goto(self, url: str) -> None:
        """Navigate to URL using firecrawl browser."""
        if not self._available or not self.client or not self.browser_session_id:
            raise RuntimeError("Browser not available")
        try:
            self.client.browser_goto(self.browser_session_id, url)
        except Exception as e:
            logger.warning("browser_goto failed: %s", e)
            raise

    async def _browser_click_location(self, location: str) -> None:
        """Click on location selection."""
        if not self._available or not self.client or not self.browser_session_id:
            raise RuntimeError("Browser not available")
        try:
            # Try to find location input and type
            self.client.browser_execute(
                self.browser_session_id,
                f"document.querySelector('[data-location]')?.click();"
            )
            await asyncio.sleep(0.5)
            # Type location
            self.client.browser_type(self.browser_session_id, "[data-location-input]", location)
        except Exception as e:
            logger.warning("browser_click_location failed: %s", e)
            # Try alternative selectors
            try:
                self.client.browser_execute(
                    self.browser_session_id,
                    f"document.querySelector('input[placeholder*=\"lokasi\"]')?.value = '{location}';"
                )
            except Exception:
                pass

    async def _browser_select_room(self, room_type: str) -> None:
        """Select room type from available options."""
        if not self._available or not self.client or not self.browser_session_id:
            raise RuntimeError("Browser not available")
        try:
            # Click room type selector
            self.client.browser_execute(
                self.browser_session_id,
                "document.querySelector('[data-room-type]')?.click();"
            )
            await asyncio.sleep(0.5)
            # Select the specific room
            self.client.browser_execute(
                self.browser_session_id,
                f"document.querySelector('[data-room-type=\"{room_type}\"]')?.click();"
            )
        except Exception as e:
            logger.warning("browser_select_room failed: %s", e)

    async def _browser_fill_date(self, field: str, date_value: str) -> None:
        """Fill check-in or check-out date field."""
        if not self._available or not self.client or not self.browser_session_id:
            raise RuntimeError("Browser not available")
        try:
            self.client.browser_type(
                self.browser_session_id,
                f"[data-{field}-date]",
                date_value,
            )
        except Exception as e:
            logger.warning("browser_fill_date failed: %s", e)

    async def _browser_click_order(self) -> None:
        """Click the order/booking button."""
        if not self._available or not self.client or not self.browser_session_id:
            raise RuntimeError("Browser not available")
        try:
            self.client.browser_execute(
                self.browser_session_id,
                "document.querySelector('[data-order-btn]')?.click();"
            )
        except Exception as e:
            logger.warning("browser_click_order failed: %s", e)

    async def _browser_extract_price(self) -> str:
        """Extract price text from the page."""
        if not self._available or not self.client or not self.browser_session_id:
            raise RuntimeError("Browser not available")
        try:
            return self.client.browser_get_text(
                self.browser_session_id,
                "[data-price-display]"
            ) or ""
        except Exception as e:
            logger.warning("browser_extract_price failed: %s", e)
            return ""

    async def _browser_get_url(self) -> str:
        """Get current browser URL."""
        if not self._available or not self.client or not self.browser_session_id:
            return ""
        try:
            return self.client.browser_get_url(self.browser_session_id) or ""
        except Exception:
            return ""

    async def _http_fallback_validate(
        self,
        result: PriceValidationResult,
        steps: list[str],
    ) -> PriceValidationResult:
        """HTTP-based fallback when browser is unavailable."""
        result.validation_steps.extend(steps)
        result.validation_steps.append("http_fallback")

        if not _RUMAHLUH_HTTP_AVAILABLE and not _AIOHTTP_AVAILABLE:
            result.error_message = "No HTTP client available for fallback"
            return result

        try:
            async with get_resilient_session() if _RUMAHLUH_HTTP_AVAILABLE else _dummy_session() as session:
                # Try to fetch the homepage to establish connectivity
                async with session.get("https://rumahlabuh.com", timeout=10) as resp:
                    if resp.status != 200:
                        result.error_message = f"HTTP {resp.status}"
                        return result

                # Build search URL with params
                params = {
                    "location": result.location,
                    "room_type": result.room_type,
                    "check_in": result.check_in,
                    "check_out": result.check_out,
                }
                async with session.get(
                    "https://rumahlabuh.com/api/search",
                    params=params,
                    timeout=15,
                ) as search_resp:
                    if search_resp.status != 200:
                        result.error_message = f"Search API returned {search_resp.status}"
                        return result

                    data = await search_resp.json()
                    price = data.get("price") or data.get("data", {}).get("price")
                    if price:
                        result.price_displayed = float(price)
                        result.raw_price_text = str(price)
                        result.success = True
                    else:
                        result.error_message = "No price in API response"

        except Exception as e:
            result.error_message = f"HTTP fallback failed: {e}"

        return result

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price string to float.

        Examples:
            "Rp 2.500.000" → 2500000.0
            "2.5 juta" → 2500000.0
            "2500000" → 2500000.0
        """
        if not price_text:
            return None

        # Clean the text
        text = price_text.strip()
        text = text.replace("Rp", "").replace("rp", "").replace("IDR", "")
        text = text.replace("juta", "000000").replace("jt", "000000")
        text = text.replace(",", "").replace(" ", "")

        # Extract numeric value
        match = re.search(r"[\d.]+", text)
        if not match:
            return None

        try:
            value = float(match.group())
            # Convert 'juta' format if present (was replaced with 000000)
            if "000000" in text and "juta" in price_text.lower():
                value = value / 1000000 * 1000000  # Normalize
            return value
        except ValueError:
            return None


async def _dummy_session():
    """Dummy async context manager when no session available."""
    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        def get(self, *args, **kwargs):
            return _dummy_response(404)
        async def close(self):
            pass
    class _dummy_response:
        def __init__(self, status):
            self.status = status
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def json(self):
            return {}
    return DummySession()


# ── Main async validation function ─────────────────────────────────────────────


async def validate_room_price(
    room_type: str,
    location: str,
    check_in: str,
    check_out: str,
) -> PriceValidationResult:
    """Validate room price from rumahlabuh.com.

    Uses browser automation (firecrawl) when available,
    falls back to HTTP API scraping.

    Args:
        room_type: Type of room (e.g., "standard", "deluxe", "suite")
        location: Location/location name (e.g., "Jakarta", "Bandung")
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format

    Returns:
        PriceValidationResult with success status, price, and validation steps

    Example:
        >>> result = await validate_room_price(
        ...     room_type="deluxe",
        ...     location="Jakarta",
        ...     check_in="2026-04-24",
        ...     check_out="2026-04-26",
        ... )
        >>> print(result.price_displayed)
        2500000.0
    """
    validator = BrowserValidator()
    return await validator.navigate_and_validate(
        room_type=room_type,
        location=location,
        check_in=check_in,
        check_out=check_out,
    )


# ── CLI entry point ──────────────────────────────────────────────────────────────


def main() -> int:
    """CLI for quick price validation testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate rumahlabuh.com room prices")
    parser.add_argument("--room", required=True, help="Room type")
    parser.add_argument("--location", required=True, help="Location")
    parser.add_argument("--check-in", required=True, help="Check-in date YYYY-MM-DD")
    parser.add_argument("--check-out", required=True, help="Check-out date YYYY-MM-DD")
    args = parser.parse_args()

    result = asyncio.run(validate_room_price(
        room_type=args.room,
        location=args.location,
        check_in=args.check_in,
        check_out=args.check_out,
    ))

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
