import base64
import os
import uuid
from typing import Optional

def save_base64_image(data_uri: str, upload_dir: str = "app/static/uploads") -> Optional[str]:
    """
    Decodes a base64 image string and saves it to the specified directory.
    Returns the relative URL path to the saved image.
    """
    if not data_uri:
        return None

    try:
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

        # Check for data URI prefix
        if "base64," in data_uri:
            header, encoded = data_uri.split("base64,", 1)
            # Extrapolate extension from header if possible, default to jpg
            # header example: data:image/png;
            ext = "jpg"
            if "image/png" in header:
                ext = "png"
            elif "image/jpeg" in header:
                ext = "jpg"
            elif "image/webp" in header:
                ext = "webp"
        else:
            encoded = data_uri
            ext = "jpg"

        # Generate unique filename
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(upload_dir, filename)

        # Decode and save
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(encoded))

        # Return relative URL (assuming static mount at /static)
        # We return the path relative to the mounting point
        return f"/static/uploads/{filename}"
    except Exception as e:
        print(f"Error saving image: {e}")
        return None
