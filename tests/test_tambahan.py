"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud.lexer import LexError, TokenType as T, tokenize

def test_keyword_huruf_campuran_dikenali():
    toks = tokenize("SeLeCt * FrOm t")
    assert [(t.type, t.value) for t in toks[:3]] == [
        (T.KEYWORD, "SELECT"), (T.STAR, "*"), (T.KEYWORD, "FROM")
    ]

def test_regresi_komentar_blok_multi_baris_dilewati():
    """Bug: komentar blok /* ... */ sebelumnya memicu LexError."""
    toks = tokenize("/* komentar\n   dua baris */ SELECT")
    assert toks[0].value == "SELECT" and toks[0].line == 2

# Lima edge-case yang sering gagal bila lexer tidak menangani komentar blok dengan benar.
def test_tepi_komentar_blok_di_awal_file():
    # Risiko: token setelah komentar bisa ikut terlewat jika offset tidak diperbarui dengan benar.
    toks = tokenize("/* awal */ select * from t")
    assert toks[0].value == "SELECT" and toks[1].value == "*"

def test_tepi_komentar_blok_dengan_spasi_sebelum_select():
    # Risiko: whitespace setelah penutup komentar bisa mengganggu token berikutnya.
    toks = tokenize("/* isi */\n  SELECT\n  id")
    assert toks[0].value == "SELECT" and toks[0].line == 2

def test_tepi_keyword_campur_huruf_setelah_komentar():
    # Risiko: lexer harus tetap case-insensitive walaupun komentar berada tepat sebelum keyword.
    toks = tokenize("/* x */ SeLeCt * FrOm t")
    assert toks[0].value == "SELECT" and toks[1].value == "*" and toks[2].value == "FROM"

def test_tepi_komentar_blok_tidak_ditutup():
    # Risiko: EOF yang tidak tertutup harus gagal dengan pesan yang jelas, bukan token acak.
    with pytest.raises(LexError, match="komentar blok"):
        tokenize("/* belum ditutup\nSELECT")

def test_tepi_komentar_baris_dan_blok_bersama():
    # Risiko: campuran komentar menumbuhkan offset dan line yang salah jika skip tidak konsisten.
    toks = tokenize("-- komentar baris\n/* blok */\nSELECT id FROM t")
    assert toks[0].value == "SELECT"
    assert toks[1].value == "id"
    assert toks[2].value == "FROM"

def test_operator_tidak_sama_diamond_satu_token():
    toks = [t for t in tokenize("a <> 1") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [(T.IDENT, "a"), (T.OP, "<>"), (T.NUMBER, "1")]
