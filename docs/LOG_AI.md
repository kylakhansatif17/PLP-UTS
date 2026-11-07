# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

Penulis log ini: Kyla. Urutan isi tiap nomor: Siapa, Tugas, Hasil, Alasan, Cara verifikasi.

1. Siapa: Kyla
   Tugas: Minta arahan membuat test untuk empat bug yang saya kerjakan (Bug 3, 5, 7, 9). Perbedaannya:
   - Bug 3 (escape `''`): satu test regresi dan tiga test kasus tepi.
   - Bug 5 (error recovery): satu test regresi dan dua test kasus tepi.
   - Bug 7 (pencarian alias): satu test regresi dan satu test fallback ke scope induk.
   - Bug 9 (subquery di `UPDATE`): satu test regresi.
   Hasil: Diterima.
   Alasan: Penyebab masalah dan solusi kode di keempat bug saya tentukan sendiri. AI hanya menyarankan jenis test yang dibuat, yaitu satu test regresi (gagal di kode lama, lulus di kode baru) dan beberapa test kasus tepi (input yang berisiko menimbulkan kesalahan), beserta contoh kasus yang perlu diuji. Saya yang menulis dan menjalankan test-nya.
   Cara verifikasi: Setiap test dijalankan di kode lama dan kode baru dengan `python -m pytest -q`. Test regresi gagal di kode lama dan lulus di kode baru. Test fallback pada Bug 7 (nama alias hanya ada di scope luar) lulus di keduanya, karena tujuannya memastikan perbaikan saya tidak merusak kasus yang sebelumnya sudah benar.

2. Siapa: Kyla
   Tugas: Minta AI memeriksa laporan bug terhadap kode dan `SPESIFIKASI.md`.
   Hasil: Diterima. AI menemukan dua hal. Pertama, `_synchronize` versi awal saya menghasilkan dua error pada `SELECT * FROM WHERE id IN (SELECT id FROM u);`, padahal spesifikasi 6.2 meminta satu error. Kedua, perubahan saya pada `column_usage` membuat kolom di `WHERE` pada `UPDATE` menjadi `U`, padahal di kode awal `R`.
   Alasan: Kedua temuan terbukti dengan menjalankan contoh SQL dan membandingkannya dengan spesifikasi bagian 5 dan 6.2.
   Cara verifikasi: Saya menjalankan contoh SQL dari AI dan hasilnya sekarang satu error, dengan statement sesudahnya tetap terproses. Test untuk kolom `WHERE` lulus, dan test baru untuk `_synchronize` gagal bila cabang keyword dipasang kembali sementara. Terakhir, `python -m pytest -q` lulus semua.

   **Refleksi (3-5 kalimat).** AI paling membantu saat memeriksa laporan saya terhadap kode dan spesifikasi. Dari situ muncul dua temuan yang tidak tertangkap test saya: rancangan error recovery menghasilkan dua error padahal spesifikasi meminta satu, dan perubahan saya membuat kolom di `WHERE` pada `UPDATE` bernilai `U` padahal seharusnya `R`. AI juga pernah keliru: ia salah menjelaskan isi file Kartu Desain yang ia kirim, dan salah satu kalimatnya ("error kedua yang tidak benar") terlalu kabur. Saya mengetahuinya dengan membandingkan penjelasan AI dengan file yang saya kirim dan membaca ulang tiap kalimat, lalu AI meralat dan memperjelasnya.