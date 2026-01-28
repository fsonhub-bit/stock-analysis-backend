from pydantic import BaseModel
from datetime import datetime

class AnalysisResult(BaseModel):
    ticker: str
    current_price: float
    rsi: float
    signal: str
    timestamp: datetime
