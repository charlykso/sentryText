from fastapi import APIRouter, Depends, HTTPException
from app.schemas import AuditorRequest, AuditorResponse
from app.routes.auth import get_current_user
from app.ml_engine.classifier import predict_comment

router = APIRouter(prefix="/auditor", tags=["External Text Auditor"])

@router.post("/analyze", response_model=AuditorResponse)
def analyze_external_text(req: AuditorRequest, current_actor: dict = Depends(get_current_user)):
    """
    Analyzes an external text snippet submitted via copy-paste.
    Evaluates both SVM and Logistic Regression models and returns raw confidence metrics.
    """
    text = req.Text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")
        
    # Analyze text using the ML engine
    verdict = predict_comment(text)
    return verdict
