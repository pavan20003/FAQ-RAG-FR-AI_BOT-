from eval.run_eval import load_questions, retrieval_metrics, verify_gold_references
from app.rag.retrieve import RetrievedChunk


def test_question_set_has_40_answerable_and_10_unanswerable_with_balanced_fixed_split():
    questions = load_questions()
    assert len(questions) == 50
    assert sum(question["answerable"] for question in questions) == 40
    assert sum(question["answerable"] for question in questions[:25]) == 20
    assert sum(not question["answerable"] for question in questions[:25]) == 5
    assert sum(question["answerable"] for question in questions[25:]) == 20
    assert sum(not question["answerable"] for question in questions[25:]) == 5


def test_retrieval_metrics_use_source_and_heading_stable_labels():
    question = {"answerable": True, "gold": [{"source": "hours.md", "heading": "Horaires"}]}
    relevant = RetrievedChunk(1, "hours", "Horaires", "hours.md", None)
    distractor = RetrievedChunk(2, "prices", "Tarifs", "prices.md", None)
    assert retrieval_metrics([(question, [distractor, relevant])]) == (1.0, 0.5)


def test_gold_reference_verifier_rejects_missing_heading():
    class Result:
        def fetchall(self):
            return [{"source": "hours.md", "heading": "Horaires"}]

    class Connection:
        def execute(self, _sql):
            return Result()

    try:
        verify_gold_references(Connection(), [{"gold": [{"source": "other.md", "heading": "absent"}]}])
    except ValueError as error:
        assert "other.md :: absent" in str(error)
    else:
        raise AssertionError("Expected a missing gold reference to fail verification")
