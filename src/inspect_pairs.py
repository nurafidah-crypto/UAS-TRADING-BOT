
import pandas as pd
from indodax import get_ticker

tickers = get_ticker()

if not tickers:
    print("Gagal mengambil data ticker Indodax.")
    raise SystemExit

results = []

for pair, data in tickers.items():
    if not pair.upper().endswith("_IDR"):
        continue

    try:
        volume_idr = float(data.get("vol_idr", 0) or 0)
        last_price = float(data.get("last", 0) or 0)
        best_bid = float(data.get("buy", 0) or 0)
        best_ask = float(data.get("sell", 0) or 0)

        midpoint = (best_bid + best_ask) / 2 if best_bid and best_ask else 0

        spread_percent = (
            (best_ask - best_bid) / midpoint * 100
            if midpoint > 0 else None
        )

        results.append({
            "Pair": pair.upper(),
            "Volume_IDR": volume_idr,
            "Last_Price": last_price,
            "Best_Bid": best_bid,
            "Best_Ask": best_ask,
            "Spread_Percent": spread_percent
        })

    except (TypeError, ValueError):
        continue

df = pd.DataFrame(results)

if df.empty:
    print("Tidak ada pair IDR yang ditemukan.")
    raise SystemExit

df = df.sort_values("Volume_IDR", ascending=False)

df.to_csv("data/pair_liquidity_ranking.csv", index=False)

print("RANKING LIKUIDITAS PAIR IDR")
print("===========================")
print("Jumlah pair:", len(df))
print("\n20 PAIR DENGAN VOLUME TERBESAR:\n")

for _, row in df.head(20).iterrows():
    print(
        f"{row['Pair']:20} "
        f"Volume IDR: Rp{row['Volume_IDR']:,.0f} "
        f"Spread: {row['Spread_Percent']:.4f}%"
        if pd.notna(row["Spread_Percent"])
        else f"{row['Pair']:20} Volume IDR: Rp{row['Volume_IDR']:,.0f}"
    )

print("\nFile tersimpan: data/pair_liquidity_ranking.csv")
