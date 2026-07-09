import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import core.hash_engine as hashEngine
import core.db_manager as dbManager
import alerts.log_manager as logManager
from config import BL_FILES


def scanAndRegisterDirectory(directoryPath: str) -> None:
    for dirpath, dirnames, filenames in os.walk(directoryPath):
        for files in filenames:
            filePath = os.path.join(dirpath, files)
            if filePath in BL_FILES:
                continue
            fileHash = hashEngine.calculateFileHash(filePath)
            mtime = int(os.path.getmtime(filePath))
            existingRecord = dbManager.getHashRecord(filePath)
            if existingRecord is None:
                dbManager.insertHashRecord(filePath, fileHash, mtime)
                logManager.logInfo(f"[INIT] Registro creado: {filePath}")
            else:
                dbManager.updateHashRecord(filePath, fileHash, mtime)
                logManager.logInfo(f"[INIT] Registro actualizado: {filePath}")


class IntegrityEventHandler(FileSystemEventHandler):

    def __init__(self, app=None):
        super().__init__()
        self.app = app

    def _notifyApp(self, message: str) -> None:
        if self.app:
            self.app.call_from_thread(self.app.addAlert, message)

    def _shortPath(self, filePath: str) -> str:
        # Muestra solo los ultimos dos segmentos del path
        parts = filePath.split(os.sep)
        return os.sep.join(parts[-2:]) if len(parts) >= 2 else filePath

    def on_modified(self, event):
        if event.is_directory:
            return
        filePath = event.src_path
        if filePath in BL_FILES:
            return
        fileHash = hashEngine.calculateFileHash(filePath)
        query = dbManager.getHashRecord(filePath)
        mtime = int(os.path.getmtime(filePath))
        if query is None:
            dbManager.insertHashRecord(filePath, fileHash, mtime)
            logManager.logInfo(f"[MONITOR] Archivo no registrado, insertando: {filePath}")
            return
        recordedHash = query[1]
        if fileHash == recordedHash:
            logManager.logInfo(f"[MONITOR] Falso positivo en modificación de: {filePath}")
        else:
            logManager.logAlert(f"[ALERTA] Modificación no autorizada: {filePath}")
            self._notifyApp(f"Modificado: {self._shortPath(filePath)}")
        dbManager.updateHashRecord(filePath, fileHash, mtime)

    def on_created(self, event):
        if event.is_directory:
            return
        filePath = event.src_path
        if filePath in BL_FILES:
            return
        fileHash = hashEngine.calculateFileHash(filePath)
        mtime = int(os.path.getmtime(filePath))
        dbManager.insertHashRecord(filePath, fileHash, mtime)
        logManager.logInfo(f"[MONITOR] Nuevo archivo detectado y registrado: {filePath}")
        self._notifyApp(f"Nuevo: {self._shortPath(filePath)}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        filePath = event.src_path
        if filePath in BL_FILES:
            return
        dbManager.markAsDeleted(filePath)
        logManager.logAlert(f"[ALERTA] Archivo eliminado: {filePath}")
        self._notifyApp(f"Eliminado: {self._shortPath(filePath)}")
        if self.app:
            self.app.call_from_thread(self.app.markFileAsDeleted, filePath)


def startMonitoring(directoryPaths: list, app=None) -> None:
    observer = Observer()
    for directoryPath in directoryPaths:
        handler = IntegrityEventHandler(app=app)
        observer.schedule(handler, directoryPath, recursive=True)
        logManager.logInfo(f"[MONITOR] Monitoreo activo en: {directoryPath}")
    observer.start()
    return observer