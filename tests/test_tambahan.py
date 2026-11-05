"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
from crud.lexer import tokenize, TokenType as T
def test_keyword_huruf_campuran_dikenali():
    toks = tokenize("Select sElEcT SELECT")
    assert [(t.type, t.value) for t in toks[:3]] == [(T.KEYWORD, "SELECT")] * 3
