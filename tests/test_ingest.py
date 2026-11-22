from __future__ import annotations

import contextlib
import tempfile
import unittest
from pathlib import Path

from app.ingest.chunker import approximate_tokens, chunk_text
from app.ingest.loaders import load_document, normalize_text
from app.ingest.pipeline import ingest_directory


class _Result:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class _MemoryConnection:
    """Small in-memory SQL fixture for testing pipeline transaction behavior offline."""

    def __init__(self):
        self.documents = {}
        self.chunks = []
        self.next_id = 1

    @contextlib.contextmanager
    def transaction(self):
        before = (dict(self.documents), list(self.chunks), self.next_id)
        try:
            yield
        except Exception:
            self.documents, self.chunks, self.next_id = before
            raise

    def execute(self, query, params=()):
        if query.startswith("SELECT source, id, content_hash"):
            return _Result({"source": source, **document} for source, document in self.documents.items())
        if query.startswith("DELETE FROM documents"):
            source = params[0]
            document = self.documents.pop(source, None)
            if document:
                self.chunks = [chunk for chunk in self.chunks if chunk["document_id"] != document["id"]]
            return _Result()
        if query.startswith("INSERT INTO documents"):
            source, title, doc_type, content_hash = params
            document = self.documents.get(source)
            if document is None:
                document = {"id": self.next_id}
                self.next_id += 1
            document.update(title=title, doc_type=doc_type, content_hash=content_hash)
            self.documents[source] = document
            return _Result([{"id": document["id"]}])
        if query.startswith("DELETE FROM chunks"):
            document_id = params[0]
            self.chunks = [chunk for chunk in self.chunks if chunk["document_id"] != document_id]
            return _Result()
        if query.startswith("INSERT INTO chunks"):
            document_id, chunk_index, heading, text, embedding, page = params
            self.chunks.append({
                "document_id": document_id,
                "chunk_index": chunk_index,
                "heading": heading,
                "text": text,
                "embedding": embedding,
                "page": page,
            })
            return _Result()
        raise AssertionError(f"Unexpected SQL: {query}")


class _FakeEncoder:
    def encode(self, texts, *, kind="passage", batch_size=32):
        return [[float(index), 1.0] for index, _ in enumerate(texts)]


class LoaderTests(unittest.TestCase):
    def test_html_loader_removes_navigation_footer_and_script(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text(
                "<html><head><title>Épicerie</title></head><body><nav>Menu privé</nav>"
                "<main><h1>Épicerie</h1><p>Du pain frais.</p></main>"
                "<script>secret()</script><footer>Mentions</footer></body></html>",
                encoding="utf-8",
            )
            document = load_document(path)

        self.assertEqual(document.title, "Épicerie")
        self.assertIn("Du pain frais.", document.pages[0].text)
        self.assertNotIn("Menu privé", document.pages[0].text)
        self.assertNotIn("secret", document.pages[0].text)
        self.assertNotIn("Mentions", document.pages[0].text)

    def test_markdown_loader_keeps_french_accents_and_normalizes_unicode(self):
        normalized = normalize_text("Cre\u0300me\u00a0frai\u0302che\r\n\r\n\r\n")
        self.assertEqual(normalized, "Crème fraîche")

    def test_pdf_loader_keeps_page_numbers(self):
        path = Path(__file__).resolve().parents[1] / "data" / "demo_site" / "tarifs.pdf"
        document = load_document(path, source="tarifs.pdf")

        self.assertEqual(document.doc_type, "pdf")
        self.assertTrue(document.pages)
        self.assertEqual(document.pages[0].page, 1)
        self.assertIn("1,30", " ".join(page.text for page in document.pages))


class ChunkerTests(unittest.TestCase):
    def test_heading_path_and_accents_are_kept(self):
        chunks = chunk_text(
            "# Boissons\nTexte d'introduction.\n## Thé glacé\nLe thé glacé à la pêche coûte 2 €.",
            title="Menu du café",
            target_tokens=40,
            max_tokens=50,
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[1].heading, "Boissons > Thé glacé")
        self.assertIn("thé glacé à la pêche", chunks[1].text)
        self.assertIn("Titre : Menu du café", chunks[1].text)

    def test_chunks_respect_maximum_and_overlap(self):
        sentence = "Chaque matin notre équipe prépare du pain frais avec soin pour les habitants du quartier."
        text = "# Pain\n" + " ".join([sentence] * 16)
        chunks = chunk_text(text, title="Boulangerie", target_tokens=48, max_tokens=60)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(approximate_tokens(chunk.text) <= 60 for chunk in chunks))
        self.assertTrue(set(chunks[0].text.split()[-5:]) & set(chunks[1].text.split()))


class PipelineTests(unittest.TestCase):
    def test_ingest_is_idempotent_and_changed_files_are_rechunked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "faq.md"
            source.write_text("# Horaires\nOuvert chaque matin.", encoding="utf-8")
            connection = _MemoryConnection()
            encoder = _FakeEncoder()

            first = ingest_directory(root, connection=connection, encoder=encoder)
            second = ingest_directory(root, connection=connection, encoder=encoder)
            source.write_text("# Horaires\nOuvert chaque matin et chaque soir.", encoding="utf-8")
            third = ingest_directory(root, connection=connection, encoder=encoder)

        self.assertEqual(first.added, 1)
        self.assertEqual(second.skipped, 1)
        self.assertEqual(len(connection.documents), 1)
        self.assertEqual(third.updated, 1)
        self.assertEqual(len(connection.chunks), third.chunks)
        self.assertIn("chaque soir", connection.chunks[0]["text"])

    def test_deleted_file_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "page.txt").write_text("Une page utile.", encoding="utf-8")
            connection = _MemoryConnection()
            encoder = _FakeEncoder()
            ingest_directory(root, connection=connection, encoder=encoder)
            (root / "page.txt").unlink()
            result = ingest_directory(root, connection=connection, encoder=encoder)

        self.assertEqual(result.deleted, 1)
        self.assertEqual(connection.documents, {})
        self.assertEqual(connection.chunks, [])


if __name__ == "__main__":
    unittest.main()
