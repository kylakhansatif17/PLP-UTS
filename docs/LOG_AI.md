# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Aulia | AI membantu memvalidasi draf laporan bug yang telah disusun secara mandiri oleh Aulia dan Kyla, memastikan apabila terdapat kesalahan dalam analisis kami berdua. | Diterima | AI memisahkan klaim yang sudah terbukti dari yang hanya baru dugaan saja, dan hasil pengecekan manual dengan AI sama, yaitu benar terdapat 9 bug dan 3 fitur yang harus kami selesaikan| Membandingkan dengan output pytest dan CLI milik sendiri |
| 2 | Aulia | Bug 1: AI memastikan keyword huruf kecil memang bug dan memvalidasi solusi yang saya susun benar atau salah | Diterima | Solusi saya adalah mengubah kata ke huruf besar sebelum dicek ke KEYWORDS yang sesuai dengan spesifikasi 2.2. Saya juga memiliki alternatif lain dengan mengubah isi KEYWORDS ke huruf kecil, tetapi hal ini tidak dipilih karena melanggar spesifikasi | Menyusun solusi yang telah dibuat menjadi perbaikan pada program, lalu membuat test regresi test_keyword_huruf_campuran_dikenali yang gagal sebelum dilakukan perbaikan dan lulus sesudah perbaikan, lalu melakukan python -m pytest.|
| 3 | Aulia | Bug 2: bingung bagian mana yang harus diubah agar <> menjadi satu token dan memvalidasi apakah akar masalahnya dibagian tersebut | Diterima | AI membantu memvalidasi dengan menunjukkan akar masalah di cabang "<" lexer yang hanya mengecek "=". Untuk kode perbaikannya sama seperti di bug 1, saya tetap tulis sendiri. Ada juga alternatif saran untuk memperbaiki di parser, tetapi tidak saya pilih karena salah tahap | Menyusun kode perbaikan, lalu membuat test_operator_tidak_sama_diamond_satu_token yang gagal sebelum dilakukan perbaikan lalu lulus, error ">" di laporan_penjualan.sql baris 6 hilang, python -m pytest tidak menunjukkan bug baru |
| 4 | Aulia | Bug 4: akar masalah di _logical sudah saya temukan, tetapi masih bingung cara memperbaikinya | Diterima | AI mengarahkan saya memisahkan OR dan AND menjadi dua fungsi (_logical dan _and) sesuai grammar bagian 3. Ada juga solusi menukar urutan cek di satu loop tetapi tidak saya pilih karena tidak bisa menyatakan dua tingkat presedensi | Menyusun kode perbaikan secara mandiri, lalu membuat test_and_lebih_kuat_dari_or yang ketika di test sebelum perbaikan gagal dan lulus sesudahnya |
| 5 | Aulia | Bug 6: menelusuri pesan error "diharapkan JOIN, ditemukan OUTER" sampai ke _join | Diterima | AI membantu mencocokkan kode dengan grammar dan menjelaskan bagian opsional [OUTER] diterapkan dengan satu _match_kw("OUTER"). Menerima OUTER di mana saja tidak dipilih karena melanggar grammar | test_left_outer_join_diterima dan test_tepi_outer_tanpa_left_tetap_ditolak lulus, python -m pytest tidak menunjukkan bug baru |
| 6 | Aulia | Bug 8: mencari kenapa alias DELETE masih terbaca oleh SELECT berikutnya | Diterima | Dari pembacaan bersama _select, _update, dan _delete terlihat hanya _delete yang tidak memanggil _pop. Mereset scope di tiap statement tidak dipilih karena hanya menutupi masalah | test_regresi_delete_scope_pop_setelah_statement gagal sebelum perbaikan dan lulus sesudahnya |
| 7 | Aulia | Menanyakan bagaimana fitur INSERT ... SELECT (parser) dan kolom tanpa qualifier (resolver) ini berjalan | Diterima | AI membantu saya untuk menyusun rancangan kodenya, lalu saya coba susun dan pelajari sampai paham | test_insert_select dan test_kolom_tanpa_qualifier_satu_tabel berhasil dijalankan dan python -m pytest tidak menunjukkan kegagalan baru |
| 8 | Aulia | Saran awal AI menambah test di tests/test_lexer.py | Ditolak | test_lexer.py yang berasal dari file dosen tidak boleh diubah, dan penambahan test harus berada di tests/test_tambahan.py | Membaca docstring test_tambahan.py dan template LAPORAN_BUG |
| 9 | Aulia | Klaim AI lain yang digunakan rekan saya menjelaskan bahwa Bug 4, 6, dan 8 belum resolved | Ditolak | Klaim itu hanya dugaan tanpa menjalankan kode | Tiga test regresi dan python -m pytest saya jalankan sendiri, semuanya lulus |


**Refleksi (3-5 kalimat).** 
```
Aulia Rahmi Taufik:
AI paling membantu ketika saya mencari letak penyebab bug yang masih saya bingungkan. Pada bug <>, errornya muncul di parser, padahal masalahnya ada di lexer. Bug _pop yang hilang di _delete juga baru terlihat setelah saya membandingkan ketiga fungsi yang mengatur scope. Namun AI juga dapat melakukan kesalahan. Ia menyarankan menambah test di file milik dosen diluar test_tambahan.py padahal hal itu tidak perbolehkan dan penulisan test harus di test_tambahan.py dan AI juga menulis sebuah claim “sudah dicek” atas nama saya, padahal disini saya belum mengecek apa pun jadi tentunya kedua saran dari AI tersebut saya tolak. AI lain juga menyebut beberapa bug belum selesai tanpa disertai bukti, padahal tujuannya disini hanya ingin memvalidasi bug yang sudah resolved agar lebih yakin, sehingga saya menjalankan lagi secara mandiri test regresi dan pytest secara penuh, lalu menolak klaim tersebut karena hasilnya lulus.

```
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
