# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Keyword huruf kecil tidak dikenali

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** Input select 1 from t; menghasilkan ParseError: Baris 1, kolom 1: diharapkan awal statement (SELECT, INSERT, UPDATE, DELETE), ditemukan 'select', dan tidak ada statement yang terbentuk. Menurut SPESIFIKASI.md bagian 2.2, keyword tidak peka huruf besar/kecil dan nilai token keyword dinormalkan ke huruf besar. Test bawaan test_keyword_huruf_kecil gagal karena select dibaca sebagai token IDENT, bukan KEYWORD 'SELECT'

**Reproduksi minimal.** 

```sql
select 1 from t;
```

**Akar masalah.** Penyebabnya ada di Lexer._word. Setelah satu kata selesai dibaca, kata itu langsung dicari di KEYWORDS tanpa diubah hurufnya dulu (text in KEYWORDS), padahal isi KEYWORDS huruf besar semua. Karena itu kata select tidak ketemu di daftar dan dianggap IDENT, bukan keyword.

Bagian ini sesuai dengan tahap "reserved words and identifiers" di Crafting Interpreters bab 4 (bagian 4.7): scanner membaca satu kata penuh lebih dulu, lalu mengecek ke tabel kata cadangan untuk menentukan apakah kata itu keyword atau identifier. Bedanya, tabel di Lox peka huruf besar/kecil, sedangkan SQL tidak, sehingga kode dari buku tidak bisa dipakai begitu saja. Kata harus disamakan hurufnya dulu sebelum dicari di tabel.

Nilai token juga harus dinormalkan ke huruf besar, karena parser membandingkan tok.value dengan string huruf besar lewat _check_kw. Kalau tidak, token tetap salah walaupun tipenya sudah benar. Dampaknya, parser menolak input di _statement karena token pertama bertipe IDENT, bukan KEYWORD.

**Perbaikan.** File crud/lexer.py, fungsi Lexer._word. Kata diubah ke huruf besar (upper = text.upper()), dicek ke KEYWORDS memakai versi huruf besar itu, dan nilai token keyword disimpan huruf besar. Token IDENT tidak diubah, karena spesifikasi 2.2 menyerahkan penurunan huruf kecil nama tabel, alias, dan kolom ke parser.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Mengubah isi KEYWORDS menjadi huruf kecil: melanggar spesifikasi (nilai token harus huruf besar) dan merusak parser yang membandingkan dengan string huruf besar.
2. Membuat parser tidak peka huruf besar/kecil: hanya memindahkan masalah, token select tetap bertipe IDENT sehingga kontrak lexer tetap salah.

**Test regresi.** test_keyword_huruf_campuran_dikenali di tests/test_tambahan.py (input SeLeCt * FrOm t). Gagal sebelum perbaikan karena FrOm bertipe IDENT, lulus sesudahnya. Test bawaan test_keyword_huruf_kecil juga ikut mencakup bug ini.

**Peran AI.** Membantu saya berdiskusi dan memastikan bahwa Bug 1 yang saya temukan memang
bug. Setelah saya menyusun solusinya sendiri, AI membantu memvalidasi apakah perbaikan itu
sudah benar atau masih ada yang salah. Saya memverifikasinya dengan menjalankan test regresi 'test_keyword_huruf_campuran_dikenali' yang gagal sebelum perbaikan dan lulus sesudahnya, lalu menjalankan 'python -m pytest'. 

---
## Bug 2: Operator <> terpecah menjadi < dan >

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** SELECT 1 FROM t WHERE a <> 1; menghasilkan ParseError: Baris 1, kolom 26: diharapkan ekspresi, ditemukan '>'. Menurut SPESIFIKASI.md bagian 2.5, <> adalah satu token OP (maximal munch). Pada laporan_penjualan.sql baris 6 error yang sama muncul (Baris 6, kolom 41 ... ditemukan '>'), sehingga file itu gagal di-parse.

**Reproduksi minimal.** 

```sql
SELECT 1 FROM t WHERE a <> 1; 
```

**Akar masalah.** Pesan error yang muncul menyebut tanda ">" ditemukan di tempat yang seharusnya berisi ekspresi, sehingga awalnya terlihat seperti kesalahan parser. Setelah urutan tokennya diperiksa, ternyata input a <> 1 sudah terpecah sejak tahap lexer menjadi a, <, >, dan 1. Di lexer, cabang untuk karakter "<" hanya menanyakan apakah karakter berikutnya "=", sehingga "<=" dikenali tetapi "<>" tidak. Menurut Crafting Interpreters bab 4 bagian 4.5, setiap operator dua karakter memang perlu pengecekan sendiri lewat match(), dan untuk "<>" pengecekan itu belum ada. Lexer berhenti di "<", tanda ">" dibaca sebagai token baru, dan parser akhirnya bertemu ">" di posisi operand. Jadi pesan error di parser hanyalah akibat, sedangkan sumbernya ada di lexer.

**Perbaikan.** File crud/lexer.py, cabang <. Setelah cek <=, ditambah cabang elif self._match(">") yang menghasilkan <>, selain itu tetap <. Parser, resolver, dan analyzer tidak diubah.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Menggabungkan token < dan > yang berurutan di parser: salah tahap, dan a < > 1 (dengan spasi) ikut diterima padahal bukan operator <>.
2. Mencocokkan operator terpanjang dari sebuah tabel operator juga benar, tetapi lebih besar dari kebutuhan karena hanya satu cabang yang kurang.


**Test regresi.** test_operator_tidak_sama_diamond_satu_token di tests/test_tambahan.py (input a <> 1 harus menghasilkan IDENT, OP '<>', NUMBER). Gagal sebelum perbaikan (empat token), lulus sesudahnya.

**Peran AI.** Saya awalnya bingung bagian mana yang harus diubah agar '<>' dihasilkan sebagai satu token. Saya berdiskusi dengan AI untuk menelusuri akar masalahnya dimana cabang '<' di lexer hanya mengecek '=' dan memahami solusinya. Setelah paham saya menyusun kode perbaikannya di lexer. Untuk verifikasi dari bug 2 ini ada pada test regresi 'test_operator_tidak_sama_diamond_satu_token' gagal sebelum
perbaikan dan lulus sesudahnya, error '>' di 'laporan_penjualan.sql' baris 6 hilang, dan hasil 'python -m pytest' tidak menunjukkan bug baru.

---
## Bug 4: AND dan OR berpresedensi sama

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** Untuk WHERE a = 1 OR b = 2 AND c = 3, parser membentuk AND(OR(a=1, b=2), c=3). Menurut SPESIFIKASI.md bagian 3.1, AND lebih kuat daripada OR, sehingga hasilnya harus OR(a=1, AND(b=2, c=3)). Contoh nyata: audit.sql baris 4 sampai 6 menghasilkan akar AND dengan anak kiri OR. Pada sampel yang ada, CRUD matrix tidak berubah karena kedua cabang ikut ditelusuri, tetapi bentuk AST salah dan AST termasuk API publik (SPESIFIKASI.md bagian 7).

**Reproduksi minimal.** 

```sql
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** Hasil parsing a = 1 OR b = 2 AND c = 3 ternyata berbentuk AND di akar pohon dengan OR di sebelah kiri, seolah-olah OR dikerjakan lebih dulu. Ini mirip menghitung 1 + 2 * 3 dari kiri ke kanan tanpa memberi perkalian prioritas yang lebih tinggi. Penyebabnya ada di Parser._logical dimana fungsi ini membaca AND dan OR dalam satu loop, yaitu while self._check_kw("AND", "OR"), sehingga keduanya berada di tingkat yang sama dan sama-sama dikelompokkan dari kiri. Di Crafting Interpreters bab 6 (presedensi dan asosiatif, lalu recursive descent), tingkat presedensi diwujudkan dengan fungsi bertingkat: operator yang ikatannya lebih kuat ditangani oleh fungsi yang dipanggil lebih dalam. Artinya dibutuhkan satu fungsi untuk OR yang memanggil fungsi untuk AND, dan fungsi AND itulah yang memanggil _not. Satu loop tidak bisa melakukannya karena hanya mampu menyatakan satu tingkat.

**Perbaikan.** File crud/parser.py. _logical sekarang hanya menangani OR dan memanggil _and. Fungsi baru _and menangani AND dan memanggil _not. _expr, _not, dan _comparison tidak diubah. Urutan panggilan nya adalah _expr, lalu _logical (OR), lalu _and (AND), lalu _not _comparison. Ini mengikuti grammar spesifikasi bagian 3 (or_expr, and_expr). AND milik BETWEEN tetap aman karena dibaca di _comparison (batas bawahnya additive), dan asosiatif kiri dipertahankan.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Menukar urutan cek di dalam satu loop tetapi tidak akan bisa, karena satu loop tidak dapat menyatakan dua tingkat presedensi.


**Test regresi.** test_and_lebih_kuat_dari_or di tests/test_tambahan.py. Gagal sebelum perbaikan (akar AND, bukan OR), lulus sesudahnya.

**Peran AI.** Saya sudah menemukan bahwa akar masalahnya ada pada fungsi '_logical' di parser, karena AND dan OR diproses dalam satu loop yang sama. Namun saya masih bingung bagaimana cara memperbaikinya. Di tahap ini AI membantu mengarahkan saya menyusun
solusinya, yaitu memisahkan OR dan AND menjadi dua fungsi ('_logical' untuk OR dan '_and' untuk AND). Setelah itu saya menjalankan 'test_and_lebih_kuat_dari_or' dimana hasilnya gagal sebelum perbaikan dan lulus sesudah perbaikan.

---
## Bug 6: LEFT OUTER JOIN ditolak

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** SELECT 1 FROM a LEFT OUTER JOIN b ON a.id = b.id; menghasilkan ParseError: Baris 1, kolom 22: diharapkan JOIN, ditemukan 'OUTER', padahal seharusnya diterima dan menghasilkan Join bertipe LEFT. Grammar SPESIFIKASI.md bagian 3 menulis join = [ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN" .... pemeliharaan.sql baris 5 menggunakan bentuk ini, dan OUTER sudah terdaftar di KEYWORDS, jadi lexer memang berniat untuk mengenalinya.

**Reproduksi minimal.** 

```sql
SELECT 1 FROM a LEFT OUTER JOIN b ON a.id = b.id;
```

**Akar masalah.** Jika dicocokkan dengan grammar pada spesifikasi bagian 3, aturan join berbunyi LEFT [OUTER] JOIN, artinya kata OUTER boleh ada boleh tidak di antara LEFT dan JOIN. Kodenya tidak mengikuti aturan itu. Di Parser._join, begitu LEFT terbaca, parser langsung menuntut JOIN lewat _expect_kw("JOIN"), jadi OUTER tidak punya tempat dan dilaporkan sebagai kesalahan (Baris 1, kolom 22: diharapkan JOIN, ditemukan 'OUTER'). Padahal lexer sudah mengenali OUTER sebagai keyword, jadi tokennya sampai ke parser dengan benar. Yang tertinggal hanya fungsi parsernya. Di Crafting Interpreters bab 6 (bagian 6.2, recursive descent), setiap fungsi parser dibuat sesuai satu aturan grammar, dan bagian yang opsional ditulis sebagai if match(...). Bagian [OUTER] belum diterjemahkan seperti itu di _join.

**Perbaikan.** File crud/parser.py, fungsi _join. Setelah kind = "LEFT" ditambah satu baris self._match_kw("OUTER"). JOIN tetap wajib sesudahnya, dan jenis join tetap LEFT. 

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Menerima OUTER di mana saja sebelum JOIN tetapi solusi ini terlalu longgar dan melanggar grammar, karena OUTER JOIN tanpa LEFT ikut lolos.

**Test regresi.** test_left_outer_join_diterima di tests/test_tambahan.py. Gagal sebelum perbaikan (ada ParseError), lulus sesudahnya (tanpa error dan jenis LEFT).

**Peran AI.** Saya menemukan bug ini dari pesan error 'diharapkan JOIN, ditemukan 'OUTER'' dan saya telusuri sampai ke fungsi '_join' di parser. AI membantu saya mencocokkan kode dengan grammar pada spesifikasi bagian 3, lalu menjelaskan bahwa bagian opsional '[ "OUTER" ]' diterapkan dengan satu pemanggilan '_match_kw("OUTER")' setelah 'LEFT'. Lalu saya coba untuk melakukan perubahan tersebut pada '_join'.  Untuk memverifikasinya saya menjalankan 'test_left_outer_join_diterima' dimana test gagal sebelum perbaikan dan lulus ketika sudah diperbaiki. Saya juga memastikan 'OUTER JOIN' tanpa 'LEFT' tetap ditolak dan 'python -m pytest' tidak memunculkan suatu bug baru.

---

## Bug 8: Scope DELETE tidak pernah di-pop

**Ditemukan oleh:** Aulia Rahmi Taufik · **Diperbaiki oleh:** Aulia Rahmi Taufik

**Gejala.** Alias dari statement 'DELETE' ternyata masih terbaca oleh statement sesudahnya. Pada 'DELETE FROM a x;' yang diikuti 'SELECT x.id FROM b;', resolver tidak memberi laporan apa pun dan 'x.id' malah diarahkan ke tabel 'a' ('{('a', 'id', 'R')}'). Padahal 'x'
tidak pernah didefinisikan di 'SELECT' itu, sehingga seharusnya muncul error 'alias 'x' tidak terdefinisi' (SPESIFIKASI.md bagian 4.3). Bagian 4.5 juga menyebutkan bahwa tidak boleh ada scope yang tersisa setelah satu statement selesai. Kasus ini terlihat pada 'audit.sql' yaitu alias 's' didefinisikan di 'DELETE' baris 16, lalu digunakan di 'SELECT' baris 18 tanpa definisi, tetapi error yang diharapkan tidak muncul.

**Reproduksi minimal.** 

```sql
DELETE FROM a x;
SELECT x.id FROM b;
```

**Akar masalah.** Jika ketiga fungsi pembuat scope di resolver dibandingkan, ada satu yang berbeda. Resolver._select dan Resolver._update sama-sama memanggil _push() di awal dan _pop() di akhir, sedangkan Resolver._delete hanya memanggil _push() dan tidak pernah _pop(). Di Crafting Interpreters bab 11 (resolving blocks, lewat beginScope dan endScope), setiap scope yang dibuka harus ditutup lagi di akhir blok. Karena _delete tidak menutupnya, self.scope tetap menunjuk ke scope milik DELETE setelah statement itu selesai. Statement berikutnya lalu membuat scope barunya sebagai anak dari scope DELETE tersebut, ibarat membuka lembar catatan baru di atas lembar lama yang tidak pernah ditutup. Alhasil, alias dari statement yang sudah selesai masih bisa ditemukan oleh statement sesudahnya.

**Perbaikan.** File crud/resolver.py, fungsi _delete. Ditambah satu baris self._pop() di akhir fungsi, sehingga pola push/pop sama dengan _select dan _update. Sesudah perbaikan, x.id pada contoh di atas menghasilkan error alias 'x' tidak terdefinisi, dan self.scope bernilai None setelah semua statement selesai.

Alternatif yang dipertimbangkan dan tidak dipilih:

1. Mereset self.scope = None di awal setiap statement di resolve_statement dimana akan menutup kebocoran, tetapi menyembunyikan ketidakseimbangan push/pop dan bisa menutupi bug serupa di tempat lain.

**Test regresi.** test_regresi_delete_scope_pop_setelah_statement di tests/test_tambahan.py. Sebelum perbaikan test ini gagal, karena scope DELETE tidak pernah ditutup sehingga resolver.scope masih terisi dan error 'alias 'x'' tidak
terdefinisi' tidak muncul. Setelah perbaikan, scope milik DELETE ditutup begitu statement nya selesai, sehingga alias 'x' tidak lagi terbaca oleh SELECT berikutnya dan error 'alias 'x' tidak terdefinisi' muncul. Dengan begitu test lulus.

**Peran AI.** Awalnya saya kebingungan mengapa 'x.id' pada 'SELECT' bisa lolos tanpa error padahal alias 'x' hanya ada di 'DELETE' sebelumnya. Saya lalu berdiskusi dengan AI, dan dari pembacaan bersama ketiga fungsi scope di resolver terlihat bahwa hanya '_delete' yang membuka scope tanpa menutupnya. Satu baris 'self._pop()' kemudian ditambahkan di akhir fungsi itu. Hasilnya saya cek dengan 'test_regresi_delete_scope_pop_setelah_statement'. test ini gagal sebelum saya melakukan perbaikan dan lulus sesudah diperbaiki.