"""Bloqueo no destructivo para evitar dos sincronizaciones en paralelo."""
from contextlib import contextmanager
from pathlib import Path
import os


@contextmanager
def sync_lock(root):
    path = Path(root) / 'sync.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.lockf(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except (OSError, IOError):
            pass
        try:
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.lockf(handle.fileno(), fcntl.LOCK_UN)
