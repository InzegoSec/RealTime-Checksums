import time
import argparse
from alerts.log_manager import initializeLoggers, logInfo, logError
from core.db_manager import initializeDatabase
from core.file_scanner import scanAndRegisterDirectory, startMonitoring
from core.hash_engine import calculateFileHash
from alerts.notifier import triggerDesktopNotification
from ui.dashboard import RealTimeChecksumApp
from config import DEFAULT_MONITOR_PATH
import os


def initializeSystem() -> None:
    initializeLoggers()
    initializeDatabase()
    logInfo("[SYSTEM] Sistema inicializado correctamente")


def runInitialScan(directoryPaths: list) -> None:
    for directoryPath in directoryPaths:
        if not os.path.exists(directoryPath):
            logError(f"[SYSTEM] Directorio no encontrado: {directoryPath}")
            continue
        logInfo(f"[SYSTEM] Escaneando: {directoryPath}")
        scanAndRegisterDirectory(directoryPath)


def handleUpdate(targetPath: str) -> None:
    from core.db_manager import updateHashRecord, insertHashRecord, getHashRecord
    if os.path.isfile(targetPath):
        fileHash = calculateFileHash(targetPath)
        mtime = int(os.path.getmtime(targetPath))
        existing = getHashRecord(targetPath)
        if existing:
            updateHashRecord(targetPath, fileHash, mtime)
        else:
            insertHashRecord(targetPath, fileHash, mtime)
        logInfo(f"[UPDATE] Hash actualizado para: {targetPath}")
        print(f"[OK] Hash actualizado: {targetPath}")
    elif os.path.isdir(targetPath):
        scanAndRegisterDirectory(targetPath)
        logInfo(f"[UPDATE] Directorio re-escaneado: {targetPath}")
        print(f"[OK] Directorio actualizado: {targetPath}")
    else:
        print(f"[ERROR] Ruta no encontrada: {targetPath}")


def parseArguments():
    parser = argparse.ArgumentParser(
        description="RealTimeChecksums - Monitor de integridad de archivos"
    )
    parser.add_argument(
        "--update",
        metavar="RUTA",
        help="Recalcula y guarda el hash de un archivo o directorio como version de confianza"
    )
    parser.add_argument(
        "--monitor",
        metavar="RUTA",
        nargs="+",
        help="Directorios a monitorear (por defecto usa los definidos en config.py)"
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Corre el monitor en segundo plano sin abrir la interfaz"
    )
    return parser.parse_args()


def main():
    args = parseArguments()

    initializeSystem()

    if args.update:
        handleUpdate(args.update)
        return

    directoryPaths = args.monitor if args.monitor else DEFAULT_MONITOR_PATH

    runInitialScan(directoryPaths)

    triggerDesktopNotification(
        "RealTimeChecksums",
        f"Monitoreo activo en {len(directoryPaths)} directorio(s)"
    )

    if args.no_ui:
        logInfo("[SYSTEM] Corriendo en modo sin interfaz")
        print("[RealTimeChecksums] Monitoreo activo. Ctrl+C para detener.")
        observer = startMonitoring(directoryPaths)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
            logInfo("[SYSTEM] Monitor detenido por el usuario")
            print("\n[RealTimeChecksums] Monitor detenido.")
        return

    # Crea la app primero para poder pasar su referencia al handler
    app = RealTimeChecksumApp(observer=None, monitoredPaths=directoryPaths)
    observer = startMonitoring(directoryPaths, app=app)
    app.observer = observer

    app.run()

    observer.stop()
    observer.join()
    logInfo("[SYSTEM] Monitor detenido")


if __name__ == "__main__":
    main()