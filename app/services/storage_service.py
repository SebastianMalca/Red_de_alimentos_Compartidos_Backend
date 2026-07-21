import base64
import os
import uuid

from supabase import create_client, Client

_supabase: Client | None = None


def _get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        _supabase = create_client(url, key)
    return _supabase


def subir_imagen_base64(base64_str: str, nombre_archivo: str) -> str | None:
    try:
        client = _get_supabase()
        file_bytes = base64.b64decode(base64_str)
        client.storage.from_("imagenes_donaciones").upload(
            path=nombre_archivo,
            file=file_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        return client.storage.from_("imagenes_donaciones").get_public_url(nombre_archivo)
    except Exception:
        return None
