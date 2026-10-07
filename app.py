from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import time
from compression.pdf_compressor import compress_file


app = Flask(
    __name__,
    template_folder="html"
)

app.config["SECRET_KEY"] = "data-compression-secret-key"


# ==========================================================
# FOLDER
# ==========================================================

BASE_DIR = app.root_path

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
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
# HUMAN SIZE
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

    if "file" not in request.files:

        flash(
            "File belum dipilih.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    file = request.files["file"]

    if file.filename == "":

        flash(
            "File belum dipilih.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    filename = file.filename

    if not filename.lower().endswith(".pdf"):

        flash(
            "File harus berformat PDF.",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )

    timestamp = str(
        int(time.time())
    )

    stored_name = (
        timestamp
        + "_"
        + filename
    )

    input_path = os.path.join(
        UPLOAD_FOLDER,
        stored_name
    )

    output_name = (
        "compressed_"
        + filename
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        output_name
    )

    file.save(
        input_path
    )

    try:

        start = time.perf_counter()

        result = compress_file(
            input_path,
            output_path
        )

        processing_time = (
            time.perf_counter()
            - start
        )

        original_size = (
            result["original_size"]
        )

        compressed_size = (
            result["compressed_size"]
        )

        if original_size > 0:

            compression_ratio = (
                compressed_size
                / original_size
            )

            space_saved = (
                (
                    original_size
                    - compressed_size
                )
                / original_size
            ) * 100

        else:

            compression_ratio = 0

            space_saved = 0

        return render_template(

            "compress.html",

            result={

                "file_name":
                    filename,

                "original_size":
                    human_size(
                        original_size
                    ),

                "compressed_size":
                    human_size(
                        compressed_size
                    ),

                "compression_ratio":
                    f"{compression_ratio:.4f}",

                "space_saved":
                    f"{space_saved:.2f}",

                "processing_time":
                    f"{processing_time:.4f} detik",

                "output":
                    output_name
            }

        )

    except Exception as error:

        flash(
            f"Terjadi error: {error}",
            "error"
        )

        return redirect(
            url_for("compress_page")
        )


# ==========================================================
# DOWNLOAD PDF
# ==========================================================

@app.route(
    "/download/<path:filename>"
)
def download_file(filename):

    return send_from_directory(

        OUTPUT_FOLDER,

        filename,

        as_attachment=True
    )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )