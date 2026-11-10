
import os
import pandas as pd

INPUT_FILE = "data/orderbook_snapshots.csv"
OUTPUT_FILE = "data/orderbook_analysis.csv"


def analyze_orderbook():
    if not os.path.exists(INPUT_FILE):
        print("File snapshot tidak ditemukan.")
        return

    df = pd.read_csv(INPUT_FILE)

    required_columns = ["Timestamp", "Pair", "Side", "Price", "Amount"]

    if not all(col in df.columns for col in required_columns):
        print("Format kolom CSV tidak sesuai.")
        return

    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df.dropna(subset=["Price", "Amount"])

    results = []

    for (timestamp, pair), group in df.groupby(["Timestamp", "Pair"]):
        bids = group[group["Side"] == "BID"].sort_values(
            "Price", ascending=False
        )

        asks = group[group["Side"] == "ASK"].sort_values(
            "Price", ascending=True
        )

        if bids.empty or asks.empty:
            continue

        best_bid = bids.iloc[0]["Price"]
        best_ask = asks.iloc[0]["Price"]

        spread = best_ask - best_bid
        midpoint = (best_ask + best_bid) / 2
        spread_percent = spread / midpoint * 100

        bid_depth_5 = (bids.head(5)["Price"] * bids.head(5)["Amount"]).sum()
        ask_depth_5 = (asks.head(5)["Price"] * asks.head(5)["Amount"]).sum()

        bid_depth_10 = (bids.head(10)["Price"] * bids.head(10)["Amount"]).sum()
        ask_depth_10 = (asks.head(10)["Price"] * asks.head(10)["Amount"]).sum()

        results.append({
            "Timestamp": timestamp,
            "Pair": pair,
            "Best_Bid": best_bid,
            "Best_Ask": best_ask,
            "Spread_IDR": spread,
            "Spread_Percent": spread_percent,
            "Bid_Depth_5_IDR": bid_depth_5,
            "Ask_Depth_5_IDR": ask_depth_5,
            "Bid_Depth_10_IDR": bid_depth_10,
            "Ask_Depth_10_IDR": ask_depth_10
        })

    if not results:
        print("Belum ada snapshot yang dapat dianalisis.")
        return

    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False)

    print("ANALISIS ORDER BOOK BERHASIL")
    print("============================")
    print("Jumlah snapshot:", len(result_df))
    print("Pair:", ", ".join(result_df["Pair"].unique()))
    print("Rata-rata spread (%):", round(result_df["Spread_Percent"].mean(), 6))
    print("Spread terkecil (%):", round(result_df["Spread_Percent"].min(), 6))
    print("Spread terbesar (%):", round(result_df["Spread_Percent"].max(), 6))
    print("File hasil:", OUTPUT_FILE)


if __name__ == "__main__":
    analyze_orderbook()
