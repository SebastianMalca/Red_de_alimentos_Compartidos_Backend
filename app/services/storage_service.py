import os
import uuid
from fastapi import UploadFile
from supabase import create_client, Client

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

async def subir_imagen(file: UploadFile) -> str:
    extension = file.filename.split(".")[-1]
    nombre_archivo = f"{uuid.uuid4()}.{extension}"
    
    file_bytes = await file.read()
    
    # Subir a Supabase Storage
    supabase.storage.from_("imagenes_donaciones").upload(
        path=nombre_archivo,
        file=file_bytes,
        file_options={"content-type": file.content_type}
    )
    
    url_publica = supabase.storage.from_("imagenes_donaciones").get_public_url(nombre_archivo)
    return url_publica
