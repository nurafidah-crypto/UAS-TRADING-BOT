import os
import time
import requests
import pandas as pd

from datetime import datetime, timezone

URL = "https://indodax.com/tradingview/history_v2"

PAIRS = ["BTC", "ETH", "XRP", "SOL", "PEPE", "HYPE"]

TIMEFRAME = "60"
OUTPUT_DIR = "data/forward_test/historical"

os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()


def update_pair(pair):
    symbol = pair + "IDR"

    output_file = os.path.join(
        OUTPUT_DIR,
        pair.lower() + "idr_3tahun.csv"
    )

    if not os.path.exists(output_file):
        print("FILE TIDAK DITEMUKAN:", output_file)
        return

    old_df = pd.read_csv(output_file)

    required_columns = [
        "Time", "Open", "High", "Low", "Close", "Volume"
    ]

    if not all(col in old_df.columns for col in required_columns):
        print("FORMAT FILE TIDAK SESUAI:", pair)
        return

    old_df["Time"] = pd.to_numeric(
        old_df["Time"], errors="coerce"
    )
    old_df = old_df.dropna(subset=["Time"])

    last_time = int(old_df["Time"].max())

    now = int(datetime.now(timezone.utc).timestamp())
    complete_end_time = (now // 3600) * 3600 - 1

    start_time = last_time + 3600

    print("\n================================")
    print("UPDATE:", symbol)
    print("Candle terakhir:", datetime.fromtimestamp(
        last_time, timezone.utc
    ))

    if start_time + 3600 > complete_end_time:
        print("Belum ada candle baru yang selesai.")
        return

    params = {
        "symbol": symbol,
        "tf": TIMEFRAME,
        "from": start_time,
        "to": complete_end_time
    }

    try:
        response = session.get(
            URL,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list) or not data:
            print("Tidak ada candle baru.")
            return

        new_df = pd.DataFrame(data)

        if not all(col in new_df.columns for col in required_columns):
            print("FORMAT DATA API TIDAK SESUAI:", pair)
            return

        new_df = new_df[required_columns].copy()

        for col in required_columns:
            new_df[col] = pd.to_numeric(
                new_df[col], errors="coerce"
            )

        new_df = new_df.dropna(subset=required_columns)

        new_df = new_df[
            (new_df["Time"] > last_time) &
            (new_df["Time"] + 3600 <= now)
        ]

        if new_df.empty:
            print("Tidak ada candle baru yang valid.")
            return

        combined = pd.concat(
            [old_df, new_df],
            ignore_index=True
        )

        combined = combined.drop_duplicates(
            subset="Time",
            keep="last"
        )

        combined = combined.sort_values("Time")

        combined.to_csv(output_file, index=False)

        print("Candle baru:", len(new_df))
        print("Total candle:", len(combined))
        print("Candle terbaru:", datetime.fromtimestamp(
            int(combined["Time"].max()), timezone.utc
        ))
        print("UPDATE BERHASIL:", pair)

    except Exception as error:
        print("UPDATE GAGAL:", pair, error)


if __name__ == "__main__":
    print("UPDATE DATA FORWARD TEST")
    print("Waktu UTC:", datetime.now(timezone.utc))

    for pair in PAIRS:
        update_pair(pair)
        time.sleep(0.4)

    print("\nPROSES UPDATE SELESAI")