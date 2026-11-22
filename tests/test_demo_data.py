import unittest

from scripts.make_demo_data import DATA_DIR, FACTS, PAGES, PDFS, generate


class DemoDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        generate()

    def test_generated_corpus_has_expected_file_counts(self) -> None:
        self.assertEqual(len(list(DATA_DIR.rglob("*.md"))), len(PAGES))
        self.assertEqual(len(list(DATA_DIR.rglob("*.pdf"))), len(PDFS))

    def test_pdfs_are_valid_files_and_fact_ledger_lists_sources(self) -> None:
        for path in DATA_DIR.rglob("*.pdf"):
            self.assertTrue(path.read_bytes().startswith(b"%PDF-"), path)
        ledger = (DATA_DIR.parent / "FACTS.md").read_text(encoding="utf-8")
        self.assertIn("Deliberate superseded versions", ledger)
        for fact in FACTS:
            self.assertIn(f"`{fact.key}`", ledger)


if __name__ == "__main__":
    unittest.main()
