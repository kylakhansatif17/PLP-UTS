# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text

```

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1.
2.
3.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.
2.
3.

## 4. Pembagian kerja

Kami bersama-sama mengidentifikasi bug apa saja yang ada pada program. Kami menemukan terdapat 9 bug dan 3 fitur yang harus kami selesaikan. Lalu kami membagi pengerjaan tersebut dengan seimbang, Aulia mengerjakan bug sebagai berikut:
1. Keyword huruf kecil tidak dikenali.
2. Operator <> terpecah menjadi < dan >.
3. AND dan OR berpresedensi sama.
4. LEFT OUTER JOIN ditolak.
5. Scope DELETE tidak pernah di-pop. 

Lalu untuk fitur yang dikerjakan sebagai berikut:
1. test_insert_select
2. test_kolom_tanpa_qualifier_satu_tabel. 

Kyla mengerjakan bug sebagai berikut:
1. Escape '' di dalam string.
2. Error recovery membuang semua sisa file.
3. Lookup scope mencari dari terluar.
4. Subquery di UPDATE dihitung U, bukan R.
Lalu untuk fitur yang dikerjakan sebagai berikut:
1. test_komentar_blok
2. test_matrix_laporan_penjualan 

Cara agar setiap orang memahami kode yang diperbaiki adalah dengan mereview perbaikan satu sama lain sebelum melakukan tahap merge, jika sudah dipahami dan sama-sama setuju dengan solusinya, kami akan melakukan merge untuk pengerjaan yang dilakukan. Tidak sampai disitu, jika kami merasa masih perlu ada perbaikan yang dilakukan, kami akan berdiskusi sampai menemukan solusi terbaik yang kami sepakati.
