"""Analyzer CRUD. Aturan lokal proyek ini: SPESIFIKASI.md bagian 5."""
from collections import defaultdict
from dataclasses import fields

from . import ast_nodes as ast


def analyze_statement(stmt) -> dict[str, set[str]]:
    """Mengembalikan {nama_tabel: {operasi}} untuk satu statement."""
    usage: dict[str, set[str]] = defaultdict(set)
    if isinstance(stmt, ast.Select):
        _collect_select(stmt, usage, "R")
    elif isinstance(stmt, ast.Insert):
        usage[stmt.table.name].add("C")
        for row in stmt.values:
            for expr in row:
                _collect(expr, usage, "R")
        if stmt.query is not None:
            _collect_select(stmt.query, usage, "R")
    elif isinstance(stmt, ast.Update):
        usage[stmt.table.name].add("U")
        for assignment in stmt.assignments:
            _collect(assignment.value, usage, "U")
        _collect(stmt.where, usage, "U")
    elif isinstance(stmt, ast.Delete):
        usage[stmt.table.name].add("D")
        _collect(stmt.where, usage, "R")
    return dict(usage)


def _collect_select(sel: ast.Select, usage, op: str) -> None:
    """Menandai semua tabel di SELECT (termasuk subquery-nya) dengan `op`."""
    for src in sel.sources + [j.source for j in sel.joins]:
        if isinstance(src, ast.TableRef):
            usage[src.name].add(op)
        else:
            _collect_select(src.query, usage, op)
    for item in sel.columns:
        if isinstance(item, ast.SelectItem):
            _collect(item.expr, usage, op)
    for join in sel.joins:
        _collect(join.condition, usage, op)
    _collect(sel.where, usage, op)
    for expr in sel.group_by:
        _collect(expr, usage, op)
    for item in sel.order_by:
        _collect(item.expr, usage, op)


def _collect(expr, usage, op: str) -> None:
    """Menandai tabel di setiap subquery di dalam ekspresi dengan `R`.

    Aturan lokal proyek: tabel target UPDATE hanya mendapat `U`; subquery yang
    dibaca di dalam nilai/WHERE tetap `R`.
    """
    if expr is None:
        return
    if isinstance(expr, ast.BinaryOp):
        _collect(expr.left, usage, op)
        _collect(expr.right, usage, op)
    elif isinstance(expr, ast.UnaryOp):
        _collect(expr.operand, usage, op)
    elif isinstance(expr, ast.InExpr):
        _collect(expr.expr, usage, op)
        for value in expr.values or []:
            _collect(value, usage, op)
        if expr.query is not None:
            _collect_select(expr.query, usage, "R")
    elif isinstance(expr, ast.Between):
        _collect(expr.expr, usage, op)
        _collect(expr.low, usage, op)
        _collect(expr.high, usage, op)
    elif isinstance(expr, ast.IsNull):
        _collect(expr.expr, usage, op)
    elif isinstance(expr, (ast.Exists, ast.Subquery)):
        _collect_select(expr.query, usage, "R")
    elif isinstance(expr, ast.FunctionCall):
        for arg in expr.args:
            _collect(arg, usage, op)


def column_usage(stmt) -> set[tuple[str, str, str]]:
    """Penggunaan kolom (tabel, kolom, operasi). Membutuhkan resolver sudah
    dijalankan, karena memakai ColumnRef.resolved."""
    result: set[tuple[str, str, str]] = set()

    def reads(node, op: str = "R") -> None:
        if node is None:
            return
        if isinstance(node, list):
            for item in node:
                reads(item, op)
            return
        if isinstance(node, ast.ColumnRef):
            if node.resolved and not node.resolved.startswith("<"):
                result.add((node.resolved, node.name, op))
            return
        if isinstance(node, (ast.Subquery, ast.Exists)):
            reads(node.query, "R")
            return
        if isinstance(node, ast.InExpr):
            reads(node.expr, op)
            for value in node.values or []:
                reads(value, op)
            if node.query is not None:
                reads(node.query, "R")
            return
        if hasattr(node, "__dataclass_fields__"):
            for field in fields(node.__class__):
                if field.name == "resolved":
                    continue
                reads(getattr(node, field.name), op)

    if isinstance(stmt, ast.Update):
        for assignment in stmt.assignments:
            col = assignment.column
            if col.resolved and not col.resolved.startswith("<"):
                result.add((col.resolved, col.name, "U"))
            reads(assignment.value, "R")
        reads(stmt.where, "R")
    elif isinstance(stmt, ast.Insert):
        for name in stmt.columns:
            result.add((stmt.table.name, name, "C"))
        reads(stmt.values, "R")
        reads(stmt.query, "R")
    else:
        reads(stmt, "R")
    return result
