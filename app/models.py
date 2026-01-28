from pydantic import BaseModel
from datetime import datetime

class AnalysisResult(BaseModel):
    ticker: str
    current_price: float
    rsi: float
    atr: float
    target_price: float
    upside_ratio: float
    signal: str
    reason: str
    timestamp: datetime
