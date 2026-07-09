import subprocess
import alerts.log_manager as Logger

def triggerDesktopNotification(title: str, message: str) -> None:
    try:
        subprocess.run(["notify-send", title, message])
    except OSError:
        Logger.logError("[NOTIFIER] notify-send no encontrado en el sistema")