
# Data Compression Tools

Aplikasi web sederhana untuk melakukan kompresi dan optimasi file PDF.

## Deskripsi

Data Compression Tools merupakan aplikasi berbasis web yang digunakan untuk mengurangi ukuran file PDF agar lebih mudah disimpan, dikirim, dan dibagikan.

Aplikasi menggunakan Python sebagai bahasa pemrograman utama dan Flask sebagai web framework. Proses optimasi PDF menggunakan PyMuPDF dan Pillow.

## Tujuan

Project ini dibuat untuk menyediakan alat sederhana yang dapat membantu pengguna mengurangi ukuran file PDF melalui browser.

## Fitur

- Upload file PDF
- Drag & Drop file PDF
- Kompresi dan optimasi PDF
- Optimasi gambar dalam PDF
- Optimasi struktur PDF
- Progress animation saat proses kompresi
- Informasi ukuran file sebelum dan sesudah kompresi
- Informasi compression ratio
- Informasi persentase ruang yang dihemat
- Informasi waktu proses
- Download hasil kompresi dalam format PDF

## Teknologi yang Digunakan

- Python
- Flask
- PyMuPDF
- Pillow
- HTML
- CSS
- JavaScript

## Struktur Project

Data Compression Tools/
│
├── compression/
│   └── pdf_compressor.py
│
├── output/
│
├── uploads/
│
├── static/
│   └── css/
│       └── style.css
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── compress.html
│
├── app.py
└── requirements.txt

## Cara Kerja Sistem

Pengguna membuka website
        ↓
Memilih atau Drag & Drop file PDF
        ↓
Flask menerima file
        ↓
PDF diproses oleh pdf_compressor.py
        ↓
PyMuPDF dan Pillow melakukan optimasi
        ↓
Sistem menghasilkan PDF hasil kompresi
        ↓
Ukuran file dibandingkan
        ↓
Hasil kompresi ditampilkan
        ↓
Pengguna mengunduh PDF

## Proses Kompresi

Sistem melakukan beberapa proses optimasi pada file PDF:

1. Membaca file PDF.
2. Mengidentifikasi gambar yang terdapat di dalam PDF.
3. Mengurangi resolusi gambar yang terlalu besar.
4. Mengoptimasi gambar menggunakan Pillow.
5. Membersihkan metadata PDF.
6. Membersihkan objek PDF yang tidak digunakan.
7. Mengompres content stream.
8. Mengoptimasi struktur PDF.
9. Membandingkan ukuran file sebelum dan sesudah kompresi.
10. Menggunakan file asli apabila hasil optimasi justru lebih besar.

Hasil akhir tetap menggunakan format `.pdf`.

## Instalasi

Pastikan Python sudah terinstall pada komputer.

Install dependency dengan perintah:

pip install -r requirements.txt

## Menjalankan Aplikasi

Jalankan aplikasi menggunakan:

python app.py

Kemudian buka browser dan akses:

http://127.0.0.1:5000

## Cara Menggunakan

1. Buka halaman utama Data Compression Tools.
2. Pilih menu Compress PDF.
3. Pilih file PDF atau lakukan Drag & Drop.
4. Klik tombol Compress PDF.
5. Tunggu proses kompresi selesai.
6. Lihat informasi hasil kompresi.
7. Klik Download PDF untuk mengunduh file hasil.

## Hasil

Aplikasi menghasilkan file PDF baru dengan ukuran yang diusahakan lebih kecil dari file asli.

Informasi yang ditampilkan setelah proses meliputi:

* Nama file
* Ukuran awal
* Ukuran setelah kompresi
* Compression Ratio
* Space Saved
* Waktu proses

## Catatan

Hasil kompresi dapat berbeda tergantung isi file PDF. PDF yang sudah teroptimasi atau memiliki sedikit gambar mungkin hanya mengalami pengurangan ukuran yang kecil.

Aplikasi tidak memaksakan kompresi apabila hasil akhirnya lebih besar daripada file asli.

## Pengembangan

Project ini dapat dikembangkan lebih lanjut dengan menambahkan fitur seperti:

* Pilihan tingkat kompresi
* Preview PDF
* Batch compression
* Penghapusan file sementara secara otomatis
* Deployment ke server agar dapat diakses melalui internet

## Author

Iqbal Alfiansyah

Universitas Pamulang
Fakultas Ilmu Komputer
Program Studi Teknik Informatika
