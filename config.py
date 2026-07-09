#
# Archivo de configuracion por predeterminado
# Contiene:
#   - Constantes GLOBALES
#   - Configuración de la herramienta
#
# Modificar este archivo, implica la posibilidad de romper la herramineta
# como la responsabilidad de configurarlo de manera correcta, para evitar
# vulnerabilidades
#

DB_PATH = "./data/checksums.db" # Directorio donde se almacenara la base de datos
BL_FILE_PATH = "./data/blacklist.json" # Blacklist
LOG_DIR_PATH = "./data/logs/" # Directorio donde se almacenara los logs
DEFAULT_MONITOR_PATH = ["/var/www/"] # Directorio que se monitorea por defecto (Modificar)
SCAN_COOLDOWN = 300 # Retraso por escaneo
HASH_ALGORITHM = "sha256" # Algoritmo de hasheo
BL_FILES = ["/etc/mtab", "/etc/resolv.conf", "/etc/adjtime", "/etc/ld.so.cache"] # Blacklist
CHUNK_SIZE = 8192 # Tamaño del bloque en que se leera el archivo, esta establecido en 8KBs


