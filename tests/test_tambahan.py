"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest
from crud.analyzer import column_usage
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.resolver import Resolver, Scope, ScopeEntry


def parse_all(sql: str):
    return parse_sql(sql).statements


def test_keyword_huruf_campuran_dikenali():
    toks = tokenize("SeLeCt * FrOm t")
    assert [(t.type, t.value) for t in toks[:3]] == [
        (T.KEYWORD, "SELECT"), (T.STAR, "*"), (T.KEYWORD, "FROM")
    ]

def test_regresi_komentar_blok_multi_baris_dilewati():
    """Bug: komentar blok /* ... */ sebelumnya memicu LexError."""
    toks = tokenize("/* komentar\n   dua baris */ SELECT")
    assert toks[0].value == "SELECT" and toks[0].line == 2

def test_operator_tidak_sama_diamond_satu_token():
    toks = [t for t in tokenize("a <> 1") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [(T.IDENT, "a"), (T.OP, "<>"), (T.NUMBER, "1")]

def test_string_dengan_kutip_ganda_escape():
    toks = [t for t in tokenize("SELECT 1 FROM t WHERE a = 'it''s'") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [
        (T.KEYWORD, "SELECT"),
        (T.NUMBER, "1"),
        (T.KEYWORD, "FROM"),
        (T.IDENT, "t"),
        (T.KEYWORD, "WHERE"),
        (T.IDENT, "a"),
        (T.OP, "="),
        (T.STRING, "it's"),
    ]

def test_and_lebih_kuat_dari_or():
    sc = parse_sql("SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;")
    w = sc.statements[0].where
    assert w.op == "OR"
    assert w.right.op == "AND"


def test_regresi_error_recovery_jangan_membuang_sisa_file():
    """Bug: error recovery semula membuang seluruh sisa file setelah satu statement gagal."""
    sql = """
    SELECT * FROM t WHERE ;
    SELECT * FROM u
    """
    stmts = parse_all(sql)
    assert len(stmts) >= 1
    assert any(getattr(s, "sources", None) and s.sources[0].name == "u" for s in stmts)

def test_left_outer_join_diterima():
    sc = parse_sql("SELECT 1 FROM a LEFT OUTER JOIN b ON a.id = b.id;")
    assert sc.errors == []
    assert sc.statements[0].joins[0].kind == "LEFT"

def test_regresi_lookup_scope_terdekat_diutamakan():
    outer = Scope()
    inner = Scope(parent=outer)
    outer.entries["u"] = ScopeEntry("u", "outer.users", 1)
    inner.entries["u"] = ScopeEntry("u", "inner.users", 2)

    resolver = Resolver()
    resolver.scope = inner

    assert resolver._lookup("u").table == "inner.users"


def test_regresi_subquery_di_update_dihitung_u_bukan_r():
    sql = """
    UPDATE produk
    SET stok = (
        SELECT MAX(gudang.stok) FROM gudang WHERE gudang.produk_id = produk.id
    )
    WHERE id IN (SELECT produk_terjual.id FROM produk_terjual);
    """
    script = parse_sql(sql)
    assert script.errors == []
    Resolver().resolve_script(script)

    usage = column_usage(script.statements[0])
    assert ("gudang", "stok", "U") in usage
    assert ("gudang", "produk_id", "U") in usage
    assert ("produk_terjual", "id", "U") in usage


def test_scope_delete_tidak_bocor_ke_statement_berikutnya():
    sc = parse_sql("DELETE FROM a x;\nSELECT x.id FROM b;")
    diags = Resolver().resolve_script(sc)
    assert any(d.level == "error" and "tidak terdefinisi" in d.message for d in diags)

def test_regresi_delete_scope_pop_setelah_statement():
    """Bug 8: scope DELETE harus diselesaikan sebelum statement berikutnya dibaca."""
    resolver = Resolver()
    script = parse_sql("DELETE FROM a x WHERE x.id = 1; SELECT x.id FROM b;")

    diags = resolver.resolve_script(script)

    assert resolver.scope is None
    assert any(d.level == "error" and "tidak terdefinisi" in d.message for d in diags)
    
# Lima edge-case yang sering gagal bila lexer tidak menangani komentar blok dengan benar.
def test_tepi_komentar_blok_di_awal_file():
    # Risiko: token setelah komentar bisa ikut terlewat jika offset tidak diperbarui dengan benar.
    toks = tokenize("/* awal */ select * from t")
    assert toks[0].value == "SELECT" and toks[1].value == "*"

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

def test_tepi_string_apostrof_di_tengah():
    # Risiko: apostrof yang escaped di tengah string harus tetap menjadi satu literal, bukan penutup string.
    toks = [t for t in tokenize("SELECT 'O''Brien' AS nama") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [
        (T.KEYWORD, "SELECT"),
        (T.STRING, "O'Brien"),
        (T.KEYWORD, "AS"),
        (T.IDENT, "nama"),
    ]

def test_tepi_string_beberapa_apostrof():
    # Risiko: beberapa escape dalam satu literal harus dipertahankan semua, bukan dibreak di karakter pertama.
    toks = [t for t in tokenize("SELECT 'A''B''C' AS kode") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [
        (T.KEYWORD, "SELECT"),
        (T.STRING, "A'B'C"),
        (T.KEYWORD, "AS"),
        (T.IDENT, "kode"),
    ]

def test_tepi_string_setelah_komentar():
    # Risiko: komentar sebelumnya tidak boleh memengaruhi parsing literal string berikutnya.
    toks = [t for t in tokenize("/* x */ SELECT 'it''s' FROM t") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [
        (T.KEYWORD, "SELECT"),
        (T.STRING, "it's"),
        (T.KEYWORD, "FROM"),
        (T.IDENT, "t"),
    ]

def test_tepi_between_and_tidak_tertukar_dengan_and_logika():
    # Risiko: BETWEEN punya AND sendiri. Setelah AND/OR dipisah jadi dua tingkat,
    # AND milik BETWEEN tidak boleh dibaca sebagai AND logika, dan sebaliknya.
    sc = parse_sql("SELECT 1 FROM t WHERE x BETWEEN 1 AND 2 AND y = 3;")
    assert sc.errors == []
    w = sc.statements[0].where
    assert w.op == "AND"
    assert type(w.left).__name__ == "Between"
    assert w.right.op == "="
    
def test_tepi_error_recovery_setelah_semicolon():
    # Risiko: setelah error di satu statement, parser harus tetap menemukan statement berikutnya setelah semicolon.
    sql = "SELECT * FROM t WHERE ; SELECT * FROM u;"
    stmts = parse_all(sql)
    assert len(stmts) >= 1
    assert any(getattr(s, "sources", None) and s.sources[0].name == "u" for s in stmts)

def test_tepi_error_recovery_setelah_error_di_tengah_baris():
    # Risiko: error di tengah baris tidak boleh memaksa parser menelan seluruh file sampai EOF.
    sql = "SELECT * FROM t WHERE a = 1 AND ;\nSELECT * FROM u;"
    stmts = parse_all(sql)
    assert len(stmts) >= 1
    assert any(getattr(s, "sources", None) and s.sources[0].name == "u" for s in stmts)

def test_tepi_outer_tanpa_left_tetap_ditolak():
    # Risiko: setelah OUTER dibuat opsional, parser bisa ikut menerima OUTER
    # di sembarang tempat. Menurut grammar, OUTER hanya sah setelah LEFT.
    sc = parse_sql("SELECT 1 FROM a OUTER JOIN b ON a.id = b.id;")
    assert len(sc.errors) == 1
    assert sc.statements == []
    
def test_tepi_lookup_fallback_ke_parent_jika_tidak_ada_di_inner():
    outer = Scope()
    inner = Scope(parent=outer)
    outer.entries["u"] = ScopeEntry("u", "outer.users", 1)

    resolver = Resolver()
    resolver.scope = inner

    assert resolver._lookup("u").table == "outer.users"

def test_tepi_tidak_ada_scope_tersisa_setelah_resolve():
    # Risiko: satu push tanpa pop saja membuat scope bocor ke statement berikutnya
    # (spesifikasi 4.5). Diuji lewat tiga jenis statement sekaligus.
    sc = parse_sql("DELETE FROM a x WHERE x.id = 1; UPDATE b SET v = 1; SELECT 1 FROM c;")
    r = Resolver()
    r.resolve_script(sc)
    assert r.scope is None