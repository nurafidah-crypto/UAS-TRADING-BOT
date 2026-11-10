
import requests
import pandas as pd
import time
from datetime import datetime, timedelta, timezone

URL = "https://indodax.com/tradingview/history_v2"

# Periode 3 tahun
end_time = int(datetime.now(timezone.utc).timestamp())
start_time = int(
    (datetime.now(timezone.utc) - timedelta(days=3*365)).timestamp()
)

cursor = end_time
all_data = []

print("MULAI DOWNLOAD DATA HISTORIS BTC/IDR")
print("Target: 3 tahun")
print("-----------------------------------")

while cursor > start_time:

    params = {
        "symbol": "BTCIDR",
        "tf": "60",
        "from": start_time,
        "to": cursor
    }

    try:
        response = requests.get(URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list) or not data:
            print("Tidak ada data tambahan.")
            break

        df = pd.DataFrame(data)

        if "Time" not in df.columns:
            print("Format data tidak sesuai.")
            break

        df["Time"] = pd.to_numeric(df["Time"])

        earliest = int(df["Time"].min())

        all_data.extend(data)

        print(
            "Berhasil mengambil:",
            len(data),
            "candle | Tanggal awal:",
            datetime.fromtimestamp(
                earliest, timezone.utc
            ).strftime("%Y-%m-%d %H:%M")
        )

        if earliest >= cursor:
            print("Tidak ada kemajuan pagination. Berhenti.")
            break

        cursor = earliest - 1

        time.sleep(0.4)

    except Exception as e:
        print("ERROR:", e)
        break


# Gabungkan dan bersihkan data
if all_data:

    df = pd.DataFrame(all_data)

    df["Time"] = pd.to_numeric(df["Time"])

    df = df.drop_duplicates(subset="Time")
    df = df.sort_values("Time")

    df = df[
        (df["Time"] >= start_time) &
        (df["Time"] <= end_time)
    ]

    df.to_csv("data/btcidr_3tahun.csv", index=False)

    print("\n-----------------------------------")
    print("DOWNLOAD SELESAI")
    print("Total candle:", len(df))
    print("Tanggal pertama:", datetime.fromtimestamp(
        int(df["Time"].min()), timezone.utc
    ))
    print("Tanggal terakhir:", datetime.fromtimestamp(
        int(df["Time"].max()), timezone.utc
    ))
    print("File: data/btcidr_3tahun.csv")

else:
    print("Download gagal: tidak ada data.")
