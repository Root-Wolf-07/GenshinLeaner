"""Automated tests for Document ingestion, chunking, and deletion.
"""

import io
from fastapi.testclient import TestClient


def test_upload_valid_document(client: TestClient):
    file_content = (
        "# Dynamic Programming Fundamentals\n\n"
        "Dynamic programming (DP) solves complex problems by breaking them down into overlapping subproblems.\n"
        "The two essential properties required are Optimal Substructure and Overlapping Subproblems.\n\n"
        "## Memoization vs Tabulation\n"
        "Memoization represents the top-down approach with caching.\n"
        "Tabulation represents the bottom-up approach iteratively filling a table.\n"
    )
    file_bytes = io.BytesIO(file_content.encode("utf-8"))

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("algorithms_lecture.md", file_bytes, "text/markdown")},
        data={"title": "Algorithms DP Lecture", "subject": "Computer Science"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "algorithms_lecture.md"
    assert data["status"] in ("ready", "uploaded", "processing")
    assert data["title"] == "Algorithms DP Lecture"
    assert data["chunk_count"] > 0
    doc_id = data["id"]

    # Verify document retrieval
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id

    # Verify chunks endpoint
    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) > 0
    assert "Optimal Substructure" in chunks[0]["content"]

    # Clean up via DELETE
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 204


def test_reject_unsupported_file_extension(client: TestClient):
    file_bytes = io.BytesIO(b"malicious executable payload")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("exploit.exe", file_bytes, "application/octet-stream")},
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Unsupported file type" in data["error"]["message"]
