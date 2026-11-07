# Laporan Bug

Dokumen ini mencatat sembilan bug yang ditemukan, diperbaiki, dan diverifikasi.

---

## Bug 1: Keyword huruf kecil tidak dikenali

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** Input `select 1 from t;` menghasilkan `ParseError: Baris 1, kolom 1: diharapkan awal statement (SELECT, INSERT, UPDATE, DELETE), ditemukan 'select'`, dan tidak ada statement yang terbentuk. Menurut `SPESIFIKASI.md` bagian 2.2, keyword tidak peka huruf besar/kecil dan nilai token keyword dinormalkan ke huruf besar. Test bawaan `test_keyword_huruf_kecil` gagal karena `select` dibaca sebagai token `IDENT`, bukan `KEYWORD 'SELECT'`.

**Reproduksi minimal.**

```sql
select 1 from t;
```

**Akar masalah.** Penyebabnya ada di `Lexer._word`. Setelah satu kata selesai dibaca, kata itu langsung dicari di `KEYWORDS` tanpa diubah hurufnya dulu (`text in KEYWORDS`), padahal isi `KEYWORDS` huruf besar semua. Karena itu kata `select` tidak ketemu di daftar dan dianggap `IDENT`, bukan keyword.

Bagian ini sesuai dengan tahap "reserved words and identifiers" di *Crafting Interpreters* bab 4 (bagian 4.7): scanner membaca satu kata penuh lebih dulu, lalu mengecek ke tabel kata cadangan untuk menentukan apakah kata itu keyword atau identifier. Bedanya, tabel di Lox peka huruf besar/kecil, sedangkan SQL tidak, sehingga kode dari buku tidak bisa dipakai begitu saja. Kata harus disamakan hurufnya dulu sebelum dicari di tabel.

Nilai token juga harus dinormalkan ke huruf besar, karena parser membandingkan `tok.value` dengan string huruf besar lewat `_check_kw`. Kalau tidak, token tetap salah walaupun tipenya sudah benar. Dampaknya, parser menolak input di `_statement` karena token pertama bertipe `IDENT`, bukan `KEYWORD`.

**Perbaikan.** File `crud/lexer.py`, fungsi `Lexer._word`. Kata diubah ke huruf besar (`upper = text.upper()`), dicek ke `KEYWORDS` memakai versi huruf besar itu, dan nilai token keyword disimpan huruf besar. Token `IDENT` tidak diubah, karena spesifikasi 2.2 menyerahkan penurunan huruf kecil nama tabel, alias, dan kolom ke parser.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Mengubah isi `KEYWORDS` menjadi huruf kecil: melanggar spesifikasi (nilai token harus huruf besar) dan merusak parser yang membandingkan dengan string huruf besar.
2. Membuat parser tidak peka huruf besar/kecil: hanya memindahkan masalah, token `select` tetap bertipe `IDENT` sehingga kontrak lexer tetap salah.

**Test regresi.** `test_keyword_huruf_campuran_dikenali` di `tests/test_tambahan.py` (input `SeLeCt * FrOm t`). Gagal sebelum perbaikan karena `FrOm` bertipe `IDENT`, lulus sesudahnya. Test bawaan `test_keyword_huruf_kecil` juga ikut mencakup bug ini.

**Peran AI.** Membantu saya berdiskusi dan memastikan bahwa Bug 1 yang saya temukan memang bug. Setelah saya menyusun solusinya sendiri, AI membantu memvalidasi apakah perbaikan itu sudah benar atau masih ada yang salah. Saya memverifikasinya dengan menjalankan test regresi `test_keyword_huruf_campuran_dikenali` yang gagal sebelum perbaikan dan lulus sesudahnya, lalu menjalankan `python -m pytest`.

---

## Bug 2: Operator `<>` terpecah menjadi `<` dan `>`

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** `SELECT 1 FROM t WHERE a <> 1;` menghasilkan `ParseError: Baris 1, kolom 26: diharapkan ekspresi, ditemukan '>'`. Menurut `SPESIFIKASI.md` bagian 2.5, `<>` adalah satu token `OP` (maximal munch). Pada `laporan_penjualan.sql` baris 6 error yang sama muncul (`Baris 6, kolom 41 ... ditemukan '>'`), sehingga file itu gagal di-parse.

**Reproduksi minimal.**

```sql
SELECT 1 FROM t WHERE a <> 1;
```

**Akar masalah.** Pesan error yang muncul menyebut tanda `>` ditemukan di tempat yang seharusnya berisi ekspresi, sehingga awalnya terlihat seperti kesalahan parser. Setelah urutan tokennya diperiksa, ternyata input `a <> 1` sudah terpecah sejak tahap lexer menjadi `a`, `<`, `>`, dan `1`. Di lexer, cabang untuk karakter `<` hanya menanyakan apakah karakter berikutnya `=`, sehingga `<=` dikenali tetapi `<>` tidak. Menurut *Crafting Interpreters* bab 4 bagian 4.5, setiap operator dua karakter memang perlu pengecekan sendiri lewat `match()`, dan untuk `<>` pengecekan itu belum ada. Lexer berhenti di `<`, tanda `>` dibaca sebagai token baru, dan parser akhirnya bertemu `>` di posisi operand. Jadi pesan error di parser hanyalah akibat, sedangkan sumbernya ada di lexer.

**Perbaikan.** File `crud/lexer.py`, cabang `<`. Setelah cek `<=`, ditambah cabang `elif self._match(">")` yang menghasilkan `<>`, selain itu tetap `<`. Parser, resolver, dan analyzer tidak diubah.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Menggabungkan token `<` dan `>` yang berurutan di parser: salah tahap, dan `a < > 1` (dengan spasi) ikut diterima padahal bukan operator `<>`.
2. Mencocokkan operator terpanjang dari sebuah tabel operator juga benar, tetapi lebih besar dari kebutuhan karena hanya satu cabang yang kurang.

**Test regresi.** `test_operator_tidak_sama_diamond_satu_token` di `tests/test_tambahan.py` (input `a <> 1` harus menghasilkan `IDENT`, `OP '<>'`, `NUMBER`). Gagal sebelum perbaikan (empat token), lulus sesudahnya.

**Peran AI.** Saya awalnya bingung bagian mana yang harus diubah agar `<>` dihasilkan sebagai satu token. Saya berdiskusi dengan AI untuk menelusuri akar masalahnya, yaitu cabang `<` di lexer yang hanya mengecek `=`, dan memahami solusinya. Setelah paham saya menyusun kode perbaikannya di lexer. Verifikasinya: test regresi `test_operator_tidak_sama_diamond_satu_token` gagal sebelum perbaikan dan lulus sesudahnya, error `>` di `laporan_penjualan.sql` baris 6 hilang, dan hasil `python -m pytest` tidak menunjukkan bug baru.

---

## Bug 3: String yang ada tanda `'` di dalamnya terpecah jadi dua

**Ditemukan oleh:** Kyla · **Diperbaiki oleh:** Kyla

**Gejala.** Di SQL, tanda `'` di dalam teks ditulis dua kali (`''`) dan artinya satu tanda `'`. Ini aturan di `SPESIFIKASI.md` bagian 2.4. Tapi kode lama malah memecah `'O''Brien'` jadi dua string.

- Hasil kode lama: string `O` dan string `Brien`
- Hasil yang benar: satu string `O'Brien`

**Reproduksi minimal.**

```sql
SELECT 'O''Brien' AS nama
```

**Akar masalah.** Bug ada di lexer, tahap scanning (*Crafting Interpreters* bab 4). Di fungsi `_string`, kode lama langsung menganggap string selesai begitu ketemu tanda `'`. Padahal `'` bisa berarti "string selesai" atau bisa juga bagian dari `''`. Untuk membedakannya, lexer harus melihat karakter sesudahnya. Kode lama tidak melakukan itu. Jadi di `'O''Brien'`, string ditutup setelah `O`, lalu `'Brien'` dianggap string baru.

**Perbaikan.** File `crud/lexer.py`, fungsi `_string`. Sekarang saat ketemu `'`, lexer mengintip karakter berikutnya dengan `_peek()`. Kalau karakter itu juga `'`, berarti itu bagian dari teks, jadi satu `'` ditambahkan ke string dan lexer lanjut membaca. Kalau bukan, string selesai.

Cara lain yang sempat terpikir: biarkan lexer memecah string dulu, lalu gabungkan dua string yang berdekatan setelahnya. Saya tidak memilih ini karena `'a' 'b'` memang dua string yang berbeda, nanti ikut tergabung padahal tidak seharusnya.

**Test regresi.** `test_string_dengan_kutip_ganda_escape`. Test ini gagal di kode lama dan lulus di kode baru. Ada juga tiga test kasus tepi: `test_tepi_string_apostrof_di_tengah`, `test_tepi_string_beberapa_apostrof`, `test_tepi_string_setelah_komentar`. Catatan: `test_tepi_string_setelah_komentar` di kode lama gagal karena komentar blok `/* ... */` belum didukung (`LexError`), jadi test itu menjaga kombinasi komentar dan string, bukan bagian dari bug `''` itu sendiri.

**Peran AI.** Saya menelusuri sendiri kenapa `'O''Brien'` terpecah: `_string` menutup string begitu ketemu `'` pertama tanpa melihat karakter sesudahnya. Solusinya juga dari saya, yaitu mengintip karakter berikutnya dengan `_peek()`. Kalau karakter itu `'` lagi, satu `'` ditambahkan ke isi string dan pembacaan lanjut, kalau bukan, string selesai. AI baru terlibat saat saya menyusun test: ia mengarahkan saya membuat test regresi dan tiga test kasus tepi, lalu saya jalankan di kode lama dan kode baru. Setelah laporan ini selesai, AI memeriksanya terhadap kode. Hasilnya, `test_string_dengan_kutip_ganda_escape`, `test_tepi_string_apostrof_di_tengah`, dan `test_tepi_string_beberapa_apostrof` gagal di kode lama dan lulus di kode baru, dan token `O` + `Brien` berubah menjadi satu string `O'Brien`. Dari pemeriksaan itu juga terlihat bahwa `test_tepi_string_setelah_komentar` gagal di kode lama karena komentar blok belum didukung, bukan karena bug `''`, sehingga catatannya saya tambahkan di bagian Test regresi.

---

## Bug 4: `AND` dan `OR` berpresedensi sama

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** Untuk `WHERE a = 1 OR b = 2 AND c = 3`, parser membentuk `AND(OR(a=1, b=2), c=3)`. Menurut `SPESIFIKASI.md` bagian 3.1, `AND` lebih kuat daripada `OR`, sehingga hasilnya harus `OR(a=1, AND(b=2, c=3))`. Contoh nyata: `audit.sql` baris 4 sampai 6 menghasilkan akar `AND` dengan anak kiri `OR`. Pada sampel yang ada, CRUD matrix tidak berubah karena kedua cabang ikut ditelusuri, tetapi bentuk AST salah dan AST termasuk API publik (`SPESIFIKASI.md` bagian 7).

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** Hasil parsing `a = 1 OR b = 2 AND c = 3` ternyata berbentuk `AND` di akar pohon dengan `OR` di sebelah kiri, seolah-olah `OR` dikerjakan lebih dulu. Ini mirip menghitung `1 + 2 * 3` dari kiri ke kanan tanpa memberi perkalian prioritas yang lebih tinggi. Penyebabnya ada di `Parser._logical`, di mana fungsi ini membaca `AND` dan `OR` dalam satu loop, yaitu `while self._check_kw("AND", "OR")`, sehingga keduanya berada di tingkat yang sama dan sama-sama dikelompokkan dari kiri. Di *Crafting Interpreters* bab 6 (presedensi dan asosiatif, lalu recursive descent), tingkat presedensi diwujudkan dengan fungsi bertingkat: operator yang ikatannya lebih kuat ditangani oleh fungsi yang dipanggil lebih dalam. Artinya dibutuhkan satu fungsi untuk `OR` yang memanggil fungsi untuk `AND`, dan fungsi `AND` itulah yang memanggil `_not`. Satu loop tidak bisa melakukannya karena hanya mampu menyatakan satu tingkat.

**Perbaikan.** File `crud/parser.py`. `_logical` sekarang hanya menangani `OR` dan memanggil `_and`. Fungsi baru `_and` menangani `AND` dan memanggil `_not`. `_expr`, `_not`, dan `_comparison` tidak diubah. Urutan panggilannya adalah `_expr`, lalu `_logical` (`OR`), lalu `_and` (`AND`), lalu `_not`, lalu `_comparison`. Ini mengikuti grammar spesifikasi bagian 3 (`or_expr`, `and_expr`). `AND` milik `BETWEEN` tetap aman karena dibaca di `_comparison` (batas bawahnya `additive`), dan asosiatif kiri dipertahankan.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Menukar urutan pengecekan `AND` dan `OR` di dalam satu loop: tidak akan bisa, karena satu loop tidak dapat menyatakan dua tingkat presedensi.

**Test regresi.** `test_and_lebih_kuat_dari_or` di `tests/test_tambahan.py`. Gagal sebelum perbaikan (akar `AND`, bukan `OR`), lulus sesudahnya.

**Peran AI.** Saya sudah menemukan bahwa akar masalahnya ada pada fungsi `_logical` di parser, karena `AND` dan `OR` diproses dalam satu loop yang sama. Namun saya masih bingung bagaimana cara memperbaikinya. Di tahap ini AI membantu mengarahkan saya menyusun solusinya, yaitu memisahkan `OR` dan `AND` menjadi dua fungsi (`_logical` untuk `OR` dan `_and` untuk `AND`). Setelah itu saya menjalankan `test_and_lebih_kuat_dari_or` dan hasilnya gagal sebelum perbaikan dan lulus sesudah perbaikan.

---

## Bug 5: Satu error bikin semua statement sesudahnya hilang

**Ditemukan oleh:** Kyla · **Diperbaiki oleh:** Kyla

**Gejala.** Kalau satu statement error, statement setelahnya tidak ikut diproses. Padahal `SPESIFIKASI.md` bagian 6.2 bilang: setelah error, lompat sampai batas statement, lalu lanjut memproses sisanya.

- Hasil kode lama: 0 statement berhasil
- Hasil yang benar: 1 statement berhasil (`SELECT * FROM u`)

**Reproduksi minimal.**

```sql
SELECT * FROM t WHERE ;
SELECT * FROM u
```

**Akar masalah.** Bug ada di parser, pada bagian pemulihan error atau *panic mode* (*Crafting Interpreters* bab 6, bagian "Syntax Errors"). Setelah error, parser memanggil `_synchronize` untuk membuang token sampai ke tempat yang aman untuk mulai lagi. Di kode lama, fungsi ini cuma menghapus token terus-menerus sampai file habis. Dia tidak pernah berhenti di tempat yang aman. Akibatnya statement setelah error ikut terbuang, dan hasil CRUD matrix jadi kurang lengkap.

**Perbaikan.** File `crud/parser.py`, fungsi `_synchronize`. Sekarang parser berhenti tepat saat bertemu `;`. Tanda `;` itu tidak dibuang di `_synchronize`, tetapi oleh loop `parse_script` lewat `self._match(T.SEMICOLON)` pada iterasi berikutnya, lalu parsing lanjut ke statement sesudahnya. Ini sesuai `SPESIFIKASI.md` bagian 6.2: buang token sampai dan termasuk `;`, dan setiap statement rusak menghasilkan tepat satu error.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Berhenti di `;` dan juga di keyword awal statement (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Versi ini sempat saya pakai lebih dulu, karena statement yang lupa diberi `;` tetap bisa diselamatkan. Tetapi `SELECT` di dalam subquery yang rusak dianggap awal statement baru, sehingga satu statement rusak menghasilkan lebih dari satu error. Contohnya `SELECT * FROM WHERE id IN (SELECT id FROM u);` menghasilkan dua error, dan error kedua palsu. Ini melanggar aturan "tepat satu error" di spesifikasi 6.2.

Kekurangan versi sekarang: statement yang lupa diberi `;` dan rusak akan membuang token sampai `;` berikutnya, sehingga statement sesudahnya ikut hilang. Spesifikasi menetapkan `;` sebagai batas statement, jadi hal ini diterima.

**Test regresi.** `test_regresi_error_recovery_jangan_membuang_sisa_file`. Test ini gagal di kode lama dan lulus di kode baru. Ada juga tiga test kasus tepi: `test_tepi_error_recovery_setelah_semicolon`, `test_tepi_error_recovery_setelah_error_di_tengah_baris`, dan `test_tepi_error_recovery_satu_error_per_statement_dengan_subquery`. Test terakhir mengecek bahwa SQL di atas menghasilkan tepat satu error dan statement `SELECT * FROM v` tetap terparse. Test ini lulus di versi sekarang dan gagal bila cabang keyword ditambahkan lagi ke `_synchronize`.

**Peran AI.** Pada bug ini saya sendiri yang melacak bahwa statement sesudah error hilang karena `_synchronize` hanya menghapus token sampai akhir file. Rancangan awal perbaikannya dari saya: berhenti di `;` atau di keyword awal statement. AI membantu menyusun test regresi dan test kasus tepi, yang saya jalankan di kode lama dan kode baru. Saat AI memeriksa laporan terhadap kode dan spesifikasi, ia menemukan bahwa rancangan awal saya menyimpang dari spesifikasi 6.2 dan membuktikannya dengan `SELECT * FROM WHERE id IN (SELECT id FROM u);`, yang menghasilkan dua error padahal seharusnya satu. Saya menerima temuan itu, lalu mengubah `_synchronize` agar berhenti hanya di `;` dan menulis sendiri test `test_tepi_error_recovery_satu_error_per_statement_dengan_subquery`. Saya memverifikasinya dengan menambahkan kembali cabang keyword sementara waktu: test gagal, dan lulus lagi setelah dikembalikan. Hasil `python -m pytest` menunjukkan seluruh test lulus.

---

## Bug 6: `LEFT OUTER JOIN` ditolak

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** `SELECT 1 FROM a LEFT OUTER JOIN b ON a.id = b.id;` menghasilkan `ParseError: Baris 1, kolom 22: diharapkan JOIN, ditemukan 'OUTER'`, padahal seharusnya diterima dan menghasilkan `Join` bertipe `LEFT`. Grammar `SPESIFIKASI.md` bagian 3 menulis `join = [ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN" ...`. `pemeliharaan.sql` baris 5 menggunakan bentuk ini, dan `OUTER` sudah terdaftar di `KEYWORDS`, jadi lexer memang berniat untuk mengenalinya.

**Reproduksi minimal.**

```sql
SELECT 1 FROM a LEFT OUTER JOIN b ON a.id = b.id;
```

**Akar masalah.** Jika dicocokkan dengan grammar pada spesifikasi bagian 3, aturan join berbunyi `LEFT [OUTER] JOIN`, artinya kata `OUTER` boleh ada boleh tidak di antara `LEFT` dan `JOIN`. Kodenya tidak mengikuti aturan itu. Di `Parser._join`, begitu `LEFT` terbaca, parser langsung menuntut `JOIN` lewat `_expect_kw("JOIN")`, jadi `OUTER` tidak punya tempat dan dilaporkan sebagai kesalahan (`Baris 1, kolom 22: diharapkan JOIN, ditemukan 'OUTER'`). Padahal lexer sudah mengenali `OUTER` sebagai keyword, jadi tokennya sampai ke parser dengan benar. Yang tertinggal hanya fungsi parsernya. Di *Crafting Interpreters* bab 6 (bagian 6.2, recursive descent), setiap fungsi parser dibuat sesuai satu aturan grammar, dan bagian yang opsional ditulis sebagai `if match(...)`. Bagian `[OUTER]` belum diterjemahkan seperti itu di `_join`.

**Perbaikan.** File `crud/parser.py`, fungsi `_join`. Setelah `kind = "LEFT"` ditambah satu baris `self._match_kw("OUTER")`. `JOIN` tetap wajib sesudahnya, dan jenis join tetap `LEFT`.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Menerima `OUTER` di mana saja sebelum `JOIN`: solusi ini terlalu longgar dan melanggar grammar, karena `OUTER JOIN` tanpa `LEFT` ikut lolos.

**Test regresi.** `test_left_outer_join_diterima` di `tests/test_tambahan.py`. Gagal sebelum perbaikan (ada `ParseError`), lulus sesudahnya (tanpa error dan jenis `LEFT`).

**Peran AI.** Saya menemukan bug ini dari pesan error `diharapkan JOIN, ditemukan 'OUTER'` dan saya telusuri sampai ke fungsi `_join` di parser. AI membantu saya mencocokkan kode dengan grammar pada spesifikasi bagian 3, lalu menjelaskan bahwa bagian opsional `[ "OUTER" ]` diterapkan dengan satu pemanggilan `_match_kw("OUTER")` setelah `LEFT`. Lalu saya mencoba melakukan perubahan tersebut pada `_join`. Untuk memverifikasinya saya menjalankan `test_left_outer_join_diterima`, yang gagal sebelum perbaikan dan lulus sesudah diperbaiki. Saya juga memastikan `OUTER JOIN` tanpa `LEFT` tetap ditolak (`test_tepi_outer_tanpa_left_tetap_ditolak`) dan `python -m pytest` tidak memunculkan bug baru.

---

## Bug 7: Alias dicari dari scope paling luar, bukan yang paling dekat

**Ditemukan oleh:** Kyla · **Diperbaiki oleh:** Kyla

**Gejala.** Kalau nama alias yang sama dipakai di query luar dan di subquery, kolom di subquery malah diarahkan ke tabel milik query luar. Padahal `SPESIFIKASI.md` bagian 4.3 bilang: cari dari scope paling dalam dulu, yang paling dekat yang menang.

- Hasil kode lama: `x.id` dianggap milik tabel `a` (luar)
- Hasil yang benar: `x.id` milik tabel `b` (subquery)

**Reproduksi minimal.**

```sql
SELECT 1 FROM a x WHERE EXISTS (SELECT 1 FROM b x WHERE x.id = 1);
```

**Akar masalah.** Bug ada di resolver, tahap pencarian nama (*Crafting Interpreters* bab 11). Scope itu bersarang seperti rantai: subquery punya scope sendiri, dan scope itu punya "induk" yaitu scope query luarnya. Aturan mencarinya: mulai dari scope paling dalam, kalau tidak ada baru naik ke induknya. Jadi kalau nama sama ada di dalam dan di luar, yang dalam yang dipakai. Kode lama di fungsi `_lookup` mengumpulkan seluruh rantai scope ke sebuah list, lalu membacanya dengan `reversed`, yaitu dari luar ke dalam. Urutannya terbalik, jadi yang luar yang menang.

**Perbaikan.** File `crud/resolver.py`, fungsi `Resolver._lookup`. Sekarang pakai loop biasa: mulai dari scope saat ini, cek isinya, kalau tidak ketemu naik ke induknya, dan berhenti begitu ketemu. List `chain` dan `reversed` dihapus.

Cara lain: tetap pakai list `chain` tapi hapus `reversed`. Hasilnya sama benar, tapi membuat list hanya untuk dibaca lagi itu boros dan kurang jelas maksudnya. Loop langsung lebih jelas menunjukkan aturan "yang paling dekat menang".

**Test regresi.** `test_regresi_lookup_scope_terdekat_diutamakan` dan `test_tepi_lookup_fallback_ke_parent_jika_tidak_ada_di_inner`. Test kedua mengecek kasus saat nama hanya ada di scope luar, dan harus tetap ketemu.

**Peran AI.** Kesalahan urutan pencarian ini saya temukan sendiri di `_lookup`: rantai scope dikumpulkan ke sebuah list lalu dibaca dengan `reversed`, sehingga scope terluar yang menang. Solusi yang saya pilih adalah mengganti list itu dengan loop yang mulai dari scope saat ini dan naik ke induknya sampai nama ketemu. AI membantu di bagian test, yaitu mengarahkan saya membuat test regresi untuk alias yang sama di query luar dan di subquery, serta test kasus tepi untuk nama yang hanya ada di scope luar. Saat memeriksa laporan, AI mereproduksi contoh di atas: `x.id` mengarah ke tabel `a` di kode lama dan ke tabel `b` di kode baru. `test_regresi_lookup_scope_terdekat_diutamakan` gagal di kode lama dan lulus di kode baru, sedangkan test fallback ke parent lulus di keduanya. Itu memang tujuannya, yaitu memastikan pencarian ke scope induk tidak ikut rusak.

---

## Bug 8: Scope `DELETE` tidak pernah di-pop

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** Alias dari statement `DELETE` ternyata masih terbaca oleh statement sesudahnya. Pada `DELETE FROM a x;` yang diikuti `SELECT x.id FROM b;`, resolver tidak memberi laporan apa pun dan `x.id` malah diarahkan ke tabel `a` (`{('a', 'id', 'R')}`). Padahal `x` tidak pernah didefinisikan di `SELECT` itu, sehingga seharusnya muncul error `alias 'x' tidak terdefinisi` (`SPESIFIKASI.md` bagian 4.3). Bagian 4.5 juga menyebutkan bahwa tidak boleh ada scope yang tersisa setelah satu statement selesai. Kasus ini terlihat pada `audit.sql`, yaitu alias `s` didefinisikan di `DELETE` baris 16, lalu digunakan di `SELECT` baris 18 tanpa definisi, tetapi error yang diharapkan tidak muncul.

**Reproduksi minimal.**

```sql
DELETE FROM a x;
SELECT x.id FROM b;
```

**Akar masalah.** Jika ketiga fungsi pembuat scope di resolver dibandingkan, ada satu yang berbeda. `Resolver._select` dan `Resolver._update` sama-sama memanggil `_push()` di awal dan `_pop()` di akhir, sedangkan `Resolver._delete` hanya memanggil `_push()` dan tidak pernah `_pop()`. Di *Crafting Interpreters* bab 11 (resolving blocks, lewat `beginScope` dan `endScope`), setiap scope yang dibuka harus ditutup lagi di akhir blok. Karena `_delete` tidak menutupnya, `self.scope` tetap menunjuk ke scope milik `DELETE` setelah statement itu selesai. Statement berikutnya lalu membuat scope barunya sebagai anak dari scope `DELETE` tersebut, ibarat membuka lembar catatan baru di atas lembar lama yang tidak pernah ditutup. Alhasil, alias dari statement yang sudah selesai masih bisa ditemukan oleh statement sesudahnya.

**Perbaikan.** File `crud/resolver.py`, fungsi `_delete`. Ditambah satu baris `self._pop()` di akhir fungsi, sehingga pola push/pop sama dengan `_select` dan `_update`. Sesudah perbaikan, `x.id` pada contoh di atas menghasilkan error `alias 'x' tidak terdefinisi`, dan `self.scope` bernilai `None` setelah semua statement selesai.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Mereset `self.scope = None` di awal setiap statement di `resolve_statement`: ini menutup kebocoran, tetapi menyembunyikan ketidakseimbangan push/pop dan bisa menutupi bug serupa di tempat lain.

**Test regresi.** `test_regresi_delete_scope_pop_setelah_statement` di `tests/test_tambahan.py`. Sebelum perbaikan test ini gagal, karena scope `DELETE` tidak pernah ditutup sehingga `resolver.scope` masih terisi dan error `alias 'x' tidak terdefinisi` tidak muncul. Setelah perbaikan, scope milik `DELETE` ditutup begitu statementnya selesai, sehingga alias `x` tidak lagi terbaca oleh `SELECT` berikutnya dan error `alias 'x' tidak terdefinisi` muncul. Dengan begitu test lulus.

**Peran AI.** Awalnya saya kebingungan mengapa `x.id` pada `SELECT` bisa lolos tanpa error padahal alias `x` hanya ada di `DELETE` sebelumnya. Saya lalu berdiskusi dengan AI, dan dari pembacaan bersama ketiga fungsi scope di resolver terlihat bahwa hanya `_delete` yang membuka scope tanpa menutupnya. Satu baris `self._pop()` kemudian ditambahkan di akhir fungsi itu. Hasilnya saya cek dengan `test_regresi_delete_scope_pop_setelah_statement`. Test ini gagal sebelum saya melakukan perbaikan dan lulus sesudah diperbaiki.

---

## Bug 9: Tabel di subquery pada `UPDATE` ikut ditandai `U`

**Ditemukan oleh:** Kyla · **Diperbaiki oleh:** Kyla

**Gejala.** Pada `UPDATE`, tabel yang cuma dibaca di dalam subquery ikut ditandai `U` (Update). Menurut `SPESIFIKASI.md` bagian 5, hanya tabel yang diubah (target `UPDATE`) yang `U`. Tabel di subquery hanya dibaca, jadi harus `R`.

- Tabel `p` (yang diubah): kode lama `U`, seharusnya `U` (sudah benar)
- Tabel `q` (di subquery): kode lama `U`, seharusnya `R`

**Reproduksi minimal.**

```sql
UPDATE p SET s = 1 WHERE id IN (SELECT id FROM q);
```

**Akar masalah.** Ini bukan bug di lexer atau parser. Pohon dan resolver-nya sudah benar. Yang salah ada di analyzer, yaitu bagian yang menentukan operasi CRUD tiap tabel. Fungsi `_collect` meneruskan operasi statement induk (`U`) begitu saja ke semua subquery di dalamnya. Padahal operasi sebuah tabel ditentukan oleh perannya: apakah dia yang diubah, atau cuma dibaca. Subquery selalu cuma membaca, jadi operasinya harus `R`, apa pun jenis statement induknya.

Konsepnya mirip dengan resolver di *Crafting Interpreters* bab 11: sebuah pass menelusuri pohon sambil membawa konteks, dan konteks itu harus diganti ketika masuk ke bagian pohon yang punya aturan sendiri. Di sini konteks `op` dari `UPDATE` terbawa terus ke subquery, padahal subquery punya aturan sendiri, yaitu selalu `R`.

**Perbaikan.** File `crud/analyzer.py`. Di `_collect`, subquery (`IN (SELECT ...)`, `EXISTS`, dan subquery biasa) sekarang selalu diproses dengan operasi `"R"`. Fungsi `reads` di `column_usage` ditulis ulang dengan parameter `op`, dan kolom di dalam subquery selalu diberi `R`.

Cara lain: bikin pengecualian khusus untuk `UPDATE`. Saya tidak memilih ini karena nanti logikanya bercabang per jenis statement. Aturan "subquery itu baca" berlaku sama untuk semua statement, jadi lebih rapi dibuat satu aturan umum.

**Test regresi.** `test_regresi_subquery_di_update_dihitung_r_bukan_u`. Test ini gagal di kode lama dan lulus di kode baru. Test mengecek bahwa `produk.stok` bertanda `U`, sedangkan `gudang.stok`, `gudang.produk_id`, dan `produk_terjual.id` bertanda `R`. Ada juga `test_update_where_kolom_terbaca_bukan_termutakhirkan`, yang mengecek bahwa kolom di `WHERE` pada `UPDATE` (`p.id`) bertanda `R`, sedangkan kolom yang diubah (`p.s`) bertanda `U`.

**Peran AI.** Kesimpulan bahwa kesalahannya ada di analyzer, bukan di parser atau resolver, saya buat sendiri: `_collect` meneruskan operasi `U` milik `UPDATE` ke subquery di dalamnya. Solusi saya adalah memproses subquery selalu sebagai `R`, dan menulis ulang `reads` di `column_usage` dengan parameter `op` supaya kolom di subquery juga `R`. AI mengarahkan saya menyusun test regresinya, yaitu `produk.stok` harus `U` sedangkan `gudang.stok`, `gudang.produk_id`, dan `produk_terjual.id` harus `R`, yang lalu saya jalankan di kode lama dan kode baru. Saat memeriksa laporan, AI mengonfirmasi hasil lama (`p` dan `q` sama-sama `U`) dan hasil baru (`p` tetap `U`, `q` menjadi `R`).

AI juga menemukan bahwa perubahan saya menimbulkan regresi: kolom di `WHERE` pada `UPDATE` (misalnya `p.id`) ikut berubah dari `R` menjadi `U`, padahal di kode awal dosen kolom itu `R`, dan hal ini tidak tercakup test. Keputusan saya: dikembalikan ke `R` (`reads(stmt.where, "R")`) dan ditambah `test_update_where_kolom_terbaca_bukan_termutakhirkan`, karena `SPESIFIKASI.md` bagian 5 hanya menetapkan target `UPDATE` sebagai `U`, sedangkan kolom di `WHERE` hanya dibaca. Setelah perubahan itu seluruh test lulus. Kaitan ke bab 11 *Crafting Interpreters* di bagian Akar masalah awalnya disarankan AI, lalu saya pelajari sampai bisa menjelaskannya sendiri.