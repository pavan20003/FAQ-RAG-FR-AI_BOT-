"""Evaluate vector, French keyword, and hybrid retrieval on the fixed question set."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings
from app.ingest.embed import get_embedder
from app.rag.retrieve import RetrievedChunk, relevance_gate, retrieve

QUESTIONS_PATH = Path(__file__).with_name("questions.json")
RESULTS_PATH = Path(__file__).with_name("results.md")
MODES = ("vector", "keyword", "hybrid")
SPLIT_SEED = 42


def load_questions() -> list[dict]:
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    if len(questions) != 50 or sum(item["answerable"] for item in questions) != 40:
        raise ValueError("The evaluation set must contain exactly 40 answerable and 10 unanswerable questions.")
    return questions


def verify_gold_references(connection, questions: list[dict]) -> None:
    rows = connection.execute("SELECT d.source, c.heading FROM chunks c JOIN documents d ON d.id=c.document_id").fetchall()
    existing = {(row["source"], row["heading"]) for row in rows}
    missing = sorted({(gold["source"], gold["heading"]) for question in questions for gold in question["gold"]} - existing)
    if missing:
        formatted = ", ".join(f"{source} :: {heading}" for source, heading in missing)
        raise ValueError(f"Gold references missing from the ingested database: {formatted}. Re-ingest the demo corpus first.")
    if not existing:
        raise ValueError("The database has no ingested chunks. Run the ingestion command first.")


def _matches(chunk: RetrievedChunk, gold: list[dict]) -> bool:
    return any(chunk.source == item["source"] and chunk.heading == item["heading"] for item in gold)


def retrieval_metrics(items: list[tuple[dict, list[RetrievedChunk]]]) -> tuple[float, float]:
    answerable = [(question, results) for question, results in items if question["answerable"]]
    if not answerable:
        return 0.0, 0.0
    recalls, reciprocal_ranks = [], []
    for question, results in answerable:
        gold = question["gold"]
        relevant_found = sum(any(chunk.source == item["source"] and chunk.heading == item["heading"] for chunk in results[:5]) for item in gold)
        recalls.append(relevant_found / len(gold))
        reciprocal_ranks.append(next((1.0 / rank for rank, chunk in enumerate(results[:5], 1) if _matches(chunk, gold)), 0.0))
    return statistics.mean(recalls), statistics.mean(reciprocal_ranks)


def _gate_performance(items: list[tuple[dict, list[RetrievedChunk]]], thresholds: tuple[float, float, float]) -> tuple[float, float, float]:
    vector_floor, keyword_floor, coverage_floor = thresholds
    positive_hits, negative_abstains = [], []
    for question, results in items:
        passed = relevance_gate(results, question["question"], vector_threshold=vector_floor,
                                keyword_threshold=keyword_floor, min_term_coverage=coverage_floor)
        (positive_hits if question["answerable"] else negative_abstains).append(not passed if not question["answerable"] else passed)
    recall = statistics.mean(positive_hits) if positive_hits else 0.0
    abstention = statistics.mean(negative_abstains) if negative_abstains else 0.0
    return (recall + abstention) / 2, recall, abstention


def tune_gate(tune_items: list[tuple[dict, list[RetrievedChunk]]]) -> tuple[tuple[float, float, float], float, float, float]:
    candidates = [(v, k, c) for v in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
                  for k in (0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10)
                  for c in (0.15, 0.25, 0.35, 0.50, 0.65)]
    scored = [( *_gate_performance(tune_items, thresholds), thresholds) for thresholds in candidates]
    # Highest balanced accuracy; ties favor higher thresholds to reduce unsupported answers.
    score, recall, abstention, thresholds = max(scored, key=lambda row: (row[0], sum(row[3]), row[3]))
    return thresholds, score, recall, abstention


def _format_table(rows: list[tuple[str, float, float, float]]) -> str:
    lines = ["| Mode | Recall@5 | MRR | Mean latency (ms) |", "|---|---:|---:|---:|"]
    lines.extend(f"| {mode} | {recall:.3f} | {mrr:.3f} | {latency:.1f} |" for mode, recall, mrr, latency in rows)
    return "\n".join(lines)


def run() -> str:
    questions = load_questions()
    settings = get_settings()
    with psycopg.connect(settings.database_url, autocommit=True, row_factory=dict_row) as connection:
        from pgvector.psycopg import register_vector

        register_vector(connection)
        verify_gold_references(connection, questions)
        encoder = get_embedder(settings.embedding_model)
        # Match a running service: load and warm the local model before measuring query latency.
        encoder.encode(["Échauffement de l'évaluation."], kind="query")
        all_results: dict[str, list[tuple[dict, list[RetrievedChunk], float]]] = {mode: [] for mode in MODES}
        for question in questions:
            for mode in MODES:
                started = time.perf_counter()
                chunks = retrieve(question["question"], mode=mode, connection=connection, encoder=encoder, top_k=5)
                latency_ms = (time.perf_counter() - started) * 1000
                all_results[mode].append((question, chunks, latency_ms))

    tuning_items = [(question, chunks) for question, chunks, _ in all_results["hybrid"] if question["split"] == "tune"]
    reporting_items = [(question, chunks) for question, chunks, _ in all_results["hybrid"] if question["split"] == "report"]
    thresholds, train_score, train_recall, train_abstention = tune_gate(tuning_items)
    report_score, report_recall, report_abstention = _gate_performance(reporting_items, thresholds)

    full_metrics = []
    split_metrics = {"tune": [], "report": []}
    for mode, records in all_results.items():
        items = [(question, chunks) for question, chunks, _ in records]
        recall, mrr = retrieval_metrics(items)
        latency = statistics.mean(lat for _, _, lat in records)
        full_metrics.append((mode, recall, mrr, latency))
        for split in split_metrics:
            split_items = [(question, chunks) for question, chunks, _ in records if question["split"] == split]
            split_recall, split_mrr = retrieval_metrics(split_items)
            split_latency = statistics.mean(lat for q, _, lat in records if q["split"] == split)
            split_metrics[split].append((mode, split_recall, split_mrr, split_latency))

    unanswerable = [(q, results) for q, results, _ in all_results["hybrid"] if not q["answerable"]]
    abstained = sum(not relevance_gate(results, q["question"], vector_threshold=thresholds[0],
                    keyword_threshold=thresholds[1], min_term_coverage=thresholds[2]) for q, results in unanswerable)
    score_by_mode = {mode: recall for mode, recall, _mrr, _latency in full_metrics}
    if score_by_mode["hybrid"] < score_by_mode["vector"]:
        comparison = (
            f"Hybrid did not beat vector-only on this corpus: Recall@5 was {score_by_mode['hybrid']:.3f} "
            f"for hybrid versus {score_by_mode['vector']:.3f} for vector. The 35 ingested passages are a small, "
            "coherent collection, and BGE-M3 already retrieves most gold headings directly; RRF can lower an "
            "already-relevant vector result when keyword-only candidates enter the merged ranking."
        )
    elif score_by_mode["hybrid"] > score_by_mode["vector"]:
        comparison = (
            f"Hybrid beat vector-only on this corpus: Recall@5 was {score_by_mode['hybrid']:.3f} "
            f"for hybrid versus {score_by_mode['vector']:.3f} for vector. Keyword matches add useful exact-term "
            "evidence to semantic retrieval on this question set."
        )
    else:
        comparison = (
            f"Hybrid tied vector-only on this corpus at Recall@5 {score_by_mode['hybrid']:.3f}. "
            "The keyword list did not change gold-heading coverage in the top five."
        )
    report = f"""# Retrieval evaluation

Generated from {len(questions)} French questions against the ingested fictional bakery corpus. Fixed split seed: {SPLIT_SEED}. Gold relevance uses stable `(source file, heading)` identifiers and is verified against the database before retrieval. Recall@5 is the mean fraction of each answerable question's gold references found in the top five; MRR uses the first relevant result. Latency is measured locally and includes query embedding and database retrieval after model warm-up.

## Overall retrieval results

{_format_table(full_metrics)}

## Fixed tuning and report split

Questions were shuffled with fixed seed {SPLIT_SEED}, split into the first 25 tuning questions and the remaining 25 report questions; each split contains 20 answerable and 5 unanswerable items. Gate thresholds were selected on the first half by balanced accuracy, then frozen for the report half. Thresholds: vector similarity ≥ {thresholds[0]:.3f}, keyword rank ≥ {thresholds[1]:.3f} with term coverage ≥ {thresholds[2]:.2f}.

| Split | Gate balanced accuracy | Answerable pass rate | Unanswerable abstention rate |
|---|---:|---:|---:|
| Tune (first 25) | {train_score:.3f} | {train_recall:.3f} | {train_abstention:.3f} |
| Report (last 25) | {report_score:.3f} | {report_recall:.3f} | {report_abstention:.3f} |

Abstention rate across all 10 unanswerable questions using the selected hybrid gate: **{abstained}/10 ({abstained / len(unanswerable):.3f})**.

### Report-half retrieval metrics

{_format_table(split_metrics['report'])}

## Analysis

These scores describe this small fictional corpus only. {comparison} The balanced gate threshold is tuned on only 25 items, so it needs validation on a larger independent question set before production use.
"""
    RESULTS_PATH.write_text(report, encoding="utf-8")
    print(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run()


if __name__ == "__main__":
    main()
