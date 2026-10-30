
import os
import uuid
import logging
import tempfile

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    abort,
    url_for
)
from werkzeug.utils import secure_filename

from compression.pdf_compressor import compress_file


# =========================
# KONFIGURASI APLIKASI
# =========================

app = Flask(__name__, template_folder="html")

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "data-compression-secret-key"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Batas upload 4 MB untuk menyesuaikan batas request Vercel
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

# Gunakan folder sementara yang bisa ditulis oleh Vercel
DATA_DIR = os.path.join(
    tempfile.gettempdir(),
    "data_compression"
)

UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(DATA_DIR, "output")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================
# VALIDASI FILE
# =========================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() == "pdf"
    )


# =========================
# HALAMAN UTAMA
# =========================

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# HALAMAN KOMPRESI
# =========================

@app.route("/compress")
def compress():
    return render_template("compress.html")


# =========================
# PROSES UPLOAD DAN KOMPRESI
# =========================

@app.route("/compress/process", methods=["POST"])
def compress_process():

    try:
        # Ambil file dari form upload
        if "file" not in request.files:
            return render_template(
                "compress.html",
                error="Silakan pilih file PDF terlebih dahulu."
            )

        file = request.files["file"]

        if file.filename == "":
            return render_template(
                "compress.html",
                error="Belum ada file yang dipilih."
            )

        # Validasi ekstensi
        if not allowed_file(file.filename):
            return render_template(
                "compress.html",
                error="Format file harus PDF."
            )

        # Nama file aman dan unik
        original_filename = secure_filename(file.filename)

        unique_id = uuid.uuid4().hex

        input_filename = f"{unique_id}_{original_filename}"
        output_filename = f"compressed_{unique_id}.pdf"

        # Simpan file sementara di /tmp
        input_path = os.path.join(
            UPLOAD_FOLDER,
            input_filename
        )

        output_path = os.path.join(
            OUTPUT_FOLDER,
            output_filename
        )

        file.save(input_path)

        # Pastikan file benar-benar PDF
        with open(input_path, "rb") as pdf_file:
            header = pdf_file.read(5)

        if header != b"%PDF-":
            os.remove(input_path)

            return render_template(
                "compress.html",
                error="File yang diunggah bukan PDF yang valid."
            )

        # Jalankan kompresi PDF
        result = compress_file(
            input_path,
            output_path
        )

        original_size = result["original_size"]
        compressed_size = result["compressed_size"]

        # Hitung persentase penghematan
        if original_size > 0:
            reduction = (
                (original_size - compressed_size)
                / original_size
            ) * 100
        else:
            reduction = 0

        logger.info(
            "PDF berhasil dikompres: %s",
            original_filename
        )

        return render_template(
            "compress.html",
            success=True,
            original_filename=original_filename,
            original_size=original_size,
            compressed_size=compressed_size,
            reduction=round(reduction, 2),
            download_url=url_for(
                "download_file",
                filename=output_filename
            )
        )

    except Exception:
        logger.exception("Terjadi kesalahan saat kompresi PDF")

        return render_template(
            "compress.html",
            error="Terjadi kesalahan saat memproses PDF. Silakan coba lagi."
        )


# =========================
# DOWNLOAD HASIL KOMPRESI
# =========================

@app.route("/download/<path:filename>")
def download_file(filename):

    # Cegah akses ke file di luar folder output
    safe_filename = os.path.basename(filename)

    file_path = os.path.join(
        OUTPUT_FOLDER,
        safe_filename
    )

    if not os.path.isfile(file_path):
        abort(404, description="File hasil kompresi tidak ditemukan.")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_filename,
        mimetype="application/pdf"
    )


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():

    return {
        "status": "online",
        "upload_folder": UPLOAD_FOLDER,
        "output_folder": OUTPUT_FOLDER,
        "writable": os.access(UPLOAD_FOLDER, os.W_OK)
    }


# =========================
# ERROR UPLOAD TERLALU BESAR
# =========================

@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "compress.html",
        error="Ukuran PDF terlalu besar. Maksimal upload saat ini 4 MB."
    ), 413


# =========================
# MENJALANKAN APLIKASI
# =========================

if __name__ == "__main__":
    app.run(debug=True)
