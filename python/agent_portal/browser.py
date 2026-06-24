from __future__ import annotations

from pathlib import Path
from typing import Any

from .exceptions import BrowserOperationError
from .logging_utils import build_logger


class BrowserController:
    def __init__(self, screenshot_directory: Path, timeout_ms: int = 5_000) -> None:
        self.screenshot_directory = screenshot_directory
        self.timeout_ms = timeout_ms
        self._page = None
        self._browser = None
        self._context = None
        self._playwright = None
        self._console_errors: list[str] = []
        self._network_errors: list[str] = []
        self.logger = build_logger("agent_portal.browser")

    def available(self) -> bool:
        try:
            import playwright.sync_api  # noqa: F401
            return True
        except Exception:
            return False

    def start(self) -> None:
        if self._page is not None:
            return

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise BrowserOperationError(
                "Python Playwright is not installed.",
                module="agent_portal.browser",
                likely_cause="The Python runtime dependencies have not been installed.",
                suggested_fix="Run `pip install -e ./python`.",
                can_continue=False,
            ) from exc

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context()
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.timeout_ms)
            self._page.on("console", self._handle_console_message)
            self._page.on("pageerror", self._handle_page_error)
            self._page.on("requestfailed", self._handle_request_failed)
            self.logger.info("Browser session started")
        except Exception as exc:
            self.stop()
            raise BrowserOperationError(
                "Browser failed to launch because Chromium is not installed or not available.",
                module="agent_portal.browser",
                likely_cause="Playwright Chromium is missing or corrupted.",
                suggested_fix="Run `python -m playwright install chromium`.",
                can_continue=False,
            ) from exc

    def stop(self) -> None:
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._console_errors = []
        self._network_errors = []

    def open_url(self, url: str) -> None:
        page = self._require_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
        except Exception as exc:
            raise BrowserOperationError(
                f"Failed to open `{url}`.",
                module="agent_portal.browser",
                likely_cause="The page did not finish loading, the dev server is down, or navigation timed out.",
                suggested_fix="Verify the target URL is reachable and increase the browser timeout if the app is slow.",
                can_continue=True,
            ) from exc

    def screenshot(self, name: str) -> str:
        page = self._require_page()
        self.screenshot_directory.mkdir(parents=True, exist_ok=True)
        file_path = self.screenshot_directory / f"{name}.png"
        try:
            page.screenshot(path=str(file_path), full_page=True)
        except Exception as exc:
            raise BrowserOperationError(
                "Screenshot capture failed.",
                module="agent_portal.browser",
                likely_cause="The page crashed or the screenshot path is not writable.",
                suggested_fix="Check browser health and filesystem permissions for the screenshot directory.",
                can_continue=True,
            ) from exc
        return str(file_path)

    def click(self, selector: str) -> None:
        locator = self._resolve_locator(selector)
        self._ensure_actionable(locator, selector)
        try:
            locator.click(timeout=self.timeout_ms)
        except Exception as exc:
            raise BrowserOperationError(
                f"Click failed for `{selector}`.",
                module="agent_portal.browser",
                likely_cause="The element is covered, detached, or the page is still changing.",
                suggested_fix="Wait for the element to stabilize or use a more specific selector.",
                can_continue=True,
            ) from exc

    def type_text(self, selector: str, value: str) -> None:
        locator = self._resolve_locator(selector)
        self._ensure_actionable(locator, selector)
        try:
            locator.fill(value, timeout=self.timeout_ms)
        except Exception as exc:
            raise BrowserOperationError(
                f"Typing failed for `{selector}`.",
                module="agent_portal.browser",
                likely_cause="The target is read-only, disabled, or not a fillable element.",
                suggested_fix="Use an input selector that resolves to a visible text field.",
                can_continue=True,
            ) from exc

    def hover(self, selector: str) -> None:
        locator = self._resolve_locator(selector)
        self._ensure_actionable(locator, selector)
        try:
            locator.hover(timeout=self.timeout_ms)
        except Exception as exc:
            raise BrowserOperationError(
                f"Hover failed for `{selector}`.",
                module="agent_portal.browser",
                likely_cause="The element is hidden or no longer attached to the page.",
                suggested_fix="Wait for the element to become visible before hovering.",
                can_continue=True,
            ) from exc

    def scroll(self, selector: str | None = None) -> None:
        page = self._require_page()
        try:
            if selector:
                self._resolve_locator(selector).scroll_into_view_if_needed(timeout=self.timeout_ms)
                return
            page.mouse.wheel(0, 800)
        except Exception as exc:
            raise BrowserOperationError(
                "Scroll failed.",
                module="agent_portal.browser",
                likely_cause="The page is not interactive or the target element no longer exists.",
                suggested_fix="Retry after the page settles or scroll the main page instead of a stale element.",
                can_continue=True,
            ) from exc

    def wait(self, selector: str) -> None:
        try:
            self._resolve_locator(selector).wait_for(state="visible", timeout=self.timeout_ms)
        except Exception as exc:
            raise BrowserOperationError(
                f"Wait timed out for `{selector}`.",
                module="agent_portal.browser",
                likely_cause="The element never became visible or the selector is incorrect.",
                suggested_fix="Use a more stable selector or increase the browser timeout for slower pages.",
                can_continue=True,
            ) from exc

    def inspect(self) -> dict[str, Any]:
        page = self._require_page()
        return {
            "url": page.url,
            "title": page.title(),
            "dom": page.content(),
            "consoleErrors": self.read_console(),
            "networkErrors": self.read_network(),
        }

    def current_url(self) -> str | None:
        return self._page.url if self._page else None

    def current_title(self) -> str | None:
        return self._page.title() if self._page else None

    def read_console(self) -> list[str]:
        return list(self._console_errors)

    def read_network(self) -> list[str]:
        return list(self._network_errors)

    def read_text(self, selector: str) -> str | None:
        locator = self._resolve_locator(selector)
        try:
            return locator.text_content(timeout=self.timeout_ms)
        except Exception as exc:
            raise BrowserOperationError(
                f"Failed to read text for `{selector}`.",
                module="agent_portal.browser",
                likely_cause="The target no longer exists or text content could not be resolved.",
                suggested_fix="Target a stable visible element and retry.",
                can_continue=True,
            ) from exc

    def execute(self, script: str) -> Any:
        page = self._require_page()
        try:
            return page.evaluate(script)
        except Exception as exc:
            raise BrowserOperationError(
                "Script execution failed.",
                module="agent_portal.browser",
                likely_cause="The script threw an error or referenced unavailable browser state.",
                suggested_fix="Validate the script against the current page and retry with a simpler expression.",
                can_continue=True,
            ) from exc

    def _resolve_locator(self, selector: str):
        page = self._require_page()
        candidates = [selector]
        normalized = selector.lstrip("#")
        candidates.extend(
            [
                f"#{normalized}",
                f"[name='{normalized}']",
                f"[aria-label='{normalized}']",
                f"text={normalized}",
            ]
        )
        for candidate in candidates:
            locator = page.locator(candidate).first
            try:
                if locator.count() > 0:
                    return locator
            except Exception:
                continue
        lowered = normalized.lower()
        try:
            role_candidates = [
                page.get_by_role("button", name=normalized).first,
                page.get_by_role("link", name=normalized).first,
                page.get_by_role("textbox", name=normalized).first,
            ]
            for locator in role_candidates:
                if locator.count() > 0:
                    return locator
            if lowered.startswith("//"):
                xpath_locator = page.locator(f"xpath={selector}").first
                if xpath_locator.count() > 0:
                    return xpath_locator
        except Exception:
            pass
        raise BrowserOperationError(
            f"Element could not be found for selector `{selector}`.",
            module="agent_portal.browser",
            likely_cause="The selector is stale, hidden, or never existed on the page.",
            suggested_fix="Try a more specific selector, aria-label, visible text, or role target.",
            can_continue=True,
        )

    def _ensure_actionable(self, locator: Any, selector: str) -> None:
        try:
            locator.wait_for(state="visible", timeout=self.timeout_ms)
            if locator.is_disabled():
                raise BrowserOperationError(
                    f"Element `{selector}` is disabled.",
                    module="agent_portal.browser",
                    likely_cause="The control is present but not interactive yet.",
                    suggested_fix="Wait for the app to finish loading or target an enabled element.",
                    can_continue=True,
                )
        except BrowserOperationError:
            raise
        except Exception as exc:
            raise BrowserOperationError(
                f"Element `{selector}` is not actionable.",
                module="agent_portal.browser",
                likely_cause="The target is hidden, detached, or blocked by a modal.",
                suggested_fix="Retry after the page settles or target a visible element inside the active dialog.",
                can_continue=True,
            ) from exc

    def _require_page(self):
        if self._page is None:
            raise BrowserOperationError(
                "Browser session is not ready.",
                module="agent_portal.browser",
                likely_cause="The runtime has not launched the browser yet.",
                suggested_fix="Start the runtime and open a page before issuing browser actions.",
                can_continue=False,
            )
        return self._page

    def _handle_console_message(self, message: Any) -> None:
        if getattr(message, "type", "") == "error":
            self._console_errors.append(message.text)
            self._console_errors = self._console_errors[-20:]

    def _handle_page_error(self, error: Any) -> None:
        self._console_errors.append(str(error))
        self._console_errors = self._console_errors[-20:]

    def _handle_request_failed(self, request: Any) -> None:
        failure = request.failure
        error_text = failure["errorText"] if isinstance(failure, dict) else "unknown failure"
        self._network_errors.append(f"{request.method} {request.url} - {error_text}")
        self._network_errors = self._network_errors[-20:]
