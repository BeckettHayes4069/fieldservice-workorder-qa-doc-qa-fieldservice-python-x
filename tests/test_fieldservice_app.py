from fieldservice_app import WorkOrderQuestion, answer_question


class FakeClient:
    def embed(self, text):
        return [0.1, 0.2]

    def query(self, collection, embedding, top_k):
        return {"matches": [{"metadata": {"text": "Pump replaced; pressure test passed on WO-1042."}}]}

    def rerank(self, query, candidates, top_k):
        return {"results": [{"text": candidates[0]}]}


def test_question_returns_ranked_follow_up_note():
    result = answer_question(WorkOrderQuestion("WO-1042", "Did the repair pass?"), FakeClient())
    assert result == "Pump replaced; pressure test passed on WO-1042."
