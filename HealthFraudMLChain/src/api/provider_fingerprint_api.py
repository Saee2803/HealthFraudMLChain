"""
FastAPI endpoint for provider behavioral fingerprinting.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from features.provider_fingerprint import ProviderFingerprintGenerator

app = FastAPI(title="Provider Fingerprint API", version="1.0.0")


class FingerprintRequest(BaseModel):
    claims_path: str
    output_dir: str = "artifacts"


class FingerprintResponse(BaseModel):
    success: bool
    message: str
    parquet_path: str = None
    jsonl_path: str = None
    provider_count: int = None


@app.post("/fingerprint/compute", response_model=FingerprintResponse)
async def compute_fingerprints(request: FingerprintRequest):
    """
    Compute provider behavioral fingerprints from claims data.
    
    Args:
        request: FingerprintRequest containing claims_path and optional output_dir
        
    Returns:
        FingerprintResponse with results or error message
    """
    try:
        # Validate input file exists
        if not Path(request.claims_path).exists():
            raise HTTPException(
                status_code=400, 
                detail=f"Claims file not found: {request.claims_path}"
            )
        
        # Generate fingerprints
        generator = ProviderFingerprintGenerator()
        parquet_path, jsonl_path = generator.generate_fingerprints(
            request.claims_path, request.output_dir
        )
        
        # Count providers
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        provider_count = len(df)
        
        return FingerprintResponse(
            success=True,
            message=f"Successfully generated fingerprints for {provider_count} providers",
            parquet_path=parquet_path,
            jsonl_path=jsonl_path,
            provider_count=provider_count
        )
        
    except Exception as e:
        return FingerprintResponse(
            success=False,
            message=f"Error generating fingerprints: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "provider-fingerprint-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Provider Behavioral Fingerprinting API",
        "version": "1.0.0",
        "endpoints": {
            "compute": "POST /fingerprint/compute",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)