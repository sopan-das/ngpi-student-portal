import os
import secrets
from PIL import Image
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

def save_picture(form_picture, folder, output_size=None):
    """Save uploaded picture and return filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/uploads', folder, picture_fn)

    # Ensure directory exists
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    # Resize if needed
    if output_size:
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
    else:
        form_picture.save(picture_path)

    return picture_fn

def save_file(form_file, folder):
    """Save uploaded file (PDF/Image) and return filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_file.filename)
    file_fn = random_hex + f_ext
    file_path = os.path.join(current_app.root_path, 'static/uploads', folder, file_fn)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    form_file.save(file_path)
    return file_fn

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']