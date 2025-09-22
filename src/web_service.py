"""
Web Service API for Multi-Use Case LLM Platform

Provides REST API endpoints for health quiz and product classification use cases
with real-time processing, client authentication, and usage tracking.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import uvicorn
from datetime import datetime
import logging
import asyncio

from use_case_framework import UseCaseManager, use_case_registry
from health_quiz_use_case import HealthQuizInput, HealthQuizOutput


# API Models
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
logger = logging.getLogger(__name__)


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
    return {
        "success": False,
        "error": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(exc)}")
    return {
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "web_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )