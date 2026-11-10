
import os
import re
import subprocess
import sys
import shutil
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKTEST = os.path.join(BASE, "src", "backtest_multi.py")
OUTPUT = os.path.join(BASE, "data", "fee_sensitivity")
os.makedirs(OUTPUT, exist_ok=True)

with open(BACKTEST, "r", encoding="utf-8") as f:
    original = f.read()

pattern = r"(?m)^FEE_RATE\s*=\s*[\d.]+"
if not re.search(pattern, original):
    raise ValueError("Baris FEE_RATE tidak ditemukan.")

results = []

for fee in [0.001, 0.002, 0.003]:
    code = re.sub(
        pattern,
        f"FEE_RATE = {fee}",
        original,
        count=1
    )

    temp_file = os.path.join(
        BASE, "src", f"_backtest_fee_{int(fee*1000)}.py"
    )

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\nMenjalankan skenario fee {fee*100:.1f}%...")

    try:
        subprocess.run(
            [sys.executable, temp_file],
            cwd=BASE,
            check=True
        )

        metrics_file = os.path.join(
            BASE, "data", "backtest", "metrics_multi.csv"
        )

        metrics = pd.read_csv(metrics_file)
        metrics = dict(zip(metrics["Metric"], metrics["Value"]))

        results.append({
            "Fee_Per_Side_Percent": fee * 100,
            "Final_Equity": metrics["Final_Equity"],
            "Total_Return_Percent": metrics["Total_Return_Percent"],
            "Max_Drawdown_Percent": metrics["Max_Drawdown_Percent"],
            "Completed_Trades": metrics["Completed_Trades"],
            "Profit_Factor": metrics["Profit_Factor"]
        })

        shutil.copy(
            metrics_file,
            os.path.join(OUTPUT, f"metrics_fee_{fee*100:.1f}pct.csv")
        )

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

result = pd.DataFrame(results)
result.to_csv(
    os.path.join(OUTPUT, "fee_sensitivity_summary.csv"),
    index=False
)

print("\n========== PERBANDINGAN FEE ==========")
print(result.to_string(index=False))
print("\nHasil tersimpan di:", OUTPUT)
