from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem, Label, Header, Footer
from textual.containers import Horizontal, Vertical
from core.db_manager import getHashRecord
from config import DB_PATH, LOG_DIR_PATH
import sqlite3


class RealTimeChecksumApp(App):

    CSS = """
    Screen {
        background: #111318;
    }

    Header {
        background: #111318;
        color: #a0aabf;
        height: 1;
    }

    Footer {
        background: #16191f;
        color: #4a5568;
        height: 1;
    }

    #panel-status {
        height: 3;
        border: solid #2a2f3d;
        background: #16191f;
        padding: 0 2;
        margin: 1 1 0 1;
        color: #a0aabf;
    }

    #main-container {
        height: 1fr;
        margin: 0 1;
    }

    #panel-alertas {
        width: 45%;
        border: solid #2a2f3d;
        background: #16191f;
        margin-right: 1;
    }

    #panel-alertas-title {
        background: #1e2230;
        color: #7b8caa;
        padding: 0 1;
        height: 1;
    }

    #lista-alertas {
        background: #16191f;
        height: 1fr;
        border: none;
        padding: 0 1;
    }

    #lista-alertas > ListItem {
        background: #16191f;
        color: #c0392b;
        padding: 0 1;
    }

    #lista-alertas > ListItem.--highlight {
        background: #1f1a1a;
        color: #e74c3c;
    }

    #panel-derecho {
        width: 55%;
        height: 100%;
    }

    #panel-detalle-title {
        background: #1e2230;
        color: #7b8caa;
        padding: 0 1;
        height: 1;
    }

    #panel-detalle {
        height: 1fr;
        border: solid #2a2f3d;
        background: #16191f;
        padding: 1 2;
        color: #8899bb;
        margin-bottom: 1;
    }

    #panel-archivos {
        height: 35%;
        border: solid #2a2f3d;
        background: #16191f;
        margin: 1 1 1 1;
    }

    #panel-archivos-title {
        background: #1e2230;
        color: #7b8caa;
        padding: 0 1;
        height: 1;
    }

    #lista-archivos {
        background: #16191f;
        border: none;
        padding: 0 1;
        height: 1fr;
    }

    #lista-archivos > ListItem {
        background: #16191f;
        color: #4a5f7a;
        padding: 0 1;
    }

    #lista-archivos > ListItem.--highlight {
        background: #1a1f2e;
        color: #a0aabf;
    }

    .deleted {
        color: #c0392b;
        text-style: dim;
    }
    """

    BINDINGS = [
        ("q", "quit", "Salir"),
        ("r", "refresh", "Recargar"),
        ("u", "update", "Actualizar hash"),
        ("d", "detail", "Ver detalle"),
    ]

    def __init__(self, observer=None, monitoredPaths=None):
        super().__init__()
        self.observer = observer
        self.monitoredPaths = monitoredPaths or []
        self.alertCount = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Static(
            self._buildStatusText(),
            id="panel-status"
        )

        with Horizontal(id="main-container"):

            with Vertical(id="panel-alertas"):
                yield Static("  ALERTAS", id="panel-alertas-title")
                yield ListView(id="lista-alertas")

            with Vertical(id="panel-derecho"):
                yield Static("  DETALLE", id="panel-detalle-title")
                yield Static(
                    "\n  Selecciona un archivo para ver el detalle.\n\n"
                    "  Ruta:     —\n"
                    "  Hash BD:  —\n"
                    "  Mtime:    —\n"
                    "  Estado:   —\n",
                    id="panel-detalle"
                )

        with Vertical(id="panel-archivos"):
            yield Static("  ARCHIVOS MONITOREADOS", id="panel-archivos-title")
            yield ListView(id="lista-archivos")

        yield Footer()

    def on_mount(self) -> None:
        self._loadMonitoredFiles()
        self._loadAlertHistory()

    def _buildStatusText(self) -> str:
        totalFiles = self._countRegisteredFiles()
        return (
            f"  RealTimeChecksums  |  Estado: ACTIVO  |"
            f"  Directorios: {len(self.monitoredPaths)}  |"
            f"  Archivos: {totalFiles}  |"
            f"  Alertas: {self.alertCount}"
        )

    def _countRegisteredFiles(self) -> int:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hashes WHERE status = 'ok'")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def _loadMonitoredFiles(self) -> None:
        listView = self.query_one("#lista-archivos", ListView)
        listView.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT ab_path, status FROM hashes ORDER BY ab_path LIMIT 200")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                filePath, status = row
                label = f"[ELIMINADO] {filePath}" if status == "deleted" else filePath
                item = ListItem(Label(label))
                item.filePath = filePath
                if status == "deleted":
                    item.add_class("deleted")
                listView.append(item)
        except Exception:
            listView.append(ListItem(Label("Error al cargar archivos")))

    def _loadAlertHistory(self) -> None:
        # Carga las ultimas 100 alertas del log al iniciar, sin duplicar en refresh
        alertsLogPath = LOG_DIR_PATH + "alerts.log"
        listView = self.query_one("#lista-alertas", ListView)
        listView.clear()
        self.alertCount = 0
        try:
            import os
            if not os.path.exists(alertsLogPath):
                return
            with open(alertsLogPath, "r") as logFile:
                lines = logFile.readlines()
            recentLines = lines[-100:] if len(lines) > 100 else lines
            for line in recentLines:
                line = line.strip()
                if line:
                    listView.append(ListItem(Label(line)))
                    self.alertCount += 1
            self.query_one("#panel-status", Static).update(self._buildStatusText())
        except Exception:
            pass

    def addAlert(self, message: str) -> None:
        # Recibe alertas en tiempo real desde el hilo de watchdog
        self.alertCount += 1
        listView = self.query_one("#lista-alertas", ListView)
        listView.append(ListItem(Label(message)))
        self.query_one("#panel-status", Static).update(self._buildStatusText())

    def markFileAsDeleted(self, filePath: str) -> None:
        # Actualiza visualmente el archivo eliminado en la lista
        listView = self.query_one("#lista-archivos", ListView)
        for item in listView.query(ListItem):
            if getattr(item, "filePath", None) == filePath:
                item.query_one(Label).update(f"[ELIMINADO] {filePath}")
                item.add_class("deleted")
                break

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "lista-archivos":
            return
        filePath = getattr(event.item, "filePath", None)
        if not filePath:
            return
        record = getHashRecord(filePath)
        if record:
            from datetime import datetime
            mtime = datetime.fromtimestamp(record[2]).strftime("%Y-%m-%d %H:%M:%S")
            status = "Eliminado" if record[4] == "deleted" else "Registrado"
            detailText = (
                f"\n  Ruta:     {record[0]}\n"
                f"  Hash BD:  {record[1][:48]}...\n"
                f"  Mtime:    {mtime}\n"
                f"  Estado:   {status}\n"
            )
        else:
            detailText = "\n  Archivo no encontrado en la base de datos.\n"
        self.query_one("#panel-detalle", Static).update(detailText)

    def action_refresh(self) -> None:
        # Solo recarga archivos, las alertas se mantienen en tiempo real
        self._loadMonitoredFiles()
        self.query_one("#panel-status", Static).update(self._buildStatusText())
        self.notify("Lista actualizada", severity="information")

    def action_update(self) -> None:
        self.notify("Usa --update <ruta> desde la terminal", severity="warning")

    def action_detail(self) -> None:
        self.notify("Selecciona un archivo de la lista inferior", severity="information")

    def action_quit(self) -> None:
        if self.observer:
            self.observer.stop()
        self.exit()