"""
Web Service API for Multi-Use Case LLM Platform

Provides REST API endpoints for health quiz and product classification use cases
with real-time processing, client authentication, and usage tracking.

MVP: Formbricks webhook integration with email-based results lookup
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, List, Any, Optional
import uvicorn
from datetime import datetime, timedelta
import logging
import hashlib
import json
from pathlib import Path
import os

from use_case_framework import UseCaseManager, use_case_registry
from health_quiz_use_case import HealthQuizInput, HealthQuizOutput


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# In-Memory Storage for Quiz Results (MVP)
class QuizResultsStorage:
    """Simple in-memory storage for quiz results using both email hash and token."""

    def __init__(self):
        self.results_by_email = {}  # {email_hash: {status, data, timestamp, html_report, token}}
        self.results_by_token = {}  # {token: email_hash} - for quick token lookup
        self.ttl_hours = 24  # Results expire after 24 hours

    def _hash_email(self, email: str) -> str:
        """Create a secure hash of email for privacy."""
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()

    def store_result(self, email: str, status: str, token: str = None,
                    data: Dict[str, Any] = None, html_report: str = None):
        """Store quiz result by email hash and optional token."""
        email_hash = self._hash_email(email)

        result_data = {
            "status": status,
            "data": data,
            "html_report": html_report,
            "timestamp": datetime.now().isoformat(),
            "email": email,  # Store for email sending
            "token": token
        }

        self.results_by_email[email_hash] = result_data

        # Also store by token for direct access
        if token:
            self.results_by_token[token] = email_hash
            logger.info(f"Stored result for email hash {email_hash[:8]}... with status: {status}, token: {token[:8]}...")
        else:
            logger.info(f"Stored result for email hash {email_hash[:8]}... with status: {status}")

    def get_result_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve quiz result by email."""
        email_hash = self._hash_email(email)
        result = self.results_by_email.get(email_hash)

        if not result:
            logger.warning(f"No result found for email hash {email_hash[:8]}...")
            return None

        # Check if result has expired
        result_time = datetime.fromisoformat(result["timestamp"])
        if datetime.now() - result_time > timedelta(hours=self.ttl_hours):
            logger.info(f"Result expired for email hash {email_hash[:8]}...")
            del self.results_by_email[email_hash]
            if result.get("token"):
                del self.results_by_token[result["token"]]
            return None

        return result

    def get_result_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve quiz result by token."""
        email_hash = self.results_by_token.get(token)

        if not email_hash:
            logger.warning(f"No result found for token {token[:8]}...")
            return None

        result = self.results_by_email.get(email_hash)

        if not result:
            logger.warning(f"Token {token[:8]}... found but no email result")
            return None

        # Check if result has expired
        result_time = datetime.fromisoformat(result["timestamp"])
        if datetime.now() - result_time > timedelta(hours=self.ttl_hours):
            logger.info(f"Result expired for token {token[:8]}...")
            del self.results_by_email[email_hash]
            del self.results_by_token[token]
            return None

        return result


# Resend Email Integration
class ResendEmailService:
    """Email service using Resend API."""

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "Rogue Herbalist Health Quiz <noreply@instruction.coach>")
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("RESEND_API_KEY not set - email sending disabled")

    async def send_health_quiz_results(self, to_email: str, html_content: str,
                                      subject: str = "Your Health Quiz Results"):
        """Send health quiz results via email using Resend."""
        if not self.enabled:
            logger.warning(f"Email sending disabled - would have sent to {to_email}")
            return False

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content
                    }
                )

                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True
                else:
                    logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False


# API Models
class FormbricksWebhookPayload(BaseModel):
    """Formbricks webhook payload model."""
    event: str
    data: Dict[str, Any]


class ResultsLookupRequest(BaseModel):
    """Request model for looking up results by email."""
    email: EmailStr
class HealthQuizRequest(BaseModel):
    """Request model for health quiz API."""
    health_issue_description: str = Field(..., min_length=10, max_length=2000,
                                        description="Description of the health issue")
    tried_already: Optional[str] = Field(None, max_length=1000,
                                       description="What has been tried before")
    primary_health_area: Optional[str] = Field(None,
                                             description="Primary health category")
    secondary_health_area: Optional[str] = Field(None,
                                                description="Secondary health category")
    age_range: Optional[str] = Field(None, description="Age range (e.g., '25-35')")
    severity_level: Optional[int] = Field(None, ge=1, le=10,
                                        description="Severity level 1-10")
    budget_preference: Optional[str] = Field(None,
                                           description="Budget preference: low/medium/high")
    lifestyle_factors: Optional[str] = Field(None, max_length=500,
                                           description="Additional lifestyle context")


class HealthQuizResponse(BaseModel):
    """Response model for health quiz API."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any]


class ProductClassificationRequest(BaseModel):
    """Request model for product classification API."""
    products: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100,
                                         description="List of products to classify")
    batch_size: Optional[int] = Field(10, ge=1, le=50,
                                    description="Batch processing size")
    model_override: Optional[str] = Field(None,
                                        description="Override default model")


class ProductClassificationResponse(BaseModel):
    """Response model for product classification API."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any]
    run_id: Optional[str] = None


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""
    client_id: str
    use_case: str
    period_start: str
    period_end: str
    total_requests: int
    total_cost_usd: float
    token_usage: Dict[str, int]
    model_breakdown: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    use_cases: List[str]


# Security
security = HTTPBearer()


class ClientAuth:
    """Client authentication and authorization."""

    def __init__(self):
        # In production, this would load from a secure database
        self.client_tokens = {
            "rogue_herbalist_token": {
                "client_id": "rogue_herbalist",
                "use_cases": ["health_quiz", "product_classification"],
                "rate_limit": 1000,  # requests per hour
                "active": True
            }
        }

    async def authenticate_client(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Authenticate client and return client info."""
        token = credentials.credentials

        if token not in self.client_tokens:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        client_info = self.client_tokens[token]
        if not client_info["active"]:
            raise HTTPException(
                status_code=403,
                detail="Client account is inactive"
            )

        return client_info

    def check_use_case_access(self, client_info: Dict[str, Any], use_case: str):
        """Check if client has access to specific use case."""
        if use_case not in client_info["use_cases"]:
            raise HTTPException(
                status_code=403,
                detail=f"Client does not have access to use case: {use_case}"
            )


# Initialize FastAPI app
app = FastAPI(
    title="IC-ML Multi-Use Case Platform",
    description="LLM-powered health quiz and product classification platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
auth = ClientAuth()
use_case_manager = UseCaseManager(use_case_registry)
results_storage = QuizResultsStorage()
email_service = ResendEmailService()


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        use_cases=use_case_registry.list_use_cases()
    )


# Formbricks Webhook Integration (MVP)
@app.post("/api/v1/webhook/formbricks")
async def formbricks_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Formbricks form submissions.
    Processes health quiz submissions and stores results by email.
    """
    try:
        payload = await request.json()
        logger.info(f"=== WEBHOOK RECEIVED ===")
        logger.info(f"Event: {payload.get('event')}")
        logger.info(f"Full payload: {json.dumps(payload, indent=2)}")

        # Extract form data from Formbricks payload
        event = payload.get("event")
        data = payload.get("data", {})

        if event != "responseFinished":
            logger.info(f"Ignoring event: {event}")
            return {"status": "ignored", "event": event}

        # Extract response data
        # Note: Formbricks payload structure is payload["data"]["id"] and payload["data"]["data"]
        # NOT payload["data"]["response"]["id"] - there is no "response" nesting
        response_id = data.get("id")
        logger.info(f"Response ID: {response_id}")

        # Map Formbricks question IDs to our fields
        answers = data.get("data", {})
        logger.info(f"Answers received: {json.dumps(answers, indent=2)}")

        # Extract email (required field)
        email = None
        health_issue = None
        primary_area = None
        severity = 5
        tried_already = None
        age_range = None
        lifestyle = None

        # Exact question ID mapping for this Formbricks form
        # Updated: October 21, 2025 - Changed from contactInfo to openText with email validation
        EMAIL_QUESTION_ID = "y4t3q9ctov2dn6qdon1kdbrq"  # openText (inputType: email) - supports prefilling!
        HEALTH_ISSUE_QUESTION_ID = "dc185mu0h2xzutpzfgq8eyjy"
        PRIMARY_AREA_QUESTION_ID = "ty1zv10pffpxh2a2bymi2wz7"
        SEVERITY_QUESTION_ID = "iht7n48iwkoc1jc8ubnzrqi7"
        TRIED_ALREADY_QUESTION_ID = "ud6nnuhrgf9trqwe8j3kibii"
        AGE_RANGE_QUESTION_ID = "yru7w3e402yk8vpf1dfbw0tr"
        LIFESTYLE_QUESTION_ID = "pr4jtzy9epmquvwdksj9tctb"

        # Map primary area choice IDs to readable names
        PRIMARY_AREA_CHOICES = {
            "k7ly7nx8lvgwedl1yctb215y": "Digestive Health",
            "xugvsda3meo6onr84icgen6j": "Immune Support",
            "qir7u9yy7eh9rqad1jvgh41e": "Stress & Anxiety",
            "mn3195wdsqv6qf80tt299v2q": "Sleep Issues",
            "jhs5ehsljo52rrd9yuxbw7td": "Joint & Muscle Pain",
            "zhu8gde20tnv7talgv5ruec8": "Energy & Vitality",
            "xlzt05zhync9v1ysegm4a80c": "Women's Health",
            "m3jjnnug2s1iwtf1lo0l6uip": "Men's Health",
            "other": "Other"
        }

        # Map age range choice IDs to readable names
        AGE_RANGE_CHOICES = {
            "owv82s8m0kumnrp08j8gaqhu": "18-25",
            "nults2ndbrn6bovvs4ce03ax": "26-35",
            "u9fy0mtyjddkzrkhruh0682p": "36-45",
            "e7drxvgsjys4vewrmq5qvkoy": "46-55",
            "l9xn0kf9c8rbndzgghthsr73": "56-65",
            "lu5l0u7myjxy8b8to0zaix8m": "66+"
        }

        # Reverse mappings for URL prefilling (primary area)
        AREA_TO_CHOICE_ID = {v: k for k, v in PRIMARY_AREA_CHOICES.items()}

        # Reverse mappings for URL prefilling (age range)
        AGE_TO_CHOICE_ID = {v: k for k, v in AGE_RANGE_CHOICES.items()}

        # Parse answers - Formbricks format: {questionId: value}
        for question_id, value in answers.items():
            logger.info(f"Processing question: {question_id} = {value}")

            # Email field (openText with inputType=email, simple string value)
            if question_id == EMAIL_QUESTION_ID:
                email = value
                logger.info(f"✓ Found email: {email}")

            # Health issue description
            elif question_id == HEALTH_ISSUE_QUESTION_ID:
                health_issue = value
                logger.info(f"✓ Found health issue: {health_issue[:50] if health_issue else 'None'}...")

            # Primary health area (choice ID needs mapping)
            elif question_id == PRIMARY_AREA_QUESTION_ID:
                # Value might be a choice ID that needs mapping
                if value in PRIMARY_AREA_CHOICES:
                    primary_area = PRIMARY_AREA_CHOICES[value]
                    logger.info(f"✓ Found primary area (mapped from {value}): {primary_area}")
                else:
                    primary_area = value  # Use as-is if not in mapping
                    logger.info(f"✓ Found primary area (direct): {primary_area}")

            # Severity rating (1-10)
            elif question_id == SEVERITY_QUESTION_ID:
                try:
                    severity = int(value)
                    logger.info(f"✓ Found severity: {severity}")
                except (ValueError, TypeError):
                    severity = 5
                    logger.warning(f"Could not parse severity: {value}, using default: 5")

            # What have you tried already
            elif question_id == TRIED_ALREADY_QUESTION_ID:
                tried_already = value
                logger.info(f"✓ Found tried already: {tried_already[:50] if tried_already else 'None'}...")

            # Age range (choice ID needs mapping)
            elif question_id == AGE_RANGE_QUESTION_ID:
                if value in AGE_RANGE_CHOICES:
                    age_range = AGE_RANGE_CHOICES[value]
                    logger.info(f"✓ Found age range (mapped from {value}): {age_range}")
                else:
                    age_range = value
                    logger.info(f"✓ Found age range (direct): {age_range}")

            # Lifestyle factors
            elif question_id == LIFESTYLE_QUESTION_ID:
                lifestyle = value
                logger.info(f"✓ Found lifestyle: {lifestyle[:50] if lifestyle else 'None'}...")

        if not email:
            logger.error("❌ No email found in webhook payload")
            logger.error(f"Available question IDs: {list(answers.keys())}")
            return {"status": "error", "message": "Email is required"}

        if not health_issue:
            logger.error("❌ No health issue description found in webhook payload")
            logger.error(f"Available question IDs: {list(answers.keys())}")
            return {"status": "error", "message": "Health issue description is required"}

        logger.info(f"✅ Successfully extracted data for email: {email}")

        # Store initial status as processing with response_id as token
        results_storage.store_result(email, status="processing", token=response_id)

        # Process quiz in background
        background_tasks.add_task(
            process_health_quiz_webhook,
            email=email,
            health_issue=health_issue,
            primary_area=primary_area,
            severity=severity,
            tried_already=tried_already,
            age_range=age_range,
            lifestyle=lifestyle,
            token=response_id
        )

        logger.info(f"Queued health quiz processing for {email}")

        return {
            "status": "accepted",
            "message": "Health quiz processing started",
            "response_id": response_id
        }

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


async def process_health_quiz_webhook(email: str, health_issue: str,
                                     primary_area: Optional[str],
                                     severity: int,
                                     tried_already: Optional[str],
                                     age_range: Optional[str],
                                     lifestyle: Optional[str],
                                     token: str):
    """Background task to process health quiz and generate results."""
    try:
        logger.info(f"🔄 Processing health quiz for {email} (token: {token[:8]}...)")

        # Import framework components
        from health_quiz_use_case import HealthQuizUseCase
        from model_config import UseCaseConfig
        import time

        # Create quiz input
        quiz_input_dict = {
            "health_issue_description": health_issue,
            "tried_already": tried_already,
            "primary_health_area": primary_area,
            "severity_level": severity,
            "age_range": age_range,
            "lifestyle_factors": lifestyle
        }

        # Initialize use case with config
        use_case_config = UseCaseConfig(
            use_case_name="health_quiz",
            model_config="gpt4o_mini",  # Default model
            client_id="rogue_herbalist"
        )
        use_case = HealthQuizUseCase(config=use_case_config)

        # Process through framework
        start_time = time.time()
        result = use_case.process_request(quiz_input_dict)
        processing_time = time.time() - start_time

        if not result.success:
            # Framework returned failure
            error_msg = result.metadata.get("error", "Unknown error")
            logger.error(f"❌ Health quiz processing failed: {error_msg}")
            raise Exception(error_msg)

        # Extract results from framework output
        output_data = result.data
        quiz_output = {
            "general_recommendations": output_data.get("general_recommendations", []),
            "lifestyle_suggestions": output_data.get("lifestyle_suggestions", []),
            "educational_content": output_data.get("educational_content", []),
            "consultation_recommended": output_data.get("consultation_recommended", False)
        }

        # Convert product recommendations from dataclass objects to dicts
        # (Framework returns list of ProductRecommendation objects in dict form already)
        product_recs = output_data.get("specific_products", [])

        timing_info = {
            "total_time": processing_time,
            "model_used": result.metadata.get("model_used", "gpt4o_mini")
        }

        # Get cost data from use case LLM client if available
        client_cost_data = {}
        if hasattr(use_case, 'llm_client') and use_case.llm_client:
            client_cost_data = use_case.llm_client.get_cost_breakdown_for_reporting()

        # Generate HTML report with revision URL
        user_data = {
            "email": email,
            "health_issue": health_issue,
            "primary_area": primary_area,
            "severity": severity,
            "tried_already": tried_already,
            "age_range": age_range,
            "lifestyle": lifestyle
        }
        html_report = generate_html_report_from_results(
            quiz_output=quiz_output,
            product_recommendations=product_recs,
            timing_info=timing_info,
            email=email,
            token=token,
            user_data=user_data
        )

        # Store results
        results_storage.store_result(
            email=email,
            status="completed",
            token=token,
            data={
                "quiz_output": quiz_output,
                "product_recommendations": product_recs,
                "timing_info": timing_info,
                "cost": client_cost_data
            },
            html_report=html_report
        )

        # Send email with results
        await email_service.send_health_quiz_results(
            to_email=email,
            html_content=html_report,
            subject="Your Personalized Health Quiz Results from Rogue Herbalist"
        )

        logger.info(f"✅ Successfully processed health quiz for {email} (token: {token[:8]}...)")

    except Exception as e:
        logger.error(f"❌ Error processing health quiz: {e}", exc_info=True)
        results_storage.store_result(
            email=email,
            status="failed",
            token=token,
            data={"error": str(e)}
        )


@app.get("/results", response_class=HTMLResponse)
async def results_page_email_lookup(e: Optional[str] = None):
    """
    Serve HTML page for looking up quiz results by email.

    If ?e=email parameter is provided, auto-lookup results for that email.
    This allows Formbricks redirect URLs with recall syntax like:
    https://ic-ml-production.up.railway.app/results?e=@y4t3q9ctov2dn6qdon1kdbrq
    """
    # Log what we received for debugging Formbricks @ syntax
    if e:
        logger.info(f"📧 /results called with email parameter: {e}")
        logger.info(f"📧 Email parameter length: {len(e)} chars")
        logger.info(f"📧 Email parameter starts with @: {e.startswith('@')}")

        # Check if this looks like an email address (not unexpanded @ syntax)
        if "@" in e and not e.startswith("@") and "." in e:
            logger.info(f"✅ Email parameter looks valid, attempting auto-lookup")
            # Auto-lookup results and display them
            result = results_storage.get_result_by_email(e)

            if result and result["status"] == "completed":
                logger.info(f"✅ Found completed results for email: {e}")
                # Return the HTML report directly
                return HTMLResponse(content=result.get("html_report", "Results not available"))
            elif result and result["status"] == "processing":
                logger.info(f"⏳ Results still processing for email: {e}")
                # Show processing message with auto-refresh
                return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Processing Your Results - Rogue Herbalist</title>
                    <meta http-equiv="refresh" content="5">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            padding: 20px;
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 12px;
                            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                            text-align: center;
                            max-width: 500px;
                        }}
                        h1 {{ color: #333; margin-bottom: 20px; }}
                        p {{ color: #666; margin-bottom: 20px; }}
                        .loader {{
                            border: 4px solid #f3f3f3;
                            border-top: 4px solid #667eea;
                            border-radius: 50%;
                            width: 50px;
                            height: 50px;
                            animation: spin 1s linear infinite;
                            margin: 20px auto;
                        }}
                        @keyframes spin {{
                            0% {{ transform: rotate(0deg); }}
                            100% {{ transform: rotate(360deg); }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>⏳ Processing Your Health Quiz</h1>
                        <div class="loader"></div>
                        <p>We're analyzing your responses and generating personalized recommendations.</p>
                        <p>This page will auto-refresh in 5 seconds...</p>
                    </div>
                </body>
                </html>
                """)
            else:
                logger.warning(f"❌ No results found for email: {e}")
                # Fall through to show email lookup form
        else:
            logger.warning(f"⚠️ Email parameter doesn't look valid (might be unexpanded @ syntax): {e}")
            # Fall through to show email lookup form

    # Default: show email lookup form
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Health Quiz Results - Rogue Herbalist</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                width: 100%;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 16px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 500;
            }
            input[type="email"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input[type="email"]:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                width: 100%;
                padding: 14px;
                margin-top: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }
            button:active {
                transform: translateY(0);
            }
            .message {
                margin-top: 20px;
                padding: 12px;
                border-radius: 6px;
                display: none;
            }
            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .message.info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            .loader {
                display: none;
                margin: 20px auto;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            #resultsContainer {
                margin-top: 30px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Health Quiz Results</h1>
            <p class="subtitle">Enter your email to view your personalized recommendations</p>

            <form id="lookupForm">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required
                       placeholder="your.email@example.com">
                <button type="submit">View My Results</button>
            </form>

            <div class="loader" id="loader"></div>
            <div class="message" id="message"></div>
            <div id="resultsContainer"></div>
        </div>

        <script>
            const form = document.getElementById('lookupForm');
            const loader = document.getElementById('loader');
            const message = document.getElementById('message');
            const resultsContainer = document.getElementById('resultsContainer');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const email = document.getElementById('email').value;

                // Show loader
                loader.style.display = 'block';
                message.style.display = 'none';
                resultsContainer.style.display = 'none';

                try {
                    const response = await fetch('/api/v1/results/lookup', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email })
                    });

                    const data = await response.json();
                    loader.style.display = 'none';

                    if (data.status === 'completed') {
                        // Show results
                        resultsContainer.innerHTML = data.html_report;
                        resultsContainer.style.display = 'block';
                    } else if (data.status === 'processing') {
                        message.className = 'message info';
                        message.textContent = 'Your results are still being processed. Please wait a moment and try again.';
                        message.style.display = 'block';

                        // Auto-retry after 3 seconds
                        setTimeout(() => form.requestSubmit(), 3000);
                    } else if (data.status === 'not_found') {
                        message.className = 'message error';
                        message.textContent = 'No results found for this email. Please check your email address or complete the quiz first.';
                        message.style.display = 'block';
                    } else {
                        message.className = 'message error';
                        message.textContent = 'An error occurred. Please try again.';
                        message.style.display = 'block';
                    }
                } catch (error) {
                    loader.style.display = 'none';
                    message.className = 'message error';
                    message.textContent = 'Connection error. Please try again.';
                    message.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/results/{token}", response_class=HTMLResponse)
async def results_page_token_lookup(token: str):
    """Serve HTML page that auto-loads quiz results by token."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Health Quiz Results - Rogue Herbalist</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
                text-align: center;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 16px;
                text-align: center;
            }}
            .loading-state {{
                text-align: center;
                padding: 40px 20px;
            }}
            .loading-icon {{
                font-size: 48px;
                margin-bottom: 20px;
                animation: pulse 2s ease-in-out infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            .loader {{
                display: inline-block;
                margin: 20px auto;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .message {{
                margin-top: 20px;
                padding: 12px;
                border-radius: 6px;
                display: none;
            }}
            .message.error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .message.info {{
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }}
            #resultsContainer {{
                margin-top: 20px;
                display: none;
            }}
            .email-lookup-link {{
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
            }}
            .email-lookup-link a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }}
            .email-lookup-link a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div id="loadingState" class="loading-state">
                <div class="loading-icon">🌿</div>
                <h1>Analyzing Your Health Needs...</h1>
                <p class="subtitle">Generating personalized recommendations</p>
                <div class="loader"></div>
                <p style="color: #666; margin-top: 20px;">This usually takes 6-8 seconds</p>
            </div>

            <div class="message" id="message"></div>
            <div id="resultsContainer"></div>

            <div id="emailLookupFallback" class="email-lookup-link" style="display: none;">
                <p>Can't find your results? <a href="/results">Look up by email instead</a></p>
            </div>
        </div>

        <script>
            const token = "{token}";
            const loadingState = document.getElementById('loadingState');
            const message = document.getElementById('message');
            const resultsContainer = document.getElementById('resultsContainer');
            const emailLookupFallback = document.getElementById('emailLookupFallback');

            // Separate counters for different states
            let notFoundRetries = 0;
            let processingRetries = 0;
            let networkErrorRetries = 0;

            const MAX_NOT_FOUND_RETRIES = 10;  // 30 seconds for webhook to arrive
            const MAX_PROCESSING_RETRIES = 40;  // 120 seconds for processing
            const MAX_NETWORK_ERROR_RETRIES = 5;  // 15 seconds for network recovery
            const POLL_INTERVAL_MS = 3000;  // 3 seconds between polls

            async function loadResults() {{
                try {{
                    console.log(`Polling results for token: ${{token.substring(0, 8)}}...`);
                    const response = await fetch(`/api/v1/results/lookup/token/${{token}}`);

                    // Check if response is OK (200-299)
                    if (!response.ok) {{
                        console.error(`HTTP error! status: ${{response.status}}`);
                        handleNetworkError(response.status);
                        return;
                    }}

                    const data = await response.json();
                    console.log(`Received status: ${{data.status}}`);

                    // Reset network error counter on successful response
                    networkErrorRetries = 0;

                    if (data.status === 'completed') {{
                        console.log('✅ Results completed - displaying');
                        loadingState.style.display = 'none';
                        resultsContainer.innerHTML = data.html_report;
                        resultsContainer.style.display = 'block';

                    }} else if (data.status === 'processing') {{
                        console.log(`⏳ Still processing (retry ${{processingRetries + 1}}/${{MAX_PROCESSING_RETRIES}})`);
                        processingRetries++;

                        if (processingRetries < MAX_PROCESSING_RETRIES) {{
                            setTimeout(loadResults, POLL_INTERVAL_MS);
                        }} else {{
                            console.error('❌ Processing timeout exceeded');
                            loadingState.style.display = 'none';
                            message.className = 'message error';
                            message.textContent = 'Processing is taking longer than expected. Your results will be emailed to you shortly.';
                            message.style.display = 'block';
                            emailLookupFallback.style.display = 'block';
                        }}

                    }} else if (data.status === 'not_found') {{
                        console.log(`🔍 Not found yet (retry ${{notFoundRetries + 1}}/${{MAX_NOT_FOUND_RETRIES}}) - waiting for webhook`);
                        notFoundRetries++;

                        if (notFoundRetries < MAX_NOT_FOUND_RETRIES) {{
                            setTimeout(loadResults, POLL_INTERVAL_MS);
                        }} else {{
                            console.error('❌ Not found timeout - webhook never arrived');
                            loadingState.style.display = 'none';
                            message.className = 'message error';
                            message.textContent = 'Results not found or have expired (24 hour limit). Please check your email for results.';
                            message.style.display = 'block';
                            emailLookupFallback.style.display = 'block';
                        }}

                    }} else if (data.status === 'failed' || data.status === 'error') {{
                        console.error(`❌ Processing failed: ${{data.message || 'Unknown error'}}`);
                        loadingState.style.display = 'none';
                        message.className = 'message error';
                        message.textContent = 'An error occurred while processing your quiz. Please check your email for results or contact support.';
                        message.style.display = 'block';
                        emailLookupFallback.style.display = 'block';

                    }} else {{
                        console.error(`❌ Unknown status: ${{data.status}}`);
                        loadingState.style.display = 'none';
                        message.className = 'message error';
                        message.textContent = 'Unexpected error. Please check your email for results.';
                        message.style.display = 'block';
                        emailLookupFallback.style.display = 'block';
                    }}

                }} catch (error) {{
                    console.error('Network error:', error);
                    handleNetworkError(error);
                }}
            }}

            function handleNetworkError(error) {{
                networkErrorRetries++;
                console.log(`🌐 Network error (retry ${{networkErrorRetries}}/${{MAX_NETWORK_ERROR_RETRIES}}): ${{error}}`);

                if (networkErrorRetries < MAX_NETWORK_ERROR_RETRIES) {{
                    // Retry after delay - network might recover
                    console.log(`Retrying in ${{POLL_INTERVAL_MS}}ms...`);
                    setTimeout(loadResults, POLL_INTERVAL_MS);
                }} else {{
                    // Too many consecutive network errors - give up
                    console.error('❌ Network error limit exceeded');
                    loadingState.style.display = 'none';
                    message.className = 'message error';
                    message.textContent = 'Cannot reach server. Please check your internet connection and refresh the page, or check your email for results.';
                    message.style.display = 'block';
                    emailLookupFallback.style.display = 'block';
                }}
            }}

            // Start loading results immediately
            console.log('🚀 Starting results polling...');
            loadResults();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/v1/results/lookup")
async def lookup_results(request: ResultsLookupRequest):
    """Look up quiz results by email."""
    try:
        email = request.email
        logger.info(f"🔍 Looking up results for email: {email}")

        result = results_storage.get_result_by_email(email)

        if not result:
            logger.warning(f"❌ No results found for email: {email}")
            logger.info(f"Current storage has {len(results_storage.results_by_email)} email entries")
            logger.info(f"Current storage has {len(results_storage.results_by_token)} token entries")
            return {
                "status": "not_found",
                "message": "No results found for this email"
            }

        logger.info(f"✅ Found result for email: {email}, status: {result['status']}")
        return {
            "status": result["status"],
            "html_report": result.get("html_report"),
            "data": result.get("data"),
            "timestamp": result.get("timestamp")
        }

    except Exception as e:
        logger.error(f"❌ Error looking up results: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/v1/results/lookup/token/{token}")
async def lookup_results_by_token(token: str):
    """Look up quiz results by token (response ID from Formbricks)."""
    try:
        logger.info(f"🔍 Looking up results for token: {token[:8]}...")

        result = results_storage.get_result_by_token(token)

        if not result:
            logger.warning(f"❌ No results found for token: {token[:8]}...")
            logger.info(f"Current storage has {len(results_storage.results_by_email)} email entries")
            logger.info(f"Current storage has {len(results_storage.results_by_token)} token entries")
            return {
                "status": "not_found",
                "message": "No results found for this token"
            }

        logger.info(f"✅ Found result for token: {token[:8]}..., status: {result['status']}")
        return {
            "status": result["status"],
            "html_report": result.get("html_report"),
            "data": result.get("data"),
            "timestamp": result.get("timestamp")
        }

    except Exception as e:
        logger.error(f"❌ Error looking up results by token: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


def generate_prefilled_form_url(email: str, health_issue: str,
                               primary_area: Optional[str], severity: int,
                               tried_already: Optional[str], age_range: Optional[str],
                               lifestyle: Optional[str]) -> str:
    """
    Generate Formbricks form URL with all user answers prefilled for revision.

    This creates a stateless revision link - all user data is in the URL itself.
    Works in emails, saved HTML files, weeks/months later - no server memory required.

    Formbricks form URL: https://app.formbricks.com/s/cmf5homcz0p1kww010hzezjjp
    """
    from urllib.parse import urlencode, quote

    # Log what we're receiving
    logger.info(f"📝 generate_prefilled_form_url called with:")
    logger.info(f"  email: {email}")
    logger.info(f"  health_issue: {health_issue[:100] if health_issue else 'None'}...")
    logger.info(f"  primary_area: {primary_area}")
    logger.info(f"  severity: {severity}")
    logger.info(f"  tried_already: {tried_already[:50] if tried_already else 'None'}...")
    logger.info(f"  age_range: {age_range}")
    logger.info(f"  lifestyle: {lifestyle[:50] if lifestyle else 'None'}...")

    # Formbricks question IDs
    # Updated: October 21, 2025 - Changed from contactInfo to openText with email validation
    EMAIL_QUESTION_ID = "y4t3q9ctov2dn6qdon1kdbrq"  # openText (inputType: email) - supports prefilling!
    HEALTH_ISSUE_QUESTION_ID = "dc185mu0h2xzutpzfgq8eyjy"
    PRIMARY_AREA_QUESTION_ID = "ty1zv10pffpxh2a2bymi2wz7"
    SEVERITY_QUESTION_ID = "iht7n48iwkoc1jc8ubnzrqi7"
    TRIED_ALREADY_QUESTION_ID = "ud6nnuhrgf9trqwe8j3kibii"
    AGE_RANGE_QUESTION_ID = "yru7w3e402yk8vpf1dfbw0tr"
    LIFESTYLE_QUESTION_ID = "pr4jtzy9epmquvwdksj9tctb"

    # Reverse mappings for choice IDs
    AREA_TO_CHOICE_ID = {
        "Digestive Health": "k7ly7nx8lvgwedl1yctb215y",
        "Immune Support": "xugvsda3meo6onr84icgen6j",
        "Stress & Anxiety": "qir7u9yy7eh9rqad1jvgh41e",
        "Sleep Issues": "mn3195wdsqv6qf80tt299v2q",
        "Joint & Muscle Pain": "jhs5ehsljo52rrd9yuxbw7td",
        "Energy & Vitality": "zhu8gde20tnv7talgv5ruec8",
        "Women's Health": "xlzt05zhync9v1ysegm4a80c",
        "Men's Health": "m3jjnnug2s1iwtf1lo0l6uip",
        "Other": "other"
    }

    AGE_TO_CHOICE_ID = {
        "18-25": "owv82s8m0kumnrp08j8gaqhu",
        "26-35": "nults2ndbrn6bovvs4ce03ax",
        "36-45": "u9fy0mtyjddkzrkhruh0682p",
        "46-55": "e7drxvgsjys4vewrmq5qvkoy",
        "56-65": "l9xn0kf9c8rbndzgghthsr73",
        "66+": "lu5l0u7myjxy8b8to0zaix8m"
    }

    # Build query parameters - only include non-None values
    params = {}

    # Email field is now openText with inputType=email - prefilling works! ✅
    if email:
        params[EMAIL_QUESTION_ID] = email

    if health_issue:
        params[HEALTH_ISSUE_QUESTION_ID] = health_issue

    if primary_area:
        # Formbricks prefill expects display text, NOT choice ID
        # The string must exactly match the label in the form
        params[PRIMARY_AREA_QUESTION_ID] = primary_area

    if severity is not None:
        params[SEVERITY_QUESTION_ID] = str(severity)

    if tried_already:
        params[TRIED_ALREADY_QUESTION_ID] = tried_already

    if age_range:
        # Formbricks prefill expects display text, NOT choice ID
        # The string must exactly match the label in the form
        params[AGE_RANGE_QUESTION_ID] = age_range

    if lifestyle:
        params[LIFESTYLE_QUESTION_ID] = lifestyle

    # Build URL with properly encoded parameters
    base_url = "https://app.formbricks.com/s/cmf5homcz0p1kww010hzezjjp"
    query_string = urlencode(params, quote_via=quote)

    logger.info(f"🔗 Built params dict with {len(params)} fields")
    logger.info(f"🔗 Query string (first 300 chars): {query_string[:300]}")

    final_url = f"{base_url}?{query_string}"
    logger.info(f"🔗 Final URL length: {len(final_url)} chars")

    return final_url


def generate_html_report_from_results(quiz_output: Dict[str, Any],
                                      product_recommendations: List[Dict[str, Any]],
                                      timing_info: Dict[str, Any],
                                      email: str,
                                      token: Optional[str] = None,
                                      user_data: Optional[Dict[str, Any]] = None) -> str:
    """Generate HTML report from quiz results with optional token-based link and revision URL."""

    # Build product recommendations HTML
    products_html = ""
    for i, product in enumerate(product_recommendations, 1):
        products_html += f"""
        <div class="product-card">
            <h3>{i}. {product.get('title', 'Unknown Product')}</h3>
            <div class="relevance-score">Relevance: {product.get('relevance_score', 0):.0%}</div>
            <p><strong>Category:</strong> {product.get('category', 'Unknown')}</p>
            <p><strong>Why we recommend this:</strong> {product.get('rationale', 'No rationale provided')}</p>
            <p><strong>Key Ingredients:</strong> {', '.join(product.get('ingredient_highlights', []))}</p>
            <a href="{product.get('purchase_link', '#')}" class="purchase-btn" target="_blank">
                View Product Details
            </a>
        </div>
        """

    # Build recommendations HTML
    recommendations_html = ""
    for advice in quiz_output.get("general_recommendations", []):
        recommendations_html += f"<li>{advice}</li>\n"

    lifestyle_html = ""
    for suggestion in quiz_output.get("lifestyle_suggestions", []):
        lifestyle_html += f"<li>{suggestion}</li>\n"

    educational_html = ""
    for content in quiz_output.get("educational_content", []):
        educational_html += f"<li>{content}</li>\n"

    consultation_warning = ""
    if quiz_output.get("consultation_recommended"):
        consultation_warning = """
        <div class="warning-box">
            <h3>⚠️ Professional Consultation Recommended</h3>
            <p>Based on your responses, we recommend consulting with a healthcare professional for additional guidance and personalized care.</p>
        </div>
        """

    # Generate revision URL if user data is provided
    revision_button_html = ""
    if user_data:
        logger.info(f"🔧 Generating prefill URL with user_data: {user_data}")
        revision_url = generate_prefilled_form_url(
            email=user_data.get("email") or email,  # Ensure we have email
            health_issue=user_data.get("health_issue") or "",
            primary_area=user_data.get("primary_area"),
            severity=user_data.get("severity", 5),
            tried_already=user_data.get("tried_already"),
            age_range=user_data.get("age_range"),
            lifestyle=user_data.get("lifestyle")
        )
        logger.info(f"✅ Generated prefill URL: {revision_url[:200]}...")
        revision_button_html = f"""
        <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <p style="margin-bottom: 15px; color: #666; font-size: 16px;">
                Want to explore different recommendations?
            </p>
            <a href="{revision_url}"
               style="display: inline-block; padding: 15px 30px;
                      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; text-decoration: none; border-radius: 8px;
                      font-weight: 600; font-size: 16px; transition: transform 0.2s;">
                🔄 Revise My Answers & Get Updated Recommendations
            </a>
            <p style="margin-top: 10px; color: #999; font-size: 14px;">
                Your previous answers will be pre-filled for easy editing
            </p>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Health Quiz Results - Rogue Herbalist</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
            }}
            .section {{
                background: white;
                padding: 25px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h2 {{
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            h3 {{
                color: #555;
                margin-top: 20px;
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 12px;
            }}
            .product-card {{
                background: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }}
            .product-card h3 {{
                margin-top: 0;
                color: #333;
            }}
            .relevance-score {{
                background: #28a745;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 10px;
            }}
            .purchase-btn {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: 600;
                transition: transform 0.2s;
            }}
            .purchase-btn:hover {{
                transform: translateY(-2px);
            }}
            .warning-box {{
                background: #fff3cd;
                border: 2px solid #ffc107;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .warning-box h3 {{
                color: #856404;
                margin-top: 0;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 14px;
            }}
            .confidence-badge {{
                background: #e9ecef;
                padding: 8px 16px;
                border-radius: 20px;
                display: inline-block;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌿 Your Personalized Health Recommendations</h1>
            <p>From Rogue Herbalist</p>
        </div>

        {consultation_warning}

        <div class="section">
            <h2>General Health Recommendations</h2>
            <ul>
                {recommendations_html}
            </ul>
            <div class="confidence-badge">
                Confidence Level: {quiz_output.get('confidence_score', 0):.0%}
            </div>
        </div>

        <div class="section">
            <h2>Lifestyle Suggestions</h2>
            <ul>
                {lifestyle_html}
            </ul>
        </div>

        <div class="section">
            <h2>Recommended Products for You</h2>
            <p>Based on your health needs, we've selected {len(product_recommendations)} products that may help:</p>
            {products_html}
        </div>

        <div class="section">
            <h2>Learn More</h2>
            <ul>
                {educational_html}
            </ul>
        </div>

        {revision_button_html}

        <div class="footer">
            <p>These recommendations are for educational purposes only and are not medical advice.</p>
            <p>Always consult with a healthcare professional before starting any new health regimen.</p>
            <p><small>Results generated in {timing_info.get('total_duration_seconds', 0):.1f} seconds</small></p>
            {f'<p style="margin-top: 15px;"><a href="https://ic-ml-production.up.railway.app/results/{token}" style="color: #667eea; text-decoration: none; font-weight: 600;">View results online →</a></p>' if token else ''}
        </div>
    </body>
    </html>
    """

    return html_template


# Health Quiz endpoints
@app.post("/api/v1/health-quiz/{client_id}", response_model=HealthQuizResponse)
async def process_health_quiz(
    client_id: str,
    request: HealthQuizRequest,
    background_tasks: BackgroundTasks,
    client_info: Dict[str, Any] = Depends(auth.authenticate_client)
):
    """Process health quiz for a specific client."""

    # Verify client ID matches authenticated client
    if client_info["client_id"] != client_id:
        raise HTTPException(
            status_code=403,
            detail="Client ID mismatch"
        )

    # Check use case access
    auth.check_use_case_access(client_info, "health_quiz")

    start_time = datetime.now()

    try:
        # Convert request to input format
        input_data = request.dict(exclude_none=True)

        # Execute use case
        result = await use_case_manager.execute_use_case(
            client_id=client_id,
            use_case_name="health_quiz",
            input_data=input_data
        )

        # Log usage in background
        background_tasks.add_task(
            log_api_usage,
            client_id=client_id,
            use_case="health_quiz",
            result=result,
            request_data=input_data
        )

        return HealthQuizResponse(
            success=result.success,
            data=result.data if result.success else None,
            error=result.metadata.get("error") if not result.success else None,
            processing_time=result.processing_time,
            timestamp=result.timestamp.isoformat(),
            metadata=result.metadata
        )

    except Exception as e:
        logger.error(f"Health quiz error for client {client_id}: {str(e)}")
        processing_time = (datetime.now() - start_time).total_seconds()

        return HealthQuizResponse(
            success=False,
            error=f"Internal server error: {str(e)}",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            metadata={"error_type": type(e).__name__}
        )


# Product Classification endpoints
@app.post("/api/v1/product-classification/{client_id}", response_model=ProductClassificationResponse)
async def process_product_classification(
    client_id: str,
    request: ProductClassificationRequest,
    background_tasks: BackgroundTasks,
    client_info: Dict[str, Any] = Depends(auth.authenticate_client)
):
    """Process product classification for a specific client."""

    # Verify client ID matches authenticated client
    if client_info["client_id"] != client_id:
        raise HTTPException(
            status_code=403,
            detail="Client ID mismatch"
        )

    # Check use case access
    auth.check_use_case_access(client_info, "product_classification")

    start_time = datetime.now()

    try:
        # Convert request to input format
        input_data = {
            "products": request.products,
            "batch_size": request.batch_size,
            "model_override": request.model_override
        }

        # Execute use case
        result = await use_case_manager.execute_use_case(
            client_id=client_id,
            use_case_name="product_classification",
            input_data=input_data
        )

        # Log usage in background
        background_tasks.add_task(
            log_api_usage,
            client_id=client_id,
            use_case="product_classification",
            result=result,
            request_data=input_data
        )

        return ProductClassificationResponse(
            success=result.success,
            data=result.data if result.success else None,
            error=result.metadata.get("error") if not result.success else None,
            processing_time=result.processing_time,
            timestamp=result.timestamp.isoformat(),
            metadata=result.metadata,
            run_id=result.metadata.get("run_id")
        )

    except Exception as e:
        logger.error(f"Product classification error for client {client_id}: {str(e)}")
        processing_time = (datetime.now() - start_time).total_seconds()

        return ProductClassificationResponse(
            success=False,
            error=f"Internal server error: {str(e)}",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            metadata={"error_type": type(e).__name__}
        )


# Usage statistics endpoints
@app.get("/api/v1/usage/{client_id}", response_model=UsageStatsResponse)
async def get_usage_stats(
    client_id: str,
    use_case: Optional[str] = None,
    period_days: int = 30,
    client_info: Dict[str, Any] = Depends(auth.authenticate_client)
):
    """Get usage statistics for a client."""

    # Verify client ID matches authenticated client
    if client_info["client_id"] != client_id:
        raise HTTPException(
            status_code=403,
            detail="Client ID mismatch"
        )

    # In production, this would query a usage database
    # For now, return mock data
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=period_days)

    return UsageStatsResponse(
        client_id=client_id,
        use_case=use_case or "all",
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        total_requests=42,
        total_cost_usd=0.15,
        token_usage={
            "prompt_tokens": 15420,
            "completion_tokens": 3240,
            "total_tokens": 18660
        },
        model_breakdown={
            "gpt4o_mini": {"requests": 30, "cost": 0.08},
            "sonnet": {"requests": 12, "cost": 0.07}
        }
    )


# Administrative endpoints
@app.get("/api/v1/admin/clients")
async def list_clients():
    """List all clients (admin only)."""
    # In production, this would require admin authentication
    return {"clients": list(auth.client_tokens.keys())}


@app.get("/api/v1/admin/use-cases")
async def list_use_cases():
    """List all available use cases."""
    return {"use_cases": use_case_registry.list_use_cases()}


# Background tasks
async def log_api_usage(client_id: str, use_case: str, result: Any, request_data: Dict[str, Any]):
    """Log API usage for billing and analytics."""
    usage_record = {
        "client_id": client_id,
        "use_case": use_case,
        "timestamp": datetime.now().isoformat(),
        "success": result.success,
        "processing_time": result.processing_time,
        "metadata": result.metadata,
        "request_size": len(str(request_data))
    }

    # In production, this would write to a database
    logger.info(f"API Usage: {usage_record}")


# Rate limiting middleware (placeholder)
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Rate limiting middleware."""
    # In production, implement proper rate limiting
    # For now, just pass through
    response = await call_next(request)
    return response


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "web_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )