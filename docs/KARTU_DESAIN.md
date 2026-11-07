# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

Istilah yang dipakai:

- R = Read (tabel hanya dibaca). U = Update (tabel diubah).
- Scope adalah daftar nama tabel dan alias yang berlaku untuk satu `SELECT`, `UPDATE`, atau `DELETE`.
- Scope induk adalah scope dari statement yang membungkus subquery.
- Subquery adalah `SELECT` di dalam tanda kurung di dalam statement lain, misalnya `(SELECT id FROM u)`.
- Kode awal adalah kode yang diberikan dosen sebelum kami perbaiki.

1. Keputusan: Menangani escaped quote di dalam string. Di fungsi `_string` pada lexer, setiap kali bertemu tanda petik tunggal, lexer melihat satu karakter berikutnya dengan `_peek()`. Jika karakter itu juga petik tunggal, lexer menambahkan satu petik tunggal ke isi string dan melanjutkan pembacaan. Jika bukan petik tunggal, string berakhir di situ. Contoh: `'O''Brien'` menjadi satu string bernilai `O'Brien`.
   Alternatif yang ditolak: Menyimpan `'O''Brien'` sebagai dua string lalu menggabungkannya di belakang. Alternatif ini juga akan menggabungkan dua string yang benar-benar terpisah, seperti `'a' 'b'`, padahal keduanya berbeda.
   Alasan: Spesifikasi 2.4 menyatakan bahwa `''` di dalam string adalah bagian dari isi string, bukan penutup string. Keputusan harus dibuat saat lexer sedang membaca string, karena yang menentukan adalah karakter berikutnya.

2. Keputusan: Error recovery berhenti di `;`. Setelah satu statement error, fungsi `_synchronize` membuang token sampai bertemu `;`. Setelah itu, loop di `parse_script` membuang `;` tersebut dan parser lanjut membaca statement berikutnya.
   Alternatif yang ditolak: Berhenti di keyword `SELECT`, `INSERT`, `UPDATE`, atau `DELETE` yang pertama kali ditemukan.
   Alasan: Jika berhenti di keyword berikutnya, pada `SELECT * FROM WHERE id IN (SELECT id FROM u);` parser berhenti di `SELECT` di dalam kurung dan membacanya sebagai statement baru. Statement baru itu berakhir di `)` tanpa `;`, sehingga muncul error kedua yang salah, padahal kesalahan aslinya hanya satu (`FROM` tanpa nama tabel). Spesifikasi 6.2 menetapkan satu statement rusak menghasilkan tepat satu error, dan `;` adalah pembatas statement.

3. Keputusan: Mencari alias mulai dari scope paling dalam. Fungsi `_lookup` di resolver memakai loop yang mulai dari scope aktif. Jika nama belum ada di scope itu, pencarian berlanjut ke scope induk. Pencarian berhenti begitu nama ditemukan.
   Alternatif yang ditolak: Mengumpulkan semua scope ke dalam list lalu membacanya dari luar ke dalam dengan `reversed`.
   Alasan: Scope paling dekat harus menang. Jika pencarian dimulai dari scope paling luar, alias di subquery tidak bisa menimpa alias dengan nama sama di query induk. Loop langsung menuliskan aturan "scope terdekat dipakai lebih dulu" tanpa membuat list tambahan (spesifikasi 4.3). Subquery tetap bisa memakai alias dari query luar, karena pencarian pindah ke scope induk kalau nama tidak ada di scope sendiri.

4. Keputusan: Tabel di subquery selalu dinilai `R`. Di fungsi `_collect`, semua subquery diproses dengan operasi `R`. Di fungsi `column_usage`, kolom di `WHERE` pada `UPDATE` juga `R`. Hanya kolom yang diisi nilai baru di `SET` yang dinilai `U`.
   Alternatif yang ditolak: Membiarkan operasi `U` dari `UPDATE` diteruskan ke subquery atau ke kolom di `WHERE`. Atau membuat pengecualian khusus untuk `UPDATE`.
   Alasan: Operasi sebuah tabel ditentukan oleh apa yang dilakukan terhadap tabel itu: apakah tabel diubah atau hanya dibaca. Subquery selalu dibaca, apa pun jenis statement yang membungkusnya. Jadi satu aturan yang sama untuk semua statement lebih sederhana dan sesuai dengan spesifikasi bagian 5.

5. Keputusan: Presedensi `AND` dan `OR` dibuat dengan dua fungsi. `_logical` hanya membaca `OR` dan memanggil `_and`, sementara `_and` hanya membaca `AND` dan memanggil `_not`. Urutan panggilannya adalah `_expr` → `_logical` → `_and` → `_not` → `_comparison`. Contoh: `a = 1 OR b = 2 AND c = 3` dibaca sebagai `a = 1 OR (b = 2 AND c = 3)`.
   Alternatif yang ditolak: Membaca `AND` dan `OR` dalam satu loop, seperti kode awal. Atau tetap satu loop lalu menukar urutan pengecekan `AND` dan `OR`.
   Alasan: Satu loop memperlakukan `AND` dan `OR` setara, sehingga ekspresi dikelompokkan dari kiri ke kanan. Akibatnya `a = 1 OR b = 2 AND c = 3` dibaca sebagai `(a = 1 OR b = 2) AND c = 3`, yang salah. Dengan dua fungsi, `AND` diproses sebelum `OR`, sesuai grammar spesifikasi bagian 3.
