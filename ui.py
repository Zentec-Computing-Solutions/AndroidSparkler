import json
import os
import webbrowser
from pathlib import Path

import webview

from utils import get_play_store_url


class _AppBridge:
    __slots__ = (
        "known_bad",
        "suggested",
        "all_other",
        "uninstall_callback",
        "add_to_db_callback",
        "refresh_callback",
    )

    def __init__(self, known_bad, suggested, all_other, uninstall_callback, add_to_db_callback, refresh_callback):
        self.known_bad = set(known_bad)
        self.suggested = set(suggested)
        self.all_other = set(all_other)
        self.uninstall_callback = uninstall_callback
        self.add_to_db_callback = add_to_db_callback
        self.refresh_callback = refresh_callback

    def set_data(self, new_known, new_suggested, new_all_other):
        self.known_bad = set(new_known)
        self.suggested = set(new_suggested)
        self.all_other = set(new_all_other)

    def _package_items(self, packages):
        return [{"pkg": pkg, "has_store": True} for pkg in sorted(packages)]

    def get_state(self):
        known_items = self._package_items(self.known_bad)
        suggested_items = self._package_items(self.suggested)
        other_items = self._package_items(self.all_other)
        return {
            "known_bad": known_items,
            "suggested": suggested_items,
            "all_other": other_items,
            "has_alerts": bool(known_items or suggested_items),
            "empty": not known_items and not suggested_items and not other_items,
        }

    def refresh(self):
        new_known, new_suggested, new_all_other = self.refresh_callback()
        self.set_data(new_known, new_suggested, new_all_other)
        return self.get_state()

    def uninstall_known(self, pkg):
        self.uninstall_callback(pkg)
        self.known_bad.discard(pkg)
        return self.get_state()

    def uninstall_suggested(self, pkg):
        self.uninstall_callback(pkg)
        self.add_to_db_callback(pkg)
        self.suggested.discard(pkg)
        return self.get_state()

    def uninstall_other(self, pkg):
        self.uninstall_callback(pkg)
        self.all_other.discard(pkg)
        return self.get_state()

    def mark_bad(self, pkg):
        self.uninstall_callback(pkg)
        self.add_to_db_callback(pkg)
        self.all_other.discard(pkg)
        self.known_bad.add(pkg)
        return self.get_state()

    def open_play_store(self, pkg):
        webbrowser.open(get_play_store_url(pkg))
        return True


class AppUI:
    def __init__(self, known_bad, suggested, all_other, uninstall_callback, add_to_db_callback, refresh_callback):
        self.bridge = _AppBridge(
            known_bad,
            suggested,
            all_other,
            uninstall_callback,
            add_to_db_callback,
            refresh_callback,
        )
        self.window = None
        self.html_path = os.path.join(os.path.dirname(__file__), "ui.html")

    def set_data(self, new_known, new_suggested, new_all_other):
        self.bridge.set_data(new_known, new_suggested, new_all_other)

    def refresh(self, new_known, new_suggested, new_all_other):
        self.set_data(new_known, new_suggested, new_all_other)
        if self.window:
            state_json = json.dumps(self.bridge.get_state())
            self.window.evaluate_js(f"window.renderState({state_json});")

    def mainloop(self):
        self.window = webview.create_window(
            "Android App Cleaner",
            url=Path(self.html_path).resolve().as_uri(),
            js_api=self.bridge,
            width=920,
            height=800,
        )
        webview.start()
