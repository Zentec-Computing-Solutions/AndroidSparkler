from utils import (
    get_installed_packages, load_known_bad_packages, save_known_bad_packages,
    get_suspicious_packages, get_all_other_packages, uninstall_package
)
from ui import AppUI


def main():
    known_bad = load_known_bad_packages()

    def scan():
        packages = get_installed_packages()
        known, suggested = get_suspicious_packages(packages, known_bad)
        all_other = get_all_other_packages(packages, known, suggested)
        return known, suggested, all_other

    known, suggested, all_other = scan()

    def uninstall(pkg):
        print(f"[-] Uninstalling {pkg}")
        uninstall_package(pkg)

    def add_to_db(pkg):
        known_bad.add(pkg)
        save_known_bad_packages(known_bad)
        print(f"[+] {pkg} added to known bad database")

    def refresh():
        print("[*] Refreshing app list...")
        new_known, new_suggested, new_all_other = scan()
        app.refresh(new_known, new_suggested, new_all_other)

    app = AppUI(known, suggested, all_other, uninstall, add_to_db, refresh)
    app.mainloop()


if __name__ == "__main__":
    main()
