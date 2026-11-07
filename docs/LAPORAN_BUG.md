# Laporan Bug (bagian Kyla)

Ini empat bug yang aku perbaiki: Bug 3, 5, 7, dan 9. 

---

## Bug 3: String yang ada tanda `'` di dalamnya terpecah jadi dua

**Ditemukan oleh:** Kyla

**Diperbaiki oleh:** Kyla

**Gejala.** Di SQL, tanda `'` di dalam teks ditulis dua kali (`''`) dan artinya satu tanda `'`. Ini aturan di SPESIFIKASI.md bagian 2.4. Tapi kode lama malah memecah `'O''Brien'` jadi dua string.

- Hasil kode lama: string `O` dan string `Brien`
- Hasil yang benar: satu string `O'Brien`

**Reproduksi minimal.**

```sql
SELECT 'O''Brien' AS nama
```

**Akar masalah.** Bug ada di lexer, tahap scanning (*Crafting Interpreters* bab 4). Di fungsi `_string`, kode lama langsung menganggap string selesai begitu ketemu tanda `'`. Padahal `'` bisa berarti "string selesai" atau bisa juga bagian dari `''`. Untuk membedakannya, lexer harus melihat karakter sesudahnya. Kode lama tidak melakukan itu. Jadi di `'O''Brien'`, string ditutup setelah `O`, lalu `'Brien'` dianggap string baru.

**Perbaikan.** File `crud/lexer.py`, fungsi `_string`. Sekarang saat ketemu `'`, lexer mengintip karakter berikutnya dengan `_peek()`. Kalau karakter itu juga `'`, berarti itu bagian dari teks, jadi satu `'` ditambahkan ke string dan lexer lanjut membaca. Kalau bukan, string selesai.

Cara lain yang sempat terpikir: biarkan lexer memecah string dulu, lalu gabungkan dua string yang berdekatan setelahnya. Aku tidak pilih ini karena `'a' 'b'` memang dua string yang berbeda, nanti ikut tergabung padahal tidak seharusnya.

**Test regresi.** `test_string_dengan_kutip_ganda_escape`. Test ini gagal di kode lama dan lulus di kode baru. Ada juga tiga test kasus tepi: `test_tepi_string_apostrof_di_tengah`, `test_tepi_string_beberapa_apostrof`, `test_tepi_string_setelah_komentar`.

**Peran AI.** [ISI SESUAI KEJADIAN SEBENARNYA: pakai AI atau tidak, untuk apa, dan bagaimana kamu mengeceknya.]

---

## Bug 5: Satu error bikin semua statement sesudahnya hilang

**Ditemukan oleh:** Kyla

**Diperbaiki oleh:** Kyla

**Gejala.** Kalau satu statement error, statement setelahnya tidak ikut diproses. Padahal SPESIFIKASI.md bagian 6.2 bilang: setelah error, lompat sampai batas statement, lalu lanjut memproses sisanya.

- Hasil kode lama: 0 statement berhasil
- Hasil yang benar: 1 statement berhasil (`SELECT * FROM u`)

**Reproduksi minimal.**

```sql
SELECT * FROM t WHERE ;
SELECT * FROM u
```

**Akar masalah.** Bug ada di parser, pada bagian pemulihan error atau *panic mode* (*Crafting Interpreters* bab 6, bagian "Syntax Errors"). Setelah error, parser memanggil `_synchronize` untuk membuang token sampai ke tempat yang aman untuk mulai lagi. Di kode lama, fungsi ini cuma menghapus token terus-menerus sampai file habis. Dia tidak pernah berhenti di tempat yang aman. Akibatnya statement setelah error ikut terbuang, dan hasil CRUD matrix jadi kurang lengkap.

**Perbaikan.** File `crud/parser.py`, fungsi `_synchronize`. Sekarang parser berhenti kalau ketemu `;` atau keyword awal statement (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Setelah itu parsing lanjut seperti biasa.

Cara lain: berhenti hanya di `;`. Cara ini paling sesuai dengan teks spesifikasi dan lebih sederhana. Tapi kalau ada statement yang lupa diberi `;`, semuanya tetap hilang. Jadi aku pilih berhenti di keyword juga. Kekurangannya: kalau ada `SELECT` di dalam subquery yang rusak, parser bisa mengira itu awal statement baru dan memunculkan error tambahan.

**Test regresi.** `test_regresi_error_recovery_jangan_membuang_sisa_file`. Test ini gagal di kode lama dan lulus di kode baru. Ada juga dua test kasus tepi: `test_tepi_error_recovery_setelah_semicolon` dan `test_tepi_error_recovery_setelah_error_di_tengah_baris`.

**Peran AI.** [ISI SESUAI KEJADIAN SEBENARNYA.]

---

## Bug 7: Alias dicari dari scope paling luar, bukan yang paling dekat

**Ditemukan oleh:** Kyla

**Diperbaiki oleh:** Kyla

**Gejala.** Kalau nama alias yang sama dipakai di query luar dan di subquery, kolom di subquery malah diarahkan ke tabel milik query luar. Padahal SPESIFIKASI.md bagian 4.3 bilang: cari dari scope paling dalam dulu, yang paling dekat yang menang.

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

**Peran AI.** [ISI SESUAI KEJADIAN SEBENARNYA.]

---

## Bug 9: Tabel di subquery pada UPDATE ikut ditandai `U`

**Ditemukan oleh:** Kyla

**Diperbaiki oleh:** Kyla

**Gejala.** Pada `UPDATE`, tabel yang cuma dibaca di dalam subquery ikut ditandai `U` (Update). Menurut SPESIFIKASI.md bagian 5, hanya tabel yang diubah (target `UPDATE`) yang `U`. Tabel di subquery hanya dibaca, jadi harus `R`.

- Tabel `p` (yang diubah): kode lama `U`, seharusnya `U` (sudah benar)
- Tabel `q` (di subquery): kode lama `U`, seharusnya `R`

**Reproduksi minimal.**

```sql
UPDATE p SET s = 1 WHERE id IN (SELECT id FROM q);
```

**Akar masalah.** Ini bukan bug di lexer atau parser. Pohon dan resolver-nya sudah benar. Yang salah ada di analyzer, yaitu bagian yang menentukan operasi CRUD tiap tabel. Fungsi `_collect` meneruskan operasi statement induk (`U`) begitu saja ke semua subquery di dalamnya. Padahal operasi sebuah tabel ditentukan oleh perannya: apakah dia yang diubah, atau cuma dibaca. Subquery selalu cuma membaca, jadi operasinya harus `R`, apa pun jenis statement induknya.

**Perbaikan.** File `crud/analyzer.py`. Di `_collect`, subquery (`IN (SELECT ...)`, `EXISTS`, dan subquery biasa) sekarang selalu diproses dengan operasi `"R"`. Fungsi `reads` di `column_usage` juga disesuaikan dengan aturan yang sama.

Cara lain: bikin pengecualian khusus untuk `UPDATE`. Aku tidak pilih ini karena nanti logikanya bercabang per jenis statement. Aturan "subquery itu baca" berlaku sama untuk semua statement, jadi lebih rapi dibuat satu aturan umum.

**Test regresi.** `test_regresi_subquery_di_update_dihitung_r_bukan_u`. Test ini gagal di kode lama dan lulus di kode baru. Test mengecek bahwa `produk.stok` bertanda `U`, sedangkan `gudang.stok`, `gudang.produk_id`, dan `produk_terjual.id` bertanda `R`.

**Peran AI.** [ISI SESUAI KEJADIAN SEBENARNYA.]
