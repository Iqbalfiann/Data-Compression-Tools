
import os
import time
import uuid
import logging

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory
)

from werkzeug.utils import secure_filename
from compression.pdf_compressor import compress_file


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


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

# Maksimal upload 4 MB untuk menghindari
# batas payload Vercel Serverless Function.
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


# ==========================================================
# STORAGE CONFIGURATION - VERCEL
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Gunakan /tmp karena direktori deployment Vercel
# bersifat read-only.

DATA_DIR = os.environ.get(
    "DATA_DIR",
    "/tmp/data_compression"
)

UPLOAD_FOLDER = os.path.join(
    DATA_DIR,
    "uploads"
)

OUTPUT_FOLDER = os.path.join(
    DATA_DIR,
    "output"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


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


def cleanup_file(file_path):

    if not file_path:
        return

    try:

        if os.path.isfile(file_path):
            os.remove(file_path)

    except OSError:

        logger.exception(
            "Gagal menghapus file: %s",
            file_path
        )


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def dashboard():

    return render_template(
        "index.html"
    )


# ==========================================================
# COMPRESS PAGE
# ==========================================================

@app.route("/compress")
def compress_page():

    return render_template(
        "compress.html"
    )


# ==========================================================
# PROCESS COMPRESS
# ==========================================================

@app.route(
    "/compress/process",
    methods=["POST"]
)
def compress_process():

    input_path = None
    output_path = None

    try:

        # --------------------------------------------------
        # 1. VALIDASI FILE
        # --------------------------------------------------

        if "file" not in request.files:

            flash(
                "File belum dipilih.",
                "error"
            )

            return redirect(
                url_for("compress_page")
            )

        file = request.files["file"]

        if not file or not file.filename:

            flash(
                "File belum dipilih.",
                "error"
            )

            return redirect(
                url_for("compress_page")
            )

        filename = secure_filename(
            file.filename
        )

        if not filename:

            flash(
                "Nama file tidak valid.",
                "error"
            )

            return redirect(
                url_for("compress_page")
            )

        # --------------------------------------------------
        # 2. VALIDASI FORMAT PDF
        # --------------------------------------------------

        if not filename.lower().endswith(".pdf"):

            flash(
                "File harus berformat PDF.",
                "error"
            )

            return redirect(
                url_for("compress_page")
            )

        # --------------------------------------------------
        # 3. BUAT NAMA FILE UNIK
        # --------------------------------------------------

        unique_id = uuid.uuid4().hex

        stored_name = (
            f"{unique_id}_{filename}"
        )

        output_name = (
            f"compressed_{unique_id}_{filename}"
        )

        input_path = os.path.join(
            UPLOAD_FOLDER,
            stored_name
        )

        output_path = os.path.join(
            OUTPUT_FOLDER,
            output_name
        )

        # --------------------------------------------------
        # 4. SIMPAN FILE UPLOAD
        # --------------------------------------------------

        file.save(
            input_path
        )

        if not os.path.isfile(input_path):

            raise RuntimeError(
                "File upload gagal disimpan."
            )

        original_file_size = os.path.getsize(
            input_path
        )

        if original_file_size == 0:

            raise ValueError(
                "File PDF kosong."
            )

        # --------------------------------------------------
        # 5. VALIDASI HEADER PDF
        # --------------------------------------------------

        with open(input_path, "rb") as pdf_file:

            header = pdf_file.read(1024)

        if b"%PDF-" not in header:

            raise ValueError(
                "File bukan PDF yang valid."
            )

        # --------------------------------------------------
        # 6. PROSES KOMPRESI
        # --------------------------------------------------

        logger.info(
            "Memulai kompresi PDF: %s",
            filename
        )

        start_time = time.perf_counter()

        result = compress_file(
            input_path,
            output_path
        )

        processing_time = (
            time.perf_counter() - start_time
        )

        # --------------------------------------------------
        # 7. VALIDASI HASIL KOMPRESI
        # --------------------------------------------------

        if not isinstance(result, dict):

            raise RuntimeError(
                "Hasil kompresi tidak valid."
            )

        original_size = result.get(
            "original_size"
        )

        compressed_size = result.get(
            "compressed_size"
        )

        if original_size is None or compressed_size is None:

            raise RuntimeError(
                "Informasi ukuran PDF tidak lengkap."
            )

        if not os.path.isfile(output_path):

            raise RuntimeError(
                "File hasil kompresi tidak ditemukan."
            )

        actual_compressed_size = os.path.getsize(
            output_path
        )

        if actual_compressed_size == 0:

            raise RuntimeError(
                "File hasil kompresi kosong."
            )

        if actual_compressed_size != compressed_size:

            raise RuntimeError(
                "Ukuran file hasil kompresi tidak sesuai."
            )

        # --------------------------------------------------
        # 8. HITUNG RASIO KOMPRESI
        # --------------------------------------------------

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

        logger.info(
            "Kompresi berhasil: %s | Original: %s | Compressed: %s",
            filename,
            original_size,
            compressed_size
        )

        # --------------------------------------------------
        # 9. TAMPILKAN HASIL
        # --------------------------------------------------

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

        logger.exception(
            "Terjadi kesalahan saat memproses PDF."
        )

        cleanup_file(output_path)

        flash(
            "Gagal memproses PDF. Silakan coba lagi.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    finally:

        # Hapus file upload setelah proses selesai.
        cleanup_file(input_path)


# ==========================================================
# DOWNLOAD PDF
# ==========================================================

@app.route(
    "/download/<path:filename>"
)
def download_file(filename):

    safe_filename = secure_filename(
        filename
    )

    if not safe_filename or safe_filename != filename:

        flash(
            "Nama file tidak valid.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    file_path = os.path.join(
        OUTPUT_FOLDER,
        safe_filename
    )

    if not os.path.isfile(file_path):

        flash(
            "File hasil kompresi tidak ditemukan atau sudah kedaluwarsa.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    return send_from_directory(

        OUTPUT_FOLDER,

        safe_filename,

        as_attachment=True,

        download_name=safe_filename

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
        "Ukuran file terlalu besar. Maksimal upload 4 MB.",
        "error"
    )

    return redirect(
        url_for("compress_page")
    )


@app.errorhandler(500)
def internal_server_error(error):

    logger.exception(
        "Internal Server Error."
    )

    return (
        "Terjadi kesalahan pada server.",
        500
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
