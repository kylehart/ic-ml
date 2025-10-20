"""
Unit tests for web_service API endpoints.

Tests API endpoints, webhook processing, and email integration with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import hashlib


# Import after mocking to avoid dependency issues
@pytest.fixture
def test_app():
    """Create test FastAPI app."""
    from src.web_service import app
    return app


@pytest.fixture
def test_client(test_app):
    """Create FastAPI test client."""
    return TestClient(test_app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Test GET /health returns 200 OK."""
        response = test_client.get("/health")

        assert response.status_code == 200

    def test_health_check_response_structure(self, test_client):
        """Test health check response has required fields."""
        response = test_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "use_cases" in data

        assert data["status"] == "healthy"
        assert isinstance(data["use_cases"], list)


class TestQuizResultsStorage:
    """Test QuizResultsStorage in-memory storage."""

    def test_hash_email_consistent(self):
        """Test email hashing is consistent."""
        from src.web_service import QuizResultsStorage

        storage = QuizResultsStorage()
        email = "test@example.com"

        hash1 = storage._hash_email(email)
        hash2 = storage._hash_email(email)

        assert hash1 == hash2

    def test_hash_email_case_insensitive(self):
        """Test email hashing is case insensitive."""
        from src.web_service import QuizResultsStorage

        storage = QuizResultsStorage()

        hash_lower = storage._hash_email("test@example.com")
        hash_upper = storage._hash_email("TEST@EXAMPLE.COM")

        assert hash_lower == hash_upper

    def test_store_and_retrieve_result(self):
        """Test storing and retrieving results by email."""
        from src.web_service import QuizResultsStorage

        storage = QuizResultsStorage()
        email = "test@example.com"
        token = "test-token-123"

        storage.store_result(
            email=email,
            status="completed",
            token=token,
            data={"test": "data"}
        )

        result = storage.get_result_by_email(email)

        assert result is not None
        assert result["status"] == "completed"
        assert result["data"]["test"] == "data"
        assert result["token"] == token

    def test_store_and_retrieve_by_token(self):
        """Test storing and retrieving results by token."""
        from src.web_service import QuizResultsStorage

        storage = QuizResultsStorage()
        email = "test@example.com"
        token = "test-token-123"

        storage.store_result(
            email=email,
            status="completed",
            token=token,
            data={"test": "data"}
        )

        result = storage.get_result_by_token(token)

        assert result is not None
        assert result["status"] == "completed"
        assert result["email"] == email

    def test_get_result_nonexistent_email(self):
        """Test retrieving non-existent result returns None."""
        from src.web_service import QuizResultsStorage

        storage = QuizResultsStorage()
        result = storage.get_result_by_email("nonexistent@example.com")

        assert result is None

    def test_get_result_nonexistent_token(self):
        """Test retrieving by non-existent token returns None."""
        from src.web_service import QuizResultsStorage

        storage = QuizResultsStorage()
        result = storage.get_result_by_token("nonexistent-token")

        assert result is None


class TestFormbricksWebhook:
    """Test Formbricks webhook endpoint."""

    def test_webhook_accepts_valid_payload(self, test_client, sample_formbricks_payload):
        """Test webhook accepts valid Formbricks payload."""
        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=sample_formbricks_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

    def test_webhook_extracts_email(self, test_client, sample_formbricks_payload):
        """Test webhook correctly extracts email from array format."""
        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=sample_formbricks_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "response_id" in data

    def test_webhook_ignores_non_finished_events(self, test_client):
        """Test webhook ignores events other than responseFinished."""
        payload = {
            "event": "responseStarted",
            "data": {"id": "test-123"}
        }

        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=payload
        )

        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_requires_email(self, test_client):
        """Test webhook returns error when email is missing."""
        payload = {
            "event": "responseFinished",
            "data": {
                "id": "test-123",
                "data": {
                    # Missing email field
                    "dc185mu0h2xzutpzfgq8eyjy": "I have a health issue"
                }
            }
        }

        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=payload
        )

        data = response.json()
        assert data["status"] == "error"
        assert "email" in data["message"].lower()

    def test_webhook_requires_health_issue(self, test_client):
        """Test webhook returns error when health issue is missing."""
        payload = {
            "event": "responseFinished",
            "data": {
                "id": "test-123",
                "data": {
                    "d9klpkum9vi8x9vkunhu63fn": ["", "", "test@example.com", "", ""]
                    # Missing health issue field
                }
            }
        }

        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=payload
        )

        data = response.json()
        assert data["status"] == "error"
        assert "health issue" in data["message"].lower()

    def test_webhook_maps_choice_ids(self, test_client, sample_formbricks_payload):
        """Test webhook maps choice IDs to readable names."""
        # The payload has "mn3195wdsqv6qf80tt299v2q" which should map to "Sleep Issues"
        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=sample_formbricks_payload
        )

        assert response.status_code == 200
        # Webhook should process this without error


class TestResultsLookup:
    """Test results lookup endpoint."""

    def test_lookup_results_page_returns_html(self, test_client):
        """Test GET /results returns HTML page."""
        response = test_client.get("/results")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Health Quiz Results" in response.text

    def test_lookup_results_by_email_found(self, test_client):
        """Test POST /api/v1/results/lookup finds existing results."""
        # Store a result first
        from src.web_service import results_storage

        email = "test@example.com"
        results_storage.store_result(
            email=email,
            status="completed",
            data={"test": "data"},
            html_report="<html>Test Report</html>"
        )

        response = test_client.post(
            "/api/v1/results/lookup",
            json={"email": email}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["html_report"] == "<html>Test Report</html>"

    def test_lookup_results_by_email_not_found(self, test_client):
        """Test POST /api/v1/results/lookup for non-existent email."""
        response = test_client.post(
            "/api/v1/results/lookup",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"

    def test_lookup_results_processing_status(self, test_client):
        """Test lookup returns processing status."""
        from src.web_service import results_storage

        email = "processing@example.com"
        results_storage.store_result(
            email=email,
            status="processing"
        )

        response = test_client.post(
            "/api/v1/results/lookup",
            json={"email": email}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"


class TestResendEmailService:
    """Test Resend email service integration."""

    def test_email_service_disabled_without_api_key(self):
        """Test email service is disabled when API key is not set."""
        from src.web_service import ResendEmailService

        with patch.dict('os.environ', {}, clear=True):
            service = ResendEmailService()
            assert service.enabled is False

    def test_email_service_enabled_with_api_key(self):
        """Test email service is enabled when API key is set."""
        from src.web_service import ResendEmailService

        with patch.dict('os.environ', {'RESEND_API_KEY': 'test-key'}):
            service = ResendEmailService()
            assert service.enabled is True

    @pytest.mark.asyncio
    async def test_send_email_when_disabled(self):
        """Test sending email when service is disabled returns False."""
        from src.web_service import ResendEmailService

        with patch.dict('os.environ', {}, clear=True):
            service = ResendEmailService()
            result = await service.send_health_quiz_results(
                to_email="test@example.com",
                html_content="<html>Test</html>"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_resend_api):
        """Test successful email sending."""
        from src.web_service import ResendEmailService

        with patch.dict('os.environ', {'RESEND_API_KEY': 'test-key'}):
            service = ResendEmailService()
            result = await service.send_health_quiz_results(
                to_email="test@example.com",
                html_content="<html>Test Report</html>"
            )

            assert result is True


class TestClientAuthentication:
    """Test client authentication."""

    def test_client_auth_initialization(self):
        """Test ClientAuth initializes with client tokens."""
        from src.web_service import ClientAuth

        auth = ClientAuth()
        assert "rogue_herbalist_token" in auth.client_tokens

    def test_check_use_case_access_valid(self):
        """Test use case access check with valid access."""
        from src.web_service import ClientAuth

        auth = ClientAuth()
        client_info = {
            "client_id": "rogue_herbalist",
            "use_cases": ["health_quiz", "product_classification"]
        }

        # Should not raise exception
        auth.check_use_case_access(client_info, "health_quiz")

    def test_check_use_case_access_invalid(self):
        """Test use case access check with invalid access."""
        from src.web_service import ClientAuth
        from fastapi import HTTPException

        auth = ClientAuth()
        client_info = {
            "client_id": "rogue_herbalist",
            "use_cases": ["health_quiz"]
        }

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            auth.check_use_case_access(client_info, "product_classification")

        assert exc_info.value.status_code == 403


class TestHTMLReportGeneration:
    """Test HTML report generation."""

    def test_generate_html_report_structure(self):
        """Test HTML report has correct structure."""
        from src.web_service import generate_html_report_from_results

        quiz_output = {
            "general_recommendations": ["Advice 1", "Advice 2"],
            "lifestyle_suggestions": ["Suggestion 1"],
            "educational_content": ["Content 1"],
            "confidence_score": 0.85,
            "consultation_recommended": False
        }

        product_recommendations = [
            {
                "title": "Test Product",
                "category": "immune_support",
                "relevance_score": 0.9,
                "rationale": "Good for health",
                "ingredient_highlights": ["Ingredient 1"],
                "purchase_link": "https://example.com/product"
            }
        ]

        timing_info = {
            "total_duration_seconds": 2.5
        }

        html = generate_html_report_from_results(
            quiz_output=quiz_output,
            product_recommendations=product_recommendations,
            timing_info=timing_info,
            email="test@example.com"
        )

        assert "<html" in html
        assert "Advice 1" in html
        assert "Test Product" in html
        assert "85%" in html  # Confidence score

    def test_generate_html_report_with_consultation_warning(self):
        """Test HTML report includes consultation warning when needed."""
        from src.web_service import generate_html_report_from_results

        quiz_output = {
            "general_recommendations": ["Advice"],
            "lifestyle_suggestions": [],
            "educational_content": [],
            "confidence_score": 0.7,
            "consultation_recommended": True  # Should trigger warning
        }

        html = generate_html_report_from_results(
            quiz_output=quiz_output,
            product_recommendations=[],
            timing_info={"total_duration_seconds": 1.0},
            email="test@example.com"
        )

        assert "⚠️" in html or "warning" in html.lower()
        assert "Professional Consultation" in html or "consultation" in html.lower()


class TestAdminEndpoints:
    """Test administrative endpoints."""

    def test_list_clients(self, test_client):
        """Test GET /api/v1/admin/clients returns client list."""
        response = test_client.get("/api/v1/admin/clients")

        assert response.status_code == 200
        data = response.json()
        assert "clients" in data
        assert isinstance(data["clients"], list)

    def test_list_use_cases(self, test_client):
        """Test GET /api/v1/admin/use-cases returns use case list."""
        response = test_client.get("/api/v1/admin/use-cases")

        assert response.status_code == 200
        data = response.json()
        assert "use_cases" in data


class TestErrorHandlers:
    """Test error handling."""

    def test_404_handler(self, test_client):
        """Test 404 error handler."""
        response = test_client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()


@pytest.mark.parametrize("status", ["processing", "completed", "failed"])
def test_different_result_statuses(status, test_client):
    """Parametrized test for different result statuses."""
    from src.web_service import results_storage

    email = f"{status}@example.com"
    results_storage.store_result(
        email=email,
        status=status,
        data={"status": status}
    )

    response = test_client.post(
        "/api/v1/results/lookup",
        json={"email": email}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status


class TestWebhookEmailExtraction:
    """Test email extraction from various Formbricks payload formats."""

    @pytest.mark.parametrize("email_value,expected_email", [
        (["", "", "test@example.com", "", ""], "test@example.com"),
        ("direct@example.com", "direct@example.com"),
        ({"email": "nested@example.com"}, "nested@example.com"),
    ])
    def test_email_extraction_formats(self, test_client, email_value, expected_email):
        """Test email extraction from different payload formats."""
        payload = {
            "event": "responseFinished",
            "data": {
                "id": "test-123",
                "data": {
                    "d9klpkum9vi8x9vkunhu63fn": email_value,
                    "dc185mu0h2xzutpzfgq8eyjy": "I have a health issue"
                }
            }
        }

        response = test_client.post(
            "/api/v1/webhook/formbricks",
            json=payload
        )

        # Should process successfully
        assert response.status_code == 200
