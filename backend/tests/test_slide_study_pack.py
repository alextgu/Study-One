"""Tests for slide upload and slide quiz regeneration endpoints."""

from pathlib import Path
import re
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def isolate_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return tmp_path


class FakeSupabase:
    """Tiny fake supabase client for deterministic insert responses."""

    def __init__(self):
        self._table = None
        self.inserted = []
        self._ids = {
            "quiz": "quiz-id-123",
            "flashcards": "flash-id-123",
        }

    def table(self, name):
        self._table = name
        return self

    def insert(self, payload):
        self.inserted.append((self._table, payload))
        return self

    def execute(self):
        record_id = self._ids.get(self._table, "generic-id")
        return type("Result", (), {"data": [{"id": record_id}]})()


def _sample_payload():
    summary = [
        "HTTP is a stateless application-layer protocol used for client-server communication on the web.",
        "A request contains a method, path, headers, and optional body; a response contains a status code, headers, and body.",
        "GET is used to retrieve resources, while POST is commonly used to submit data for server-side processing.",
        "Status codes are grouped by class (2xx success, 4xx client errors, 5xx server errors) to communicate outcome.",
        "Headers such as Content-Type and Cache-Control control payload format and caching behavior between client and server.",
    ]
    quiz = [
        {
            "question": "Which HTTP method is most appropriate for retrieving an existing resource without changing server state?",
            "options": ["GET", "POST", "DELETE", "PATCH"],
            "answer": "GET",
            "topic": "HTTP Methods",
            "correctionExplanation": "GET is designed for safe, read-only retrieval. POST, DELETE, and PATCH can change server state.",
        },
        {
            "question": "A response with status code 404 means:",
            "options": [
                "The request succeeded and returned content",
                "The requested resource was not found",
                "The server had an internal error",
                "The client must authenticate first",
            ],
            "answer": "The requested resource was not found",
            "topic": "Status Codes",
            "correctionExplanation": "404 is a client error indicating the target resource does not exist at the requested URL.",
        },
        {
            "question": "Which header tells the client the media type of the response body?",
            "options": ["Authorization", "Content-Type", "Host", "Accept-Language"],
            "answer": "Content-Type",
            "topic": "HTTP Headers",
            "correctionExplanation": "Content-Type declares how the response body should be interpreted, such as application/json.",
        },
        {
            "question": "Why is HTTP often described as stateless?",
            "options": [
                "It cannot send response bodies",
                "Each request is independent and does not require server memory of prior requests",
                "It only works over encrypted channels",
                "It supports only one method",
            ],
            "answer": "Each request is independent and does not require server memory of prior requests",
            "topic": "Protocol Fundamentals",
            "correctionExplanation": "In HTTP, each request contains all the context needed; the protocol itself does not require session memory.",
        },
        {
            "question": "Which status code class generally represents successful requests?",
            "options": ["1xx", "2xx", "4xx", "5xx"],
            "answer": "2xx",
            "topic": "Status Code Classes",
            "correctionExplanation": "2xx codes indicate success, such as 200 OK and 201 Created.",
        },
    ]
    flashcards = [
        {
            "question": "What does HTTP stand for?",
            "answer": "Hypertext Transfer Protocol.",
        },
        {
            "question": "What does a 200 status code indicate?",
            "answer": "The request was successful.",
        },
        {
            "question": "What is the purpose of the Content-Type header?",
            "answer": "It specifies the media type of the HTTP message body.",
        },
        {
            "question": "Name one common use of POST.",
            "answer": "Submitting data to create or process a resource.",
        },
        {
            "question": "Why are cookies often used with HTTP?",
            "answer": "To maintain session-related state across otherwise stateless requests.",
        },
        {
            "question": "What does a 500 status code usually mean?",
            "answer": "The server encountered an internal error while processing the request.",
        },
        {
            "question": "What is a URL path used for in an HTTP request?",
            "answer": "To identify the resource being requested on the server.",
        },
        {
            "question": "What is the difference between 4xx and 5xx errors?",
            "answer": "4xx indicates client-side issues; 5xx indicates server-side failures.",
        },
        {
            "question": "What does statelessness imply for each HTTP request?",
            "answer": "Each request should include all information needed to process it.",
        },
        {
            "question": "Why might Cache-Control be used?",
            "answer": "To control how and for how long responses can be cached.",
        },
    ]
    return summary, quiz, flashcards


def _sample_chunking_text() -> str:
    """Realistic long slide text that should trigger chunking branch."""
    paragraphs = [
        (
            "HTTP is a stateless protocol where each request should contain enough context "
            "for the server to process it independently."
        ),
        (
            "A typical request includes method, path, headers, and optional body. "
            "A typical response includes status code, headers, and a response body."
        ),
        (
            "GET is generally safe and idempotent for reads, while POST is used for creating "
            "or submitting data that may change server state."
        ),
        (
            "Status codes are grouped by class: 2xx for success, 4xx for client-side issues, "
            "and 5xx for server-side failures."
        ),
        (
            "Headers such as Content-Type, Authorization, and Cache-Control influence "
            "payload format, access control, and caching behavior."
        ),
        (
            "Caching can improve performance, but stale caches can lead to unexpected behavior "
            "if cache directives are misconfigured."
        ),
    ]
    # Repeat content to exceed chunking threshold in tests.
    return "\n\n".join(paragraphs * 8)


def _marker_text(count: int = 220) -> str:
    """Deterministic token stream for chunk boundary/coverage testing."""
    return " ".join(f"T{i:04d}" for i in range(1, count + 1))


def _assert_valid_slide_pack_response(data: dict):
    assert isinstance(data["file_name"], str) and data["file_name"]
    assert isinstance(data["stored_path"], str) and data["stored_path"]
    assert isinstance(data["quiz_set_id"], str) and data["quiz_set_id"]
    assert isinstance(data["flashcard_set_id"], str) and data["flashcard_set_id"]
    assert isinstance(data["extracted_text"], str) and data["extracted_text"].strip()
    assert isinstance(data["summary"], list) and len(data["summary"]) >= 1
    assert isinstance(data["quiz"], list) and 5 <= len(data["quiz"]) <= 10
    assert isinstance(data["flashcards"], list) and len(data["flashcards"]) >= 1
    for q in data["quiz"]:
        assert isinstance(q["question"], str) and q["question"].strip()
        assert isinstance(q["options"], list) and len(q["options"]) == 4
        assert q["answer"] in q["options"]
        assert isinstance(q["topic"], str) and q["topic"].strip()
    for fc in data["flashcards"]:
        assert isinstance(fc["question"], str) and fc["question"].strip()
        assert isinstance(fc["answer"], str) and fc["answer"].strip()


def test_slides_study_pack_generates_valid_response_and_stores_file(client):
    summary, quiz, flashcards = _sample_payload()
    body = b"%PDF-1.4 fake slide bytes"
    fake_db = FakeSupabase()
    with patch("main.extract_pdf", return_value="x" * 200), patch(
        "main.generate_study_pack_slides",
        new=AsyncMock(
            return_value=(
                summary,
                [main.QuizQuestion(**q) for q in quiz],
                [main.Flashcard(**f) for f in flashcards],
            )
        ),
    ) as mock_generate, patch("main.get_supabase", return_value=fake_db):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={"file": ("lecture.pdf", body, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    _assert_valid_slide_pack_response(data)
    assert data["file_name"] == "lecture.pdf"
    assert data["extracted_text"] == "x" * 200
    assert mock_generate.await_count == 1
    stored_path = Path(data["stored_path"])
    assert stored_path.exists()
    assert stored_path.read_bytes() == body
    # quiz + flashcards persisted
    assert [name for name, _ in fake_db.inserted] == ["quiz", "flashcards"]


def test_slides_study_pack_returns_exact_sample_payload_shapes(client):
    summary, quiz, flashcards = _sample_payload()
    fake_db = FakeSupabase()
    with patch("main.extract_pdf", return_value="x" * 200), patch(
        "main.generate_study_pack_slides",
        new=AsyncMock(
            return_value=(
                summary,
                [main.QuizQuestion(**q) for q in quiz],
                [main.Flashcard(**f) for f in flashcards],
            )
        ),
    ), patch("main.get_supabase", return_value=fake_db):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={"file": ("lecture.pdf", b"pdf", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == summary
    assert len(data["quiz"]) == len(quiz)
    assert len(data["flashcards"]) == len(flashcards)
    # Spot-check first/last items to ensure mapping is faithful.
    assert data["quiz"][0]["question"] == quiz[0]["question"]
    assert data["quiz"][-1]["answer"] == quiz[-1]["answer"]
    assert data["flashcards"][0] == flashcards[0]
    assert data["flashcards"][-1] == flashcards[-1]


def test_slides_stored_path_is_inside_upload_dir_and_well_formed(client, isolate_upload_dir):
    summary, quiz, flashcards = _sample_payload()
    fake_db = FakeSupabase()
    with patch("main.extract_pdf", return_value="x" * 200), patch(
        "main.generate_study_pack_slides",
        new=AsyncMock(
            return_value=(
                summary,
                [main.QuizQuestion(**q) for q in quiz],
                [main.Flashcard(**f) for f in flashcards],
            )
        ),
    ), patch("main.get_supabase", return_value=fake_db):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={"file": ("lecture name!.pdf", b"pdf", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    stored_path = Path(data["stored_path"]).resolve()
    expected_dir = Path(isolate_upload_dir).resolve()

    # Path is physically inside the configured upload directory.
    assert stored_path.parent == expected_dir
    # Filename is sanitized and timestamped: <safe_name>_YYYYMMDD_HHMMSS.pdf
    assert re.match(r"^lecture_name_\d{8}_\d{6}\.pdf$", stored_path.name)
    # The path in response points to a real file.
    assert stored_path.exists()


def test_slides_study_pack_supports_pptx(client):
    summary, quiz, flashcards = _sample_payload()
    fake_db = FakeSupabase()
    with patch("main.extract_pptx", return_value="pptx extracted text"), patch(
        "main.generate_study_pack_slides",
        new=AsyncMock(
            return_value=(
                summary,
                [main.QuizQuestion(**q) for q in quiz],
                [main.Flashcard(**f) for f in flashcards],
            )
        ),
    ), patch("main.get_supabase", return_value=fake_db):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={
                "file": (
                    "lecture.pptx",
                    b"pptx-bytes",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            },
        )
    assert response.status_code == 200
    _assert_valid_slide_pack_response(response.json())


def test_slides_study_pack_rejects_unsupported_file(client):
    response = client.post(
        "/api/v1/slides/study-pack",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_slides_study_pack_handles_extraction_failure(client):
    with patch("main.extract_pdf", side_effect=RuntimeError("parse failed")):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={"file": ("broken.pdf", b"%PDF-1.4 broken", "application/pdf")},
        )
    assert response.status_code == 400
    assert "Could not extract text" in response.json()["detail"]


def test_slides_study_pack_handles_no_text(client):
    with patch("main.extract_pdf", return_value="   "):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={"file": ("image_only.pdf", b"%PDF-1.4 scan", "application/pdf")},
        )
    assert response.status_code == 422
    assert "No text found" in response.json()["detail"]


def test_slides_study_pack_rejects_too_large_file(client, monkeypatch, isolate_upload_dir):
    monkeypatch.setattr(main, "MAX_UPLOAD_SIZE_BYTES", 10)
    response = client.post(
        "/api/v1/slides/study-pack",
        files={"file": ("big.pdf", b"x" * 64, "application/pdf")},
    )
    assert response.status_code == 413
    # Temporary file should be removed on over-limit write
    assert list(isolate_upload_dir.iterdir()) == []


def test_slides_study_pack_persist_quiz_fails(client):
    summary, quiz, flashcards = _sample_payload()

    class BrokenSupabase(FakeSupabase):
        def execute(self):
            if self._table == "quiz":
                raise RuntimeError("db down")
            return super().execute()

    with patch("main.extract_pdf", return_value="x" * 200), patch(
        "main.generate_study_pack_slides",
        new=AsyncMock(
            return_value=(
                summary,
                [main.QuizQuestion(**q) for q in quiz],
                [main.Flashcard(**f) for f in flashcards],
            )
        ),
    ), patch("main.get_supabase", return_value=BrokenSupabase()):
        response = client.post(
            "/api/v1/slides/study-pack",
            files={"file": ("lecture.pdf", b"pdf", "application/pdf")},
        )

    assert response.status_code == 500
    assert "Failed to store generated quiz" in response.json()["detail"]


def test_regenerate_slide_quiz_endpoint_returns_valid_quiz_set(client):
    quiz = [
        {
            "question": f"Question {i + 1}",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
            "topic": "Web",
            "correctionExplanation": "A is correct.",
        }
        for i in range(5)
    ]
    payload = {"quiz": quiz}
    with patch.object(
        main.gemini_service,
        "call_gemini",
        new=AsyncMock(return_value=str(payload).replace("'", '"')),
    ), patch("main.get_supabase", return_value=FakeSupabase()):
        response = client.post(
            "/api/v1/slides/quiz/regenerate",
            json={"text": "x" * 100},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["quiz_set_id"] == "quiz-id-123"
    assert isinstance(data["quiz"], list)
    assert len(data["quiz"]) == 5
    for q in data["quiz"]:
        assert q["answer"] in q["options"]


def test_regenerate_slide_quiz_rejects_short_text(client):
    response = client.post(
        "/api/v1/slides/quiz/regenerate",
        json={"text": "short"},
    )
    assert response.status_code == 422


def test_regenerate_slide_quiz_invalid_ai_json(client):
    with patch.object(
        main.gemini_service,
        "call_gemini",
        new=AsyncMock(return_value="definitely not json"),
    ):
        response = client.post(
            "/api/v1/slides/quiz/regenerate",
            json={"text": "x" * 100},
        )
    assert response.status_code == 500
    assert "Failed to parse AI response as JSON" in response.json()["detail"]


def test_chunk_text_returns_empty_for_blank_input():
    assert main.chunk_text("   \n\t  ") == []


def test_chunk_text_creates_overlapping_chunks():
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = main.chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) == 3
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "ijklmnopqr"
    assert chunks[2] == "qrstuvwxyz"
    # overlap of 2 chars between neighboring chunks
    assert chunks[0][-2:] == chunks[1][:2]
    assert chunks[1][-2:] == chunks[2][:2]


@pytest.mark.asyncio
async def test_generate_study_pack_slides_uses_chunking_branch_success(monkeypatch):
    summary, quiz, flashcards = _sample_payload()
    quiz_models = [main.QuizQuestion(**q) for q in quiz]
    flashcard_models = [main.Flashcard(**f) for f in flashcards]

    monkeypatch.setattr(main, "CHUNKING_THRESHOLD_CHARS", 20)
    monkeypatch.setattr(main, "chunk_text", lambda _text: ["chunk-1", "chunk-2"])
    monkeypatch.setattr(main, "build_merge_outline_prompt", lambda _s, _f: "merge-prompt")
    monkeypatch.setattr(
        main,
        "summarize_chunk",
        AsyncMock(side_effect=[(["s1"], ["f1"]), (["s2"], ["f2"])]),
    )
    monkeypatch.setattr(
        main.gemini_service,
        "call_gemini",
        AsyncMock(return_value='{"outline":["o1","o2"],"summary":["sum1","sum2"]}'),
    )
    monkeypatch.setattr(
        main,
        "get_study_pack_responses",
        AsyncMock(return_value=("quiz-raw", "flashcards-raw")),
    )
    monkeypatch.setattr(main, "parse_and_validate_quiz", lambda _raw: quiz_models)
    monkeypatch.setattr(main, "parse_and_validate_flashcards", lambda _raw: flashcard_models)

    returned_summary, returned_quiz, returned_flashcards = await main.generate_study_pack_slides(
        "x" * 200
    )

    assert returned_summary == ["sum1", "sum2"]
    assert returned_quiz == quiz_models
    assert returned_flashcards == flashcard_models


@pytest.mark.asyncio
async def test_generate_study_pack_slides_chunking_fails_when_merge_invalid_json(monkeypatch):
    monkeypatch.setattr(main, "CHUNKING_THRESHOLD_CHARS", 20)
    monkeypatch.setattr(main, "chunk_text", lambda _text: ["chunk-1"])
    monkeypatch.setattr(main, "build_merge_outline_prompt", lambda _s, _f: "merge-prompt")
    monkeypatch.setattr(main, "summarize_chunk", AsyncMock(return_value=(["s1"], ["f1"])))
    monkeypatch.setattr(main.gemini_service, "call_gemini", AsyncMock(return_value="not-json"))

    with pytest.raises(main.HTTPException) as exc_info:
        await main.generate_study_pack_slides("x" * 200)

    assert exc_info.value.status_code == 500
    assert "Failed to parse AI response as JSON" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_generate_study_pack_slides_chunking_with_sample_payload(monkeypatch):
    _, quiz, flashcards = _sample_payload()

    monkeypatch.setattr(main, "CHUNKING_THRESHOLD_CHARS", 20)
    monkeypatch.setattr(main, "chunk_text", lambda _text: ["chunk-1", "chunk-2"])
    monkeypatch.setattr(main, "build_merge_outline_prompt", lambda _s, _f: "merge-prompt")
    monkeypatch.setattr(
        main,
        "summarize_chunk",
        AsyncMock(side_effect=[(["s1"], ["f1"]), (["s2"], ["f2"])]),
    )
    monkeypatch.setattr(
        main.gemini_service,
        "call_gemini",
        AsyncMock(return_value='{"outline":["o1","o2"],"summary":["sum1","sum2"]}'),
    )
    monkeypatch.setattr(
        main,
        "get_study_pack_responses",
        AsyncMock(
            return_value=(
                '{"quiz": ' + str(quiz).replace("'", '"') + "}",
                '{"flashcards": ' + str(flashcards).replace("'", '"') + "}",
            )
        ),
    )

    returned_summary, returned_quiz, returned_flashcards = await main.generate_study_pack_slides(
        "x" * 200
    )

    assert returned_summary == ["sum1", "sum2"]
    assert len(returned_quiz) == len(quiz)
    assert len(returned_flashcards) == len(flashcards)
    assert returned_quiz[0].answer in returned_quiz[0].options
    assert returned_quiz[0].topic == quiz[0]["topic"]
    assert returned_flashcards[0].question == flashcards[0]["question"]


@pytest.mark.asyncio
async def test_generate_study_pack_slides_short_text_with_sample_payload(monkeypatch):
    summary, quiz, flashcards = _sample_payload()
    monkeypatch.setattr(main, "CHUNKING_THRESHOLD_CHARS", 10_000)
    monkeypatch.setattr(
        main.gemini_service,
        "call_gemini",
        AsyncMock(return_value='{"summary": ' + str(summary).replace("'", '"') + "}"),
    )
    monkeypatch.setattr(
        main,
        "get_study_pack_responses",
        AsyncMock(
            return_value=(
                '{"quiz": ' + str(quiz).replace("'", '"') + "}",
                '{"flashcards": ' + str(flashcards).replace("'", '"') + "}",
            )
        ),
    )

    returned_summary, returned_quiz, returned_flashcards = await main.generate_study_pack_slides(
        "short but valid slide text"
    )

    assert returned_summary == summary
    assert [q.model_dump() for q in returned_quiz] == [main.QuizQuestion(**q).model_dump() for q in quiz]
    assert [f.model_dump() for f in returned_flashcards] == [
        main.Flashcard(**f).model_dump() for f in flashcards
    ]


@pytest.mark.asyncio
async def test_generate_study_pack_slides_chunking_branch_with_sample_payload(monkeypatch):
    summary, quiz, flashcards = _sample_payload()
    long_text = _sample_chunking_text()

    chunk_text_mock = lambda _text: ["chunk-1", "chunk-2"]
    summarize_chunk_mock = AsyncMock(
        side_effect=[
            (["chunk-summary-1"], ["chunk-fact-1"]),
            (["chunk-summary-2"], ["chunk-fact-2"]),
        ]
    )
    get_pack_mock = AsyncMock(
        return_value=(
            '{"quiz": ' + str(quiz).replace("'", '"') + "}",
            '{"flashcards": ' + str(flashcards).replace("'", '"') + "}",
        )
    )

    monkeypatch.setattr(main, "CHUNKING_THRESHOLD_CHARS", 20)
    monkeypatch.setattr(main, "chunk_text", chunk_text_mock)
    monkeypatch.setattr(main, "summarize_chunk", summarize_chunk_mock)
    monkeypatch.setattr(main, "build_merge_outline_prompt", lambda _s, _f: "merge-prompt")
    monkeypatch.setattr(
        main.gemini_service,
        "call_gemini",
        AsyncMock(return_value='{"outline":["o1","o2"],"summary": ' + str(summary).replace("'", '"') + "}"),
    )
    monkeypatch.setattr(main, "get_study_pack_responses", get_pack_mock)

    returned_summary, returned_quiz, returned_flashcards = await main.generate_study_pack_slides(long_text)

    # Confirms chunking path behavior and sample payload mapping.
    assert summarize_chunk_mock.await_count == 2
    assert get_pack_mock.await_count == 1
    assert returned_summary == summary
    assert [q.model_dump() for q in returned_quiz] == [main.QuizQuestion(**q).model_dump() for q in quiz]
    assert [f.model_dump() for f in returned_flashcards] == [
        main.Flashcard(**f).model_dump() for f in flashcards
    ]
    for q in returned_quiz:
        assert q.answer in q.options
        assert q.topic.strip()


def test_chunk_text_preserves_all_markers_across_chunks():
    text = _marker_text(240)
    chunks = main.chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    merged = " ".join(chunks)
    for i in range(1, 241):
        token = f"T{i:04d}"
        assert token in merged


def test_chunk_text_overlap_is_consistent_for_adjacent_chunks():
    text = _marker_text(240)
    chunk_size = 140
    overlap = 30
    chunks = main.chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    assert len(chunks) > 1
    assert all(0 < len(c) <= chunk_size for c in chunks)
    for idx in range(len(chunks) - 1):
        left = chunks[idx]
        right = chunks[idx + 1]
        expected_overlap = min(overlap, len(left), len(right))
        # chunk_text trims per-chunk boundaries; compare normalized overlap.
        assert left[-expected_overlap:].strip() == right[:expected_overlap].strip()


@pytest.mark.asyncio
async def test_generate_study_pack_slides_real_chunk_text_preserves_headers(monkeypatch):
    summary, quiz, flashcards = _sample_payload()
    long_text = (
        "### Intro\n" + ("HTTP basics and stateless communication. " * 200) + "\n"
        "### Methods\n" + ("GET retrieves and POST submits state changes. " * 200) + "\n"
        "### StatusCodes\n" + ("2xx success, 4xx client error, 5xx server error. " * 200)
    )

    seen_chunks: list[str] = []

    async def capture_summarize_chunk(index: int, chunk: str, chunks: list[str]):
        seen_chunks.append(chunk)
        return [f"summary-{index}"], [f"fact-{index}"]

    monkeypatch.setattr(main, "CHUNKING_THRESHOLD_CHARS", 50)
    monkeypatch.setattr(main, "summarize_chunk", capture_summarize_chunk)
    monkeypatch.setattr(main, "build_merge_outline_prompt", lambda _s, _f: "merge-prompt")
    monkeypatch.setattr(
        main.gemini_service,
        "call_gemini",
        AsyncMock(return_value='{"outline":["o1","o2"],"summary": ' + str(summary).replace("'", '"') + "}"),
    )
    monkeypatch.setattr(
        main,
        "get_study_pack_responses",
        AsyncMock(
            return_value=(
                '{"quiz": ' + str(quiz).replace("'", '"') + "}",
                '{"flashcards": ' + str(flashcards).replace("'", '"') + "}",
            )
        ),
    )

    returned_summary, returned_quiz, returned_flashcards = await main.generate_study_pack_slides(long_text)

    assert len(seen_chunks) > 1
    # Header markers should still be present across the captured real chunks.
    captured = "\n".join(seen_chunks)
    assert "### Intro" in captured
    assert "### Methods" in captured
    assert "### StatusCodes" in captured
    # Ensure downstream outputs still map correctly.
    assert returned_summary == summary
    assert len(returned_quiz) == len(quiz)
    assert len(returned_flashcards) == len(flashcards)
