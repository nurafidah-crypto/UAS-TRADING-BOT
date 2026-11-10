
import os
import time
import requests
import pandas as pd

from datetime import datetime, timedelta, timezone

URL = "https://indodax.com/tradingview/history_v2"

PAIRS = [
    "BTC",
    "XRP",
    "PEPE",
    "HYPE",
    "ETH",
    "SOL"
]

TIMEFRAME = "60"  # 1 jam
DAYS = 3 * 365

OUTPUT_DIR = "data/historical_3y"
os.makedirs(OUTPUT_DIR, exist_ok=True)

now = datetime.now(timezone.utc)
end_time = int(now.timestamp())
start_time = int(
    (now - timedelta(days=DAYS)).timestamp()
)

# Hanya gunakan candle 1 jam yang sudah selesai.
complete_end_time = (end_time // 3600) * 3600 - 1

session = requests.Session()


def download_pair(pair):

    symbol = pair + "IDR"
    output_file = os.path.join(
        OUTPUT_DIR,
        pair.lower() + "idr_3tahun.csv"
    )

    cursor = complete_end_time
    all_data = []

    print("\n===================================")
    print("DOWNLOAD:", pair + "/IDR")
    print("===================================")

    while cursor > start_time:

        params = {
            "symbol": symbol,
            "tf": TIMEFRAME,
            "from": start_time,
            "to": cursor
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
                print("Tidak ada data tambahan.")
                break

            df = pd.DataFrame(data)

            if "Time" not in df.columns:
                print("Format data tidak sesuai.")
                break

            df["Time"] = pd.to_numeric(
                df["Time"],
                errors="coerce"
            )

            df = df.dropna(subset=["Time"])

            if df.empty:
                print("Data waktu kosong.")
                break

            earliest = int(df["Time"].min())

            all_data.extend(df.to_dict("records"))

            print(
                "Candle:", len(df),
                "| Tanggal awal:",
                datetime.fromtimestamp(
                    earliest,
                    timezone.utc
                ).strftime("%Y-%m-%d %H:%M")
            )

            if earliest >= cursor:
                print("Pagination tidak bergerak. Berhenti.")
                break

            cursor = earliest - 1

            # Maksimal sekitar 2,5 request per detik.
            time.sleep(0.4)

        except Exception as e:
            print("ERROR:", pair, e)
            break

    if not all_data:
        print("GAGAL:", pair, "tidak ada data.")
        return

    result = pd.DataFrame(all_data)

    result["Time"] = pd.to_numeric(
        result["Time"],
        errors="coerce"
    )

    result = result.dropna(subset=["Time"])
    result = result.drop_duplicates(subset="Time")
    result = result.sort_values("Time")

    # Buang candle yang belum selesai.
    result = result[
        (result["Time"] >= start_time) &
        (result["Time"] + 3600 <= end_time)
    ]

    result.to_csv(output_file, index=False)

    print("\nSELESAI:", pair + "/IDR")
    print("Jumlah candle:", len(result))

    if not result.empty:
        print(
            "Tanggal pertama:",
            datetime.fromtimestamp(
                int(result["Time"].min()),
                timezone.utc
            )
        )
        print(
            "Tanggal terakhir:",
            datetime.fromtimestamp(
                int(result["Time"].max()),
                timezone.utc
            )
        )

    print("File:", output_file)


if __name__ == "__main__":

    print("DOWNLOAD HISTORI INDO DAX")
    print("Target: 6 pair, 3 tahun, timeframe 1 jam")
    print("Mulai:", datetime.now(timezone.utc))

    for pair in PAIRS:
        download_pair(pair)

    print("\n===================================")
    print("SEMUA PROSES DOWNLOAD SELESAI")
    print("===================================")
