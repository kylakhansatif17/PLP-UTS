# Laporan Akhir

## 1. Hasil evaluasi

```
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')

```

## 2. Tiga kasus di mana regex salah
1. Komentar dibaca seperti perintah. Pada pemeliharaan.sql, dua baris pertama adalah komentar blok:
```sql
/* Skrip pemeliharaan data pelanggan.
   Catatan lama: UPDATE pelanggan_lama sudah tidak dipakai. */
select c.id, c.nama, a.kota
from crm.pelanggan c
left outer join crm.alamat a on a.pelanggan_id = c.id
```
Regex hanya mencari kata kunci di dalam teks, sehingga kata UPDATE di dalam komentar ikut ditangkap. Hasilnya, pelanggan_lama tercatat sebagai tabel yang di-update, padahal tabel itu tidak pernah dipakai. Statement SELECT di bawahnya juga dicatat di baris 2, padahal dimulai di baris 3, sehingga crm.pelanggan dan crm.alamat muncul di baris yang salah. Parser tidak mengalami ini karena lexer membuang komentar sebelum parser sempat melihatnya (SPESIFIKASI bagian 2.3, Crafting Interpreters bab 4). Bagi parser, statement baru dimulai dari kata select di baris 3.

2. Isi string dianggap bagian dari SQL. Pada laporan_penjualan.sql baris 6:

```sql
WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
```
Teks 'FROM rahasia' hanyalah nilai pembanding, tetapi regex mengenali kata FROM di dalamnya dan melaporkan tabel rahasia sebagai tabel yang dibaca. Tabel itu tidak ada. Lexer menangani ini dengan membaca satu string utuh dari kutip pembuka sampai kutip penutup menjadi satu token STRING (Crafting Interpreters bab 4, bagian literal string), sehingga isinya tidak pernah dianggap perintah. Kesalahan ini tercatat di baris 2, bukan baris 6, karena komentar di baris 2 ("-- DELETE FROM pelanggan") membuat regex mengira statement dimulai di sana. Itu penyebab yang sama dengan poin 1.

3. Struktur statement tidak dipahami. Pada audit.sql baris 16:
```sql
DELETE FROM sesi s WHERE s.kedaluwarsa < :sekarang;
```
Regex punya pola DELETE FROM untuk operasi D dan pola FROM untuk operasi R. Keduanya cocok pada teks yang sama, jadi sesi dilaporkan D dan R sekaligus. Kesalahan yang sama muncul pada laporan_penjualan.sql baris 15 (pesanan) dan campuran_error.sql baris 8 (keranjang). Parser tidak keliru karena grammar delete_stmt (SPESIFIKASI bagian 3) hanya mengenal satu tabel target, dan aturan CRUD bagian 5 memberinya D saja. Peran setiap kata ditentukan oleh posisinya dalam struktur grammar, bukan oleh kata itu sendiri (Crafting Interpreters bab 6).

## 3. Batas pendekatan kami
1. Kolom tanpa qualifier ketika ada lebih dari satu tabel.
```sql
SELECT nama FROM pelanggan, pesanan;
```
Resolver tidak tahu kolom nama milik pelanggan atau pesanan. Hasilnya berupa warning "kolom 'nama' ambigu tanpa skema", dan nilai resolved tetap kosong. CRUD matrix tingkat tabel masih benar (kedua tabel R), tetapi laporan kolom (--kolom) tidak bisa menyebut kolom itu milik tabel mana. Untuk mengatasinya dibutuhkan skema database, yaitu daftar kolom setiap tabel. Tool ini sengaja tidak memakai skema (SPESIFIKASI bagian 7, batasan 4).

2. Sintaks di luar lingkup: WITH dan UNION (SPESIFIKASI bagian 9).
```sql
WITH aktif AS (SELECT id FROM pelanggan WHERE aktif = 1) SELECT * FROM aktif;
SELECT id FROM pelanggan UNION SELECT pelanggan_id FROM pesanan;
```
Keduanya menghasilkan error sintaks, dan karena statement yang gagal di-parse tidak dihitung, tabel pelanggan dan pesanan hilang dari CRUD matrix sama sekali. Untuk mengatasinya, grammar di parser harus diperluas untuk WITH dan UNION, dan resolver harus punya aturan scope untuk nama CTE. Nama CTE seperti aktif bukan tabel sungguhan dan tidak boleh ikut dihitung.

3. Nama tabel dengan dan tanpa skema dihitung sebagai dua tabel berbeda.
```sql
SELECT 1 FROM crm.pelanggan p JOIN pelanggan q ON p.id = q.id;
```
CRUD matrix akan memuat dua tabel, crm.pelanggan dan pelanggan, padahal di database keduanya bisa saja tabel yang sama bila skema default-nya crm. Operasi pada tabel itu menjadi terpecah di dua kolom. Untuk menggabungkannya dibutuhkan informasi skema default (search_path) dan daftar tabel yang ada.

## 4. Pembagian kerja

Kami bersama-sama mengidentifikasi bug apa saja yang ada pada program. Kami menemukan terdapat 9 bug dan 3 fitur yang harus kami selesaikan. Lalu kami membagi pengerjaan tersebut dengan seimbang, Aulia mengerjakan bug sebagai berikut:
1. Keyword huruf kecil tidak dikenali.
2. Operator <> terpecah menjadi < dan >.
3. AND dan OR berpresedensi sama.
4. LEFT OUTER JOIN ditolak.
5. Scope DELETE tidak pernah di-pop. 

Lalu untuk fitur yang dikerjakan sebagai berikut:
1. INSERT ... SELECT (di parser).
2. Kolom tanpa qualifier (di resolver).

Kyla mengerjakan bug sebagai berikut:
1. Escape '' di dalam string.
2. Error recovery membuang semua sisa file.
3. Lookup scope mencari dari terluar.
4. Subquery di UPDATE dihitung U, bukan R.

Lalu untuk fitur yang dikerjakan sebagai berikut:
1. Komentar blok (di lexer). 

Cara agar setiap orang memahami kode yang diperbaiki adalah dengan mereview perbaikan satu sama lain sebelum melakukan tahap merge, jika sudah dipahami dan sama-sama setuju dengan solusinya, kami akan melakukan merge untuk pengerjaan yang dilakukan. Tidak sampai disitu, jika kami merasa masih perlu ada perbaikan yang dilakukan, kami akan berdiskusi sampai menemukan solusi terbaik yang kami sepakati.
