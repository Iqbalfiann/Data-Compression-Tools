
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory
)

import os
import time
import uuid
import logging

from werkzeug.utils import secure_filename
from compression.pdf_compressor import compress_file


# ==========================================================
# FLASK CONFIGURATION
# ==========================================================

app = Flask(
    __name__,
    template_folder="html"
)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "data-compression-development-key"
)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# Logging untuk membantu mendeteksi error deployment
logging.basicConfig(level=logging.INFO)


# ==========================================================
# FOLDER CONFIGURATION
# ==========================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "output"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ==========================================================
# HELPER FUNCTION
# ==========================================================

def human_size(size):

    size = float(size)

    for unit in ["Bytes", "KB", "MB", "GB"]:

        if size < 1024:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} TB"


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def dashboard():

    return render_template("index.html")


# ==========================================================
# COMPRESS PAGE
# ==========================================================

@app.route("/compress")
def compress_page():

    return render_template("compress.html")


# ==========================================================
# PROCESS COMPRESS
# ==========================================================

@app.route("/compress/process", methods=["POST"])
def compress_process():

    # Memastikan file tersedia
    if "file" not in request.files:

        flash("File belum dipilih.", "error")

        return redirect(url_for("compress_page"))

    file = request.files["file"]

    if not file or file.filename == "":

        flash("File belum dipilih.", "error")

        return redirect(url_for("compress_page"))

    # Mengamankan nama file
    filename = secure_filename(file.filename)

    if not filename:

        flash("Nama file tidak valid.", "error")

        return redirect(url_for("compress_page"))

    # Memastikan format PDF
    if not filename.lower().endswith(".pdf"):

        flash("File harus berformat PDF.", "error")

        return redirect(url_for("compress_page"))

    # Membuat nama file unik agar tidak bentrok
    unique_id = uuid.uuid4().hex[:12]

    stored_name = f"{unique_id}_{filename}"

    output_name = f"compressed_{unique_id}_{filename}"

    input_path = os.path.join(
        UPLOAD_FOLDER,
        stored_name
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        output_name
    )

    try:

        # Menyimpan file upload
        file.save(input_path)

        # Memulai proses kompresi
        start_time = time.perf_counter()

        result = compress_file(
            input_path,
            output_path
        )

        processing_time = (
            time.perf_counter() - start_time
        )

        # Memastikan hasil kompresi tersedia
        if not os.path.isfile(output_path):

            raise RuntimeError(
                "File hasil kompresi tidak ditemukan."
            )

        # Mengambil ukuran file
        original_size = result["original_size"]

        compressed_size = result["compressed_size"]

        # Menghitung rasio kompresi
        if original_size > 0:

            compression_ratio = (
                compressed_size / original_size
            )

            space_saved = (
                (original_size - compressed_size)
                / original_size
            ) * 100

        else:

            compression_ratio = 0
            space_saved = 0

        # Menampilkan hasil
        return render_template(

            "compress.html",

            result={

                "file_name": filename,

                "original_size": human_size(
                    original_size
                ),

                "compressed_size": human_size(
                    compressed_size
                ),

                "compression_ratio": (
                    f"{compression_ratio:.4f}"
                ),

                "space_saved": (
                    f"{space_saved:.2f}"
                ),

                "processing_time": (
                    f"{processing_time:.4f} detik"
                ),

                "output": output_name

            }

        )

    except Exception:

        # Mencatat error lengkap di deployment logs
        app.logger.exception(
            "Terjadi kesalahan saat memproses PDF."
        )

        # Menghapus file output jika proses gagal
        if os.path.exists(output_path):

            try:
                os.remove(output_path)
            except OSError:
                app.logger.warning(
                    "Gagal menghapus file output sementara."
                )

        flash(
            "Gagal memproses PDF. Silakan coba file lain.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    finally:

        # Menghapus file upload sementara
        if os.path.exists(input_path):

            try:
                os.remove(input_path)
            except OSError:
                app.logger.warning(
                    "Gagal menghapus file upload sementara."
                )


# ==========================================================
# DOWNLOAD PDF
# ==========================================================

@app.route("/download/<path:filename>")
def download_file(filename):

    return send_from_directory(

        OUTPUT_FOLDER,

        filename,

        as_attachment=True

    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/health")
def health_check():

    return {
        "status": "ok",
        "message": "Data Compression Tools is running."
    }, 200


# ==========================================================
# ERROR HANDLER
# ==========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "Ukuran file terlalu besar. Maksimal 50 MB.",
        "error"
    )

    return redirect(
        url_for("compress_page")
    )


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
