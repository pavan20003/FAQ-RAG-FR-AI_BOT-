import unittest
import tempfile
from pathlib import Path

from scripts.make_demo_data import FACTS, PAGES, PDFS, generate


class DemoDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.data_dir = Path(cls.temporary_directory.name) / "data" / "demo_site"
        generate(Path(cls.temporary_directory.name))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_generated_corpus_has_expected_file_counts(self) -> None:
        self.assertEqual(len(list(self.data_dir.rglob("*.md"))), len(PAGES))
        self.assertEqual(len(list(self.data_dir.rglob("*.pdf"))), len(PDFS))

    def test_pdfs_are_valid_files_and_fact_ledger_lists_sources(self) -> None:
        for path in self.data_dir.rglob("*.pdf"):
            self.assertTrue(path.read_bytes().startswith(b"%PDF-"), path)
        ledger = (self.data_dir.parent / "FACTS.md").read_text(encoding="utf-8")
        self.assertIn("Deliberate superseded versions", ledger)
        for fact in FACTS:
            self.assertIn(f"`{fact.key}`", ledger)


if __name__ == "__main__":
    unittest.main()
