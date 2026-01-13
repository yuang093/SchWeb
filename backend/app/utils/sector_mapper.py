from typing import Dict

# 預定義常見股票與 ETF 的 GICS 行業分類
SYMBOL_SECTOR_MAP = {
    # Information Technology
    "AAPL": "Information Technology",
    "MSFT": "Information Technology",
    "NVDA": "Information Technology",
    "AVGO": "Information Technology",
    "ORCL": "Information Technology",
    "ADBE": "Information Technology",
    "CRM": "Information Technology",
    "AMD": "Information Technology",
    "QCOM": "Information Technology",
    "INTC": "Information Technology",
    "CSCO": "Information Technology",
    "AMAT": "Information Technology",
    "TXN": "Information Technology",
    "MU": "Information Technology",
    "IBM": "Information Technology",
    "NOW": "Information Technology",
    "LRCX": "Information Technology",
    "KLAC": "Information Technology",
    "PANW": "Information Technology",
    "SNPS": "Information Technology",
    "CDNS": "Information Technology",
    
    # Communication Services
    "GOOGL": "Communication Services",
    "GOOG": "Communication Services",
    "META": "Communication Services",
    "NFLX": "Communication Services",
    "DIS": "Communication Services",
    "TMUS": "Communication Services",
    "VZ": "Communication Services",
    "T": "Communication Services",
    "CHTR": "Communication Services",
    "CMCSA": "Communication Services",
    
    # Consumer Discretionary
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "HD": "Consumer Discretionary",
    "MCD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary",
    "LOW": "Consumer Discretionary",
    "SBUX": "Consumer Discretionary",
    "BKNG": "Consumer Discretionary",
    "TJX": "Consumer Discretionary",
    "ORLY": "Consumer Discretionary",
    "LULU": "Consumer Discretionary",
    "TSM": "Information Technology", # 台積電在美股也算 IT
    
    # Financials
    "BRK.B": "Financials",
    "BRK.A": "Financials",
    "JPM": "Financials",
    "V": "Financials",
    "MA": "Financials",
    "BAC": "Financials",
    "MS": "Financials",
    "WFC": "Financials",
    "GS": "Financials",
    "AXP": "Financials",
    "SCHW": "Financials",
    "C": "Financials",
    "BLK": "Financials",
    "SPGI": "Financials",
    "CB": "Financials",
    "PGR": "Financials",
    "SCHD": "Financials", # ETF fallback
    
    # Healthcare
    "LLY": "Health Care",
    "UNH": "Health Care",
    "JNJ": "Health Care",
    "ABBV": "Health Care",
    "MRK": "Health Care",
    "TMO": "Health Care",
    "AMGN": "Health Care",
    "ISRG": "Health Care",
    "PFE": "Health Care",
    "ABT": "Health Care",
    "BMY": "Health Care",
    "CVS": "Health Care",
    "ELV": "Health Care",
    "CI": "Health Care",
    "GILD": "Health Care",
    "VRTX": "Health Care",
    "REGN": "Health Care",
    
    # Consumer Staples
    "PG": "Consumer Staples",
    "COST": "Consumer Staples",
    "KO": "Consumer Staples",
    "PEP": "Consumer Staples",
    "WMT": "Consumer Staples",
    "PM": "Consumer Staples",
    "TGT": "Consumer Staples",
    "EL": "Consumer Staples",
    "MO": "Consumer Staples",
    "CL": "Consumer Staples",
    
    # Energy
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "SLB": "Energy",
    "EOG": "Energy",
    "MPC": "Energy",
    "PSX": "Energy",
    "VLO": "Energy",
    
    # Industrials
    "CAT": "Industrials",
    "GE": "Industrials",
    "UNP": "Industrials",
    "HON": "Industrials",
    "RTX": "Industrials",
    "BA": "Industrials",
    "LMT": "Industrials",
    "DE": "Industrials",
    "UPS": "Industrials",
    "ADP": "Industrials",
    "FDX": "Industrials",
    "MMM": "Industrials",
    
    # Utilities
    "NEE": "Utilities",
    "DUK": "Utilities",
    "SO": "Utilities",
    "D": "Utilities",
    "AEP": "Utilities",
    "SRE": "Utilities",
    
    # Materials
    "LIN": "Materials",
    "APD": "Materials",
    "SHW": "Materials",
    "FCX": "Materials",
    "ECL": "Materials",
    
    # Real Estate
    "PLD": "Real Estate",
    "AMT": "Real Estate",
    "EQIX": "Real Estate",
    "CCI": "Real Estate",
    "DRE": "Real Estate",
    
    # ETFs (General fallback)
    "SPY": "ETFs",
    "QQQ": "ETFs",
    "VOO": "ETFs",
    "IVV": "ETFs",
    "VTI": "ETFs",
    "IWM": "ETFs",
    "IWY": "ETFs",
    "SCHD": "ETFs",
}

def get_sector(symbol: str, asset_type: str = "EQUITY") -> str:
    """
    根據 Symbol 與資產類型獲取行業分類
    """
    symbol = symbol.upper().replace("/", ".")
    
    if asset_type == "OPTION":
        return "Options"
    
    if "CASH" in asset_type or symbol in ["$CASH", "CASH"]:
        return "Cash"
        
    # 優先從對照表找
    if symbol in SYMBOL_SECTOR_MAP:
        return SYMBOL_SECTOR_MAP[symbol]
        
    # 如果是 ETF 結尾或常見 ETF 關鍵字
    if any(keyword in symbol for keyword in ["ETF", "FUND", "INDEX"]):
        return "ETFs"
        
    return "Other"
