import base64
import os
import uuid

from supabase import create_client, Client

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)


def subir_imagen_base64(base64_str: str, nombre_archivo: str) -> str | None:
    try:
        file_bytes = base64.b64decode(base64_str)
        supabase.storage.from_("imagenes_donaciones").upload(
            path=nombre_archivo,
            file=file_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        return supabase.storage.from_("imagenes_donaciones").get_public_url(nombre_archivo)
    except Exception:
        return None
