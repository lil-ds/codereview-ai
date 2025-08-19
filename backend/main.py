# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.models.analyzer import PythonCodeAnalyzer

app = FastAPI(title="CodeReview-AI", version="0.1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Added Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class CodeSubmission(BaseModel):
    code: str
    filename: str = "code.py"

class AnalysisResponse(BaseModel):
    quality_score: float
    issues: list
    total_issues: int
    lines_of_code: int
    filename: str

# Initialize analyzer
analyzer = PythonCodeAnalyzer()

@app.get("/")
async def root():
    return {
        "message": "CodeReview-AI API is running!",
        "version": "0.1.0",
        "endpoints": {
            "analyze": "/analyze",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CodeReview-AI"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_code(submission: CodeSubmission):
    """
    Analyze Python code and return quality score and issues
    """
    if not submission.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        # Analyze the code
        analysis_result = analyzer.analyze_code(submission.code)
        
        # Return structured response
        return AnalysisResponse(
            quality_score=analysis_result["quality_score"],
            issues=analysis_result["issues"],
            total_issues=analysis_result["total_issues"],
            lines_of_code=analysis_result["lines_of_code"],
            filename=submission.filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analyze/demo")
async def demo_analysis():
    """
    Demo endpoint with sample code analysis
    """
    sample_code = '''
def calculateTotal(items):
    total = 0
    for item in items:
        if item.price > 0 and item.quantity > 0 and item.discount >= 0 and item.tax_rate >= 0:
            subtotal = item.price * item.quantity
            discount_amount = subtotal * item.discount
            tax_amount = (subtotal - discount_amount) * item.tax_rate
            total += subtotal - discount_amount + tax_amount
    return total

class userAccount:
    def __init__(self, name):
        self.name = name
        self.balance = 0
'''
    
    analysis_result = analyzer.analyze_code(sample_code)
    return {
        "sample_code": sample_code,
        "analysis": analysis_result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)