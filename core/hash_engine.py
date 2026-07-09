# Hash generator engine

import hashlib
from config import CHUNK_SIZE, HASH_ALGORITHM

def calculateFileHash(filePath: str) -> str | None: # Si encuentra el filePath devolvera un string, en su defecto, un None
    try:
        with open(filePath, 'rb') as file:
            hashDeploy = hashlib.new(HASH_ALGORITHM) # Inicializamos el objeto hash
            readChunk = file.read(CHUNK_SIZE) # Leemos el bloque en el tamaño seleccionado en el archivo de configuracion, que son 8KB
            while readChunk: # Bucle que actualiza el objeto hash y avtualiza el contenido de readChunk
                hashDeploy.update(readChunk)
                readChunk = file.read(CHUNK_SIZE)
            return hashDeploy.hexdigest() # Devuelve el objeto hash transformado en un string hexadecimal
    except (FileNotFoundError, PermissionError):
        return None
