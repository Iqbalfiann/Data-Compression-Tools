import os
import io
import fitz
from PIL import Image


def compress_file(input_path, output_path):
    """
    PDF Compressor

    Optimasi:
    1. Gambar
    2. Content stream
    3. Object PDF yang tidak terpakai
    4. Metadata
    5. Struktur PDF

    Hasil tetap berupa file PDF.
    """

    original_size = os.path.getsize(input_path)

    # ==========================================================
    # BUKA PDF
    # ==========================================================

    doc = fitz.open(input_path)

    processed_images = set()


    # ==========================================================
    # 1. KOMPRESI GAMBAR
    # ==========================================================

    for page in doc:

        images = page.get_images(full=True)

        for image in images:

            xref = image[0]

            # Jangan memproses gambar yang sama berkali-kali
            if xref in processed_images:
                continue

            processed_images.add(xref)

            try:

                image_info = doc.extract_image(xref)

                if not image_info:
                    continue

                image_bytes = image_info["image"]

                # Buka gambar
                pil_image = Image.open(
                    io.BytesIO(image_bytes)
                )

                pil_image.load()

                width, height = pil_image.size


                # --------------------------------------------------
                # Batasi resolusi gambar
                # --------------------------------------------------

                max_dimension = 1600

                if max(width, height) > max_dimension:

                    scale = (
                        max_dimension /
                        max(width, height)
                    )

                    new_width = int(width * scale)
                    new_height = int(height * scale)

                    pil_image = pil_image.resize(
                        (new_width, new_height),
                        Image.Resampling.LANCZOS
                    )


                # --------------------------------------------------
                # Konversi gambar ke RGB
                # --------------------------------------------------

                if pil_image.mode != "RGB":

                    if "A" in pil_image.getbands():

                        background = Image.new(
                            "RGB",
                            pil_image.size,
                            "white"
                        )

                        background.paste(
                            pil_image,
                            mask=pil_image.getchannel("A")
                        )

                        pil_image = background

                    else:

                        pil_image = pil_image.convert("RGB")


                # --------------------------------------------------
                # Kompresi JPEG
                # --------------------------------------------------

                compressed_image = io.BytesIO()

                pil_image.save(
                    compressed_image,
                    format="JPEG",
                    quality=60,
                    optimize=True
                )

                compressed_bytes = (
                    compressed_image.getvalue()
                )


                # --------------------------------------------------
                # Hanya ganti jika hasil lebih kecil
                # --------------------------------------------------

                if len(compressed_bytes) < len(image_bytes):

                    page.replace_image(
                        xref,
                        stream=compressed_bytes
                    )


            except Exception:
                # Jika gambar gagal diproses,
                # lanjutkan ke gambar berikutnya
                continue


    # ==========================================================
    # 2. BERSIHKAN METADATA
    # ==========================================================

    try:

        doc.set_metadata({
            "format": "PDF",
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "",
            "producer": ""
        })

    except Exception:
        pass


    # ==========================================================
    # 3. SIMPAN HASIL SEMENTARA
    # ==========================================================

    temp_output = output_path + ".tmp"

    try:

        doc.save(
            temp_output,

            # Membersihkan object yang tidak terpakai
            garbage=4,

            # Compress / deflate content stream
            deflate=True,

            # Bersihkan struktur PDF
            clean=True,

            # Gunakan object stream
            use_objstms=True
        )

    except Exception:

        # Fallback untuk versi PyMuPDF tertentu
        doc.save(
            temp_output,
            garbage=4,
            deflate=True,
            clean=True
        )


    doc.close()


    # ==========================================================
    # 4. CEK UKURAN HASIL
    # ==========================================================

    if not os.path.exists(temp_output):

        # Kalau gagal membuat hasil,
        # gunakan file asli
        with open(input_path, "rb") as source:
            data = source.read()

        with open(output_path, "wb") as target:
            target.write(data)

        return {
            "original_size": original_size,
            "compressed_size": original_size
        }


    compressed_size = os.path.getsize(
        temp_output
    )


    # ==========================================================
    # 5. JIKA HASIL LEBIH BESAR
    # ==========================================================

    if compressed_size >= original_size:

        os.remove(temp_output)

        with open(input_path, "rb") as source:
            data = source.read()

        with open(output_path, "wb") as target:
            target.write(data)

        compressed_size = original_size


    # ==========================================================
    # 6. JIKA HASIL LEBIH KECIL
    # ==========================================================

    else:

        if os.path.exists(output_path):
            os.remove(output_path)

        os.rename(
            temp_output,
            output_path
        )


    # ==========================================================
    # HASIL
    # ==========================================================

    return {
        "original_size": original_size,
        "compressed_size": compressed_size
    }