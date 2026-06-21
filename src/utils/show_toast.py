from os import path, system
from sys import platform

from utils.get_file import resource_path

_toast_notifier_cls = None
if platform == "win32":
    try:
        from win10toast import ToastNotifier as _toast_notifier_cls
    except Exception:
        _toast_notifier_cls = None


def show_notification_minim(main_app):
    msg = main_app.text_content["options_menu"]["settings_menu"]["minimization_toast"]
    if platform == "win32":
        if _toast_notifier_cls is None:
            return
        try:
            _toast_notifier_cls().show_toast(
                title="PyMacroRecord",
                msg=msg,
                duration=3,
                icon_path=resource_path(path.join("assets", "logo.ico")),
            )
        except Exception:
            pass
    elif "linux" in platform.lower():
        system(f'notify-send -u normal "PyMacroRecord" "{msg}"')
    elif "darwin" in platform.lower():
        system(f"""osascript -e 'display notification "{msg}" with title "PyMacroRecord"'""")
