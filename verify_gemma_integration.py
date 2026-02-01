
import sys
import os
# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.macro import macro_analyzer
from app.config import config

def test_gemma_analysis():
    print("Testing Gemma 3 Analysis via MacroAnalyzer...")
    
    ticker = "7203.T"
    profile = "トヨタ自動車。世界最大級の自動車メーカー。HV、EV、FCV全方位戦略。"
    finance = """
    2023/03 | 売上高: 37,154,298 | 営業益: 2,725,025 | 純利益: 2,451,318
    2024/03 | 売上高: 45,095,325 | 営業益: 5,352,934 | 純利益: 4,944,933
    """
    
    print(f"Analyzing {ticker}...")
    try:
        summary = macro_analyzer.analyze_individual_stock(ticker, profile, finance)
        print("-" * 50)
        print("RESULT:")
        print(summary)
        print("-" * 50)
        
        if "AI機能が無効" in summary or "AI分析エラー" in summary:
            print("❌ Analysis Failed")
            return False
        
        if len(summary) > 0:
            print("✅ Analysis Success")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_gemma_analysis()
