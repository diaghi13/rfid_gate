#!/usr/bin/env python3
"""
rfid_gate.utils.uid_normalize
---------------------------------

Helper per normalizzare UID RFID in rappresentazioni canoniche.

Funzione principale: uid_normalize(uid, force_bytes=None)

Accetta input comuni (int, bytes, bytearray, list/tuple di int, stringa esadecimale)
e restituisce un dict con:
  - uid_bytes: bytes (big-endian)
  - uid_hex: str (maiuscolo, senza 0x, padding per byte)
  - uid_int: Optional[int] (se la lunghezza <= 8 byte)
  - byte_len: int (numero di byte)

Questo file è solo aggiunto come utilità; non viene applicato automaticamente
nel codice del progetto.
"""
from typing import Any, Dict, Optional


def _bytes_from_int(n: int, length: Optional[int]) -> bytes:
    if n < 0:
        raise ValueError("UID int non può essere negativo")
    if length is not None:
        return n.to_bytes(length, 'big', signed=False)
    needed = max(1, (n.bit_length() + 7) // 8)
    return n.to_bytes(needed, 'big', signed=False)


def uid_normalize(uid: Any, force_bytes: Optional[int] = None) -> Dict[str, Any]:
    """
    Normalizza un UID in tre rappresentazioni affidabili.

    Args:
        uid: int | bytes | bytearray | list[int] | tuple[int] | str (hex o '0x...')
        force_bytes: se fornito, forza la lunghezza in byte (padding left con 0x00
                     o truncamento a destra per mantenere i byte più significativi)

    Returns:
        dict con 'uid_bytes', 'uid_hex', 'uid_int' (se len<=8), 'byte_len'

    Raises:
        TypeError: tipo uid non supportato
        ValueError: stringa esadecimale invalida o int negativo
    """

    uid_bytes: Optional[bytes] = None

    # bytes-like
    if isinstance(uid, (bytes, bytearray)):
        uid_bytes = bytes(uid)

    # list/tuple of ints
    elif isinstance(uid, (list, tuple)):
        try:
            uid_bytes = bytes(int(x) & 0xFF for x in uid)
        except Exception as e:
            raise ValueError(f"Lista UID non valida: {e}")

    # int
    elif isinstance(uid, int):
        uid_bytes = _bytes_from_int(uid, force_bytes)

    # string (esadecimale o con prefisso 0x)
    elif isinstance(uid, str):
        s = uid.strip()
        if s.startswith(('0x', '0X')):
            s = s[2:]
        s = ''.join(c for c in s if c.isalnum())
        if len(s) == 0:
            raise ValueError("Stringa UID vuota")
        if len(s) % 2 == 1:
            s = '0' + s
        try:
            uid_bytes = bytes.fromhex(s)
        except Exception:
            raise ValueError("Stringa UID non riconosciuta come esadecimale")

    else:
        raise TypeError("Tipo UID non supportato: %s" % type(uid))

    # applica force_bytes se richiesto
    if force_bytes is not None:
        if len(uid_bytes) < force_bytes:
            uid_bytes = b'\x00' * (force_bytes - len(uid_bytes)) + uid_bytes
        elif len(uid_bytes) > force_bytes:
            # tronca mantenendo i byte più significativi (right-truncate)
            uid_bytes = uid_bytes[-force_bytes:]

    byte_len = len(uid_bytes)
    uid_hex = ''.join(f"{b:02X}" for b in uid_bytes)
    uid_int = None
    if byte_len <= 8:
        uid_int = int.from_bytes(uid_bytes, 'big')

    return {
        'uid_bytes': uid_bytes,
        'uid_hex': uid_hex,
        'uid_int': uid_int,
        'byte_len': byte_len
    }


__all__ = ['uid_normalize']


if __name__ == '__main__':
    # Piccoli esempi per test manuale
    examples = [
        0x02D9BAEB,
        b"\x02\xD9\xBA\xEB",
        [2, 217, 186, 235],
        '2D9BAEB',
        '02D9BAEB',
    ]

    for ex in examples:
        try:
            norm = uid_normalize(ex, force_bytes=None)
            print(f"IN: {repr(ex)} -> bytes={list(norm['uid_bytes'])} hex={norm['uid_hex']} int={norm['uid_int']} len={norm['byte_len']}")
        except Exception as e:
            print(f"IN: {repr(ex)} -> ERROR: {e}")
