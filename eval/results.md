# Retrieval evaluation

Generated from 50 French questions against the ingested fictional bakery corpus. Fixed split seed: 42. Gold relevance uses stable `(source file, heading)` identifiers and is verified against the database before retrieval. Recall@5 is the mean fraction of each answerable question's gold references found in the top five; MRR uses the first relevant result. Latency is measured locally and includes query embedding and database retrieval after model warm-up.

## Overall retrieval results

| Mode | Recall@5 | MRR | Mean latency (ms) |
|---|---:|---:|---:|
| vector | 0.975 | 0.830 | 45.7 |
| keyword | 0.887 | 0.699 | 7.3 |
| hybrid | 0.938 | 0.756 | 48.8 |

## Fixed tuning and report split

Questions were shuffled with fixed seed 42, split into the first 25 tuning questions and the remaining 25 report questions; each split contains 20 answerable and 5 unanswerable items. Gate thresholds were selected on the first half by balanced accuracy, then frozen for the report half. Thresholds: vector similarity ≥ 0.500, keyword rank ≥ 0.100 with term coverage ≥ 0.65.

| Split | Gate balanced accuracy | Answerable pass rate | Unanswerable abstention rate |
|---|---:|---:|---:|
| Tune (first 25) | 1.000 | 1.000 | 1.000 |
| Report (last 25) | 0.875 | 0.950 | 0.800 |

Abstention rate across all 10 unanswerable questions using the selected hybrid gate: **9/10 (0.900)**.

### Report-half retrieval metrics

| Mode | Recall@5 | MRR | Mean latency (ms) |
|---|---:|---:|---:|
| vector | 1.000 | 0.818 | 34.9 |
| keyword | 0.775 | 0.568 | 5.6 |
| hybrid | 0.900 | 0.662 | 37.4 |

## Analysis

These scores describe this small fictional corpus only. Hybrid did not beat vector-only on this corpus: Recall@5 was 0.938 for hybrid versus 0.975 for vector. The 35 ingested passages are a small, coherent collection, and BGE-M3 already retrieves most gold headings directly; RRF can lower an already-relevant vector result when keyword-only candidates enter the merged ranking. The balanced gate threshold is tuned on only 25 items, so it needs validation on a larger independent question set before production use.
