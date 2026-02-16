import os
import webbrowser
import customtkinter as ctk
from PIL import Image, ImageTk
from utils import get_play_store_url, is_valid_play_store_link


class AppUI(ctk.CTk):
    def __init__(self, known_bad, suggested, all_other, uninstall_callback, add_to_db_callback, refresh_callback):
        super().__init__()
        icon_path = os.path.abspath("icon.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception:
            icon = Image.open(icon_path)
            icon = ImageTk.PhotoImage(icon.resize((32, 32)))
            self.iconphoto(True, icon)
        self.title("Android App Cleaner")
        self.geometry("620x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.uninstall_callback = uninstall_callback
        self.add_to_db_callback = add_to_db_callback
        self.refresh_callback = refresh_callback

        self.known_bad = known_bad
        self.suggested = suggested
        self.all_other = all_other
        self.all_apps_expanded = False

        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.main_frame = ctk.CTkFrame(self.scrollable_frame)
        self.main_frame.pack(fill="both", expand=True)

        self.draw_ui()

    def draw_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Header with Refresh Icon
        top_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))

        refresh_icon = "↻"  # Unicode icon alternative
        refresh_btn = ctk.CTkButton(
            top_row,
            text=refresh_icon,
            width=40,
            height=40,
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=10,
            command=self.refresh_callback
        )
        refresh_btn.pack(anchor="w", padx=6, pady=4)

        # Known Bad Apps
        if self.known_bad:
            self.known_label = ctk.CTkLabel(
                self.main_frame, text="🚫 Known Bad Apps", font=ctk.CTkFont(size=18, weight="bold"))
            self.known_label.pack(pady=(10, 5))
            self.known_frames = []
            for pkg in self.known_bad:
                frame = self.create_app_frame(pkg, "known")
                self.known_frames.append(frame)

        # Suggested Suspicious Apps
        if self.suggested:
            self.suggested_label = ctk.CTkLabel(
                self.main_frame, text="⚠️ Suggested Suspicious Apps", font=ctk.CTkFont(size=18, weight="bold"))
            self.suggested_label.pack(pady=(15, 5))
            self.suggested_frames = []
            for pkg in self.suggested:
                frame = self.create_app_frame(pkg, "suggested")
                self.suggested_frames.append(frame)

        # All Other Apps (Expandable)
        if self.all_other:
            self.all_apps_toggle_btn = ctk.CTkButton(
                self.main_frame,
                text=f"📱 Show All Other Apps ({len(self.all_other)}) ▼",
                font=ctk.CTkFont(size=16, weight="bold"),
                command=self.toggle_all_apps,
                fg_color="gray40",
                hover_color="gray30"
            )
            self.all_apps_toggle_btn.pack(pady=(20, 5), fill="x")

            self.all_apps_frame = ctk.CTkFrame(self.main_frame)
            if self.all_apps_expanded:
                self.all_apps_frame.pack(fill="x", pady=(0, 10))
                self.show_all_apps()

        if not self.known_bad and not self.suggested:
            ctk.CTkLabel(
                self.main_frame,
                text="✅ No dodgy apps detected.\nFor deeper cleaning, contact Caleb.",
                font=ctk.CTkFont(size=16)
            ).pack(pady=40)

    def create_app_frame(self, pkg, app_type):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(pady=4, padx=5, fill="x")

        # Package name label
        label = ctk.CTkLabel(frame, text=pkg, anchor="w")
        label.pack(side="left", padx=5, fill="x", expand=True)

        # Button container
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(side="right", padx=5, pady=5)

        # Uninstall button with different behavior based on app type
        if app_type == "known":
            uninstall_btn = ctk.CTkButton(
                button_frame, text="Uninstall", width=80,
                command=lambda p=pkg, f=frame: self.remove_known(p, f))
        elif app_type == "suggested":
            uninstall_btn = ctk.CTkButton(
                button_frame, text="Uninstall", width=80,
                command=lambda p=pkg, f=frame: self.remove_suggested(p, f))
        else:  # all_other
            uninstall_btn = ctk.CTkButton(
                button_frame, text="Uninstall", width=80,
                command=lambda p=pkg, f=frame: self.remove_other_app(p, f))

        uninstall_btn.pack(side="right", padx=(5, 0))

        # Add to known bad button (only for "all_other" apps)
        if app_type == "all_other":
            add_bad_btn = ctk.CTkButton(
                button_frame, text="Mark Bad", width=70,
                command=lambda p=pkg, f=frame: self.mark_as_bad(p, f),
                fg_color="orange", hover_color="darkorange")
            add_bad_btn.pack(side="right", padx=(0, 5))

        # Play Store button (check if valid link exists)
        if is_valid_play_store_link(pkg):
            play_store_btn = ctk.CTkButton(
                button_frame, text="🏪", width=30,
                command=lambda p=pkg: self.open_play_store(p),
                fg_color="green", hover_color="darkgreen")
            play_store_btn.pack(side="right", padx=(0, 5))

        return frame

    def toggle_all_apps(self):
        self.all_apps_expanded = not self.all_apps_expanded

        if self.all_apps_expanded:
            self.all_apps_toggle_btn.configure(
                text=f"📱 Hide All Other Apps ({len(self.all_other)}) ▲")
            self.all_apps_frame.pack(fill="x", pady=(0, 10))
            self.show_all_apps()
        else:
            self.all_apps_toggle_btn.configure(
                text=f"📱 Show All Other Apps ({len(self.all_other)}) ▼")
            self.all_apps_frame.pack_forget()

    def show_all_apps(self):
        # Clear existing content
        for widget in self.all_apps_frame.winfo_children():
            widget.destroy()

        # Add all other apps
        for pkg in sorted(self.all_other):
            frame = ctk.CTkFrame(self.all_apps_frame)
            frame.pack(pady=2, padx=5, fill="x")

            # Package name label
            label = ctk.CTkLabel(frame, text=pkg, anchor="w")
            label.pack(side="left", padx=5, fill="x", expand=True)

            # Button container
            button_frame = ctk.CTkFrame(frame, fg_color="transparent")
            button_frame.pack(side="right", padx=5, pady=3)

            # Uninstall button (simple uninstall without adding to known bad)
            uninstall_btn = ctk.CTkButton(
                button_frame, text="Uninstall", width=80,
                command=lambda p=pkg, f=frame: self.remove_other_app(p, f))
            uninstall_btn.pack(side="right", padx=(5, 0))

            # Mark as bad button
            mark_bad_btn = ctk.CTkButton(
                button_frame, text="Mark Bad", width=70,
                command=lambda p=pkg, f=frame: self.mark_as_bad(p, f),
                fg_color="orange", hover_color="darkorange")
            mark_bad_btn.pack(side="right", padx=(0, 5))

            # Play Store button (check if valid link exists)
            if is_valid_play_store_link(pkg):
                play_store_btn = ctk.CTkButton(
                    button_frame, text="🏪", width=30,
                    command=lambda p=pkg: self.open_play_store(p),
                    fg_color="green", hover_color="darkgreen")
                play_store_btn.pack(side="right", padx=(0, 5))

    def remove_known(self, pkg, frame):
        self.uninstall_callback(pkg)
        self.known_bad.remove(pkg)
        frame.destroy()
        if not self.known_bad and hasattr(self, 'known_label'):
            self.known_label.destroy()
        self.check_empty()

    def remove_suggested(self, pkg, frame):
        self.uninstall_callback(pkg)
        self.add_to_db_callback(pkg)
        self.suggested.remove(pkg)
        frame.destroy()
        if not self.suggested and hasattr(self, 'suggested_label'):
            self.suggested_label.destroy()
        self.check_empty()

    def remove_other_app(self, pkg, frame):
        """Remove app without adding to known bad list."""
        self.uninstall_callback(pkg)
        self.all_other.remove(pkg)
        frame.destroy()
        # Update the toggle button text
        if hasattr(self, 'all_apps_toggle_btn'):
            if self.all_apps_expanded:
                self.all_apps_toggle_btn.configure(
                    text=f"📱 Hide All Other Apps ({len(self.all_other)}) ▲")
            else:
                self.all_apps_toggle_btn.configure(
                    text=f"📱 Show All Other Apps ({len(self.all_other)}) ▼")

    def mark_as_bad(self, pkg, frame):
        """Mark app as bad and move it to known bad list."""
        self.add_to_db_callback(pkg)
        self.all_other.remove(pkg)
        self.known_bad.add(pkg)
        frame.destroy()

        # Update the toggle button text
        if hasattr(self, 'all_apps_toggle_btn'):
            if self.all_apps_expanded:
                self.all_apps_toggle_btn.configure(
                    text=f"📱 Hide All Other Apps ({len(self.all_other)}) ▲")
            else:
                self.all_apps_toggle_btn.configure(
                    text=f"📱 Show All Other Apps ({len(self.all_other)}) ▼")

        # Refresh the UI to show the app in known bad section
        self.refresh_callback()

    def check_empty(self):
        if not self.known_bad and not self.suggested:
            # Don't show empty message if there are other apps
            if not self.all_other:
                for widget in self.main_frame.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(
                    self.main_frame,
                    text="✅ No apps detected.\nFor deeper cleaning, contact Caleb.",
                    font=ctk.CTkFont(size=16)
                ).pack(pady=40)

    def refresh(self, new_known, new_suggested, new_all_other):
        self.known_bad = new_known
        self.suggested = new_suggested
        self.all_other = new_all_other
        self.draw_ui()

    def open_play_store(self, pkg):
        """Open the Google Play Store page for the given package in the default browser."""
        url = get_play_store_url(pkg)
        webbrowser.open(url)
