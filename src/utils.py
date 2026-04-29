from datetime import datetime

MONTHS_PT = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr",
    5: "mai", 6: "jun", 7: "jul", 8: "ago",
    9: "set", 10: "out", 11: "nov", 12: "dez"
}

def get_current_date() -> str:
    now = datetime.now()
    month_pt = MONTHS_PT[now.month]
    return f"{month_pt}/{now.year}"