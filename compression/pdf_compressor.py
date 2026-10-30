
import os
import io
import shutil
import logging
import fitz

from PIL import Image


logger = logging.getLogger(__name__)


def compress_file(input_path, output_path):

    """
    PDF Compressor

    Optimasi:
    1. Kompresi gambar
    2. Resize gambar beresolusi tinggi
    3. Optimasi content stream
    4. Membersihkan object PDF
    5. Membersihkan metadata

    Output tetap dalam format PDF.
    """

    if not os.path.isfile(input_path):
        raise FileNotFoundError("File PDF tidak ditemukan.")

    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    original_size = os.path.getsize(input_path)

    if original_size == 0:
        raise ValueError("File PDF kosong.")

    temp_output = output_path + ".tmp"

    doc = None

    try:

        # ==================================================
        # 1. BUKA PDF
        # ==================================================

        doc = fitz.open(input_path)

        if not doc.is_pdf:
            raise ValueError("File bukan PDF yang valid.")

        if doc.is_encrypted:
            raise ValueError(
                "PDF terenkripsi atau membutuhkan password."
            )

        processed_images = set()

        # ==================================================
        # 2. KOMPRESI GAMBAR
        # ==================================================

        for page in doc:

            images = page.get_images(full=True)

            for image in images:

                xref = image[0]

                if xref in processed_images:
                    continue

                processed_images.add(xref)

                try:

                    image_info = doc.extract_image(xref)

                    if not image_info:
                        continue

                    image_bytes = image_info["image"]

                    pil_image = Image.open(
                        io.BytesIO(image_bytes)
                    )

                    pil_image.load()

                    width, height = pil_image.size

                    # Resize gambar jika terlalu besar
                    max_dimension = 1600

                    if max(width, height) > max_dimension:

                        scale = (
                            max_dimension /
                            max(width, height)
                        )

                        new_size = (
                            max(1, int(width * scale)),
                            max(1, int(height * scale))
                        )

                        resampling = getattr(
                            Image,
                            "Resampling",
                            Image
                        )

                        pil_image = pil_image.resize(
                            new_size,
                            resampling.LANCZOS
                        )

                    # Konversi ke RGB
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

                    # Kompresi JPEG
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

                    # Ganti hanya jika lebih kecil
                    if len(compressed_bytes) < len(image_bytes):

                        page.replace_image(
                            xref,
                            stream=compressed_bytes
                        )

                except Exception:

                    logger.warning(
                        "Gambar dengan xref %s gagal dikompresi.",
                        xref,
                        exc_info=True
                    )

                    continue

        # ==================================================
        # 3. BERSIHKAN METADATA
        # ==================================================

        try:

            doc.set_metadata({
                "title": "",
                "author": "",
                "subject": "",
                "keywords": "",
                "creator": "",
                "producer": ""
            })

        except Exception:

            logger.warning(
                "Gagal membersihkan metadata PDF.",
                exc_info=True
            )

        # ==================================================
        # 4. SIMPAN PDF
        # ==================================================

        # Pastikan tidak ada file sementara sebelumnya
        if os.path.exists(temp_output):
            os.remove(temp_output)

        doc.save(
            temp_output,
            garbage=4,
            deflate=True,
            clean=True
        )

        doc.close()
        doc = None

        # ==================================================
        # 5. PERIKSA HASIL
        # ==================================================

        if not os.path.isfile(temp_output):

            raise RuntimeError(
                "File hasil kompresi tidak berhasil dibuat."
            )

        compressed_size = os.path.getsize(temp_output)

        if compressed_size == 0:

            raise RuntimeError(
                "Hasil kompresi PDF kosong."
            )

        # ==================================================
        # 6. PILIH HASIL TERKECIL
        # ==================================================

        if compressed_size >= original_size:

            os.remove(temp_output)

            shutil.copyfile(
                input_path,
                output_path
            )

            compressed_size = original_size

        else:

            os.replace(
                temp_output,
                output_path
            )

        # ==================================================
        # 7. RETURN RESULT
        # ==================================================

        return {
            "original_size": original_size,
            "compressed_size": compressed_size
        }

    except Exception:

        logger.exception(
            "PDF compression failed: %s",
            input_path
        )

        raise

    finally:

        # Pastikan dokumen selalu ditutup
        if doc is not None:

            try:
                doc.close()
            except Exception:
                pass

        # Bersihkan file sementara
        if os.path.exists(temp_output):

            try:
                os.remove(temp_output)
            except OSError:
                logger.warning(
                    "Gagal menghapus temporary file."
                )
