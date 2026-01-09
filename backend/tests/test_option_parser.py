
import re
from typing import Optional

def _parse_option_expiration(symbol: str) -> Optional[str]:
    try:
        # 匹配 Symbol + YYMMDD + C/P + Strike
        # 範例: NVDA 261218C00200000
        match = re.search(r"([A-Z]+)\s*(\d{2})(\d{2})(\d{2})([CP])(\d+)", symbol)
        if match:
            yy = match.group(2)
            mm = match.group(3)
            dd = match.group(4)
            return f"{yy}/{mm}/{dd}"
    except Exception:
        pass
    return None

def test_parse():
    test_cases = [
        ("NVDA 261218C00200000", "26/12/18"),
        ("AAPL  250117P00150000", "25/01/17"),
        ("TSLA240621C00800000", "24/06/21"),
        ("INVALID_SYMBOL", None)
    ]
    
    for sym, expected in test_cases:
        result = _parse_option_expiration(sym)
        print(f"Symbol: {sym:25} Expected: {str(expected):10} Got: {str(result):10} {'✅' if result == expected else '❌'}")

if __name__ == "__main__":
    test_parse()
