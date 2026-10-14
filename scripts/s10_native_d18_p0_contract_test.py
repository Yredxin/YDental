"""SIMULATED offline positive and negative tests only."""

import ast
import pathlib
import unittest
from unittest.mock import Mock

from s10_native_d18_p0_contract import Delta, classify_delta, classify_file, run_fixture


class ContractTests(unittest.TestCase):
    def test_static_no_orm_or_pg_imports(self):
        source = pathlib.Path(__file__).with_name("s10_native_d18_p0_contract.py").read_text()
        imports = [alias.name for node in ast.walk(ast.parse(source))
                   if isinstance(node, ast.Import) for alias in node.names]
        imports += [node.module for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.ImportFrom)]
        self.assertEqual(imports, ["dataclasses"])
        self.assertNotIn("odoo", source)
        self.assertNotIn("psycopg2", source)

    def test_template_851_is_not_a_new_message(self):
        base = frozenset(range(1, 852))
        d = Delta(base, base | {900}, frozenset(), frozenset(), frozenset({1}), frozenset({1, 2}))
        self.assertEqual(classify_delta(d, frozenset({900}))["new_internal_messages"], 1)
        with self.assertRaises(ValueError):
            classify_delta(d, frozenset())

    def test_queued_mail_is_separate_and_rejected(self):
        d = Delta(frozenset(), frozenset(), frozenset(), frozenset({1}), frozenset(), frozenset())
        with self.assertRaises(ValueError):
            classify_delta(d, frozenset())

    def test_rollback_does_not_rewrite_baseline(self):
        base = frozenset(range(1, 852))
        d = Delta(base, base, frozenset(), frozenset(), frozenset(), frozenset())
        self.assertEqual(classify_delta(d, frozenset())["new_internal_messages"], 0)

    def test_file_source_and_orphan_are_distinct(self):
        self.assertEqual(classify_file(mime="image/svg+xml", sha256="abc", size=305,
                        expected_svg_sha={"abc"}, checklist_for_known_file=False,
                        attachment_refs=0), "AVATAR_CANDIDATE_REVIEW_REFERENCE")
        self.assertEqual(classify_file(mime="application/octet-stream", sha256="x", size=0,
                        expected_svg_sha=set(), checklist_for_known_file=True,
                        attachment_refs=0), "GC_CHECKLIST_FOR_KNOWN_FILE")
        self.assertEqual(classify_file(mime="image/svg+xml", sha256="unknown", size=305,
                        expected_svg_sha={"abc"}, checklist_for_known_file=False,
                        attachment_refs=0), "UNKNOWN_STOP")

    def test_execution_closed(self):
        with self.assertRaisesRegex(RuntimeError, "NOT_AUTHORIZED"):
            run_fixture()

    def test_mock_cursor_snapshot_contract(self):
        # SIMULATED: a future ORM cursor supplies ID sets, without opening one here.
        fake_cursor = Mock()
        fake_cursor.snapshot.return_value = Delta(
            frozenset(range(1, 852)), frozenset(range(1, 853)),
            frozenset(), frozenset(), frozenset({1}), frozenset({1}))
        self.assertEqual(classify_delta(fake_cursor.snapshot(), frozenset({852}))
                         ["new_internal_messages"], 1)
        fake_cursor.snapshot.assert_called_once_with()

    def test_locked_source_ast_edges(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        sources = {
            "warehouse": root.parent / "addons/stock/models/stock_warehouse.py",
            "product_settings": root.parent / "addons/product/models/res_config_settings.py",
            "native_guard": root / "ydental_intake/models/native.py",
        }
        calls = {}
        for name, path in sources.items():
            tree = ast.parse(path.read_text())
            calls[name] = {node.func.attr for node in ast.walk(tree)
                           if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertIn("_check_multiwarehouse_group", calls["warehouse"])
        self.assertIn("execute", calls["warehouse"])
        self.assertIn("action_archive", calls["product_settings"])
        self.assertIn("_ydental_guard", calls["native_guard"])


if __name__ == "__main__":
    unittest.main()
