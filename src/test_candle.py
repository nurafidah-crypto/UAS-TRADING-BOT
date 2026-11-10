
import requests
import time
import pandas as pd

URL = "https://indodax.com/tradingview/history_v2"

# Ambil data 7 hari terakhir
end_time = int(time.time())
start_time = end_time - (7 * 24 * 60 * 60)

params = {
    "symbol": "BTCIDR",
    "tf": "60",
    "from": start_time,
    "to": end_time
}

try:
    response = requests.get(URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data:
        df = pd.DataFrame(data)

        print("BERHASIL MENGAMBIL DATA CANDLESTICK!")
        print("\n5 DATA PERTAMA:")
        print(df.head())

        print("\nJUMLAH CANDLE:", len(df))

        # Simpan data
        df.to_csv("data/btcidr_7hari.csv", index=False)

        print("\nData berhasil disimpan di data/btcidr_7hari.csv")

    else:
        print("Data candle kosong.")

except Exception as e:
    print("Terjadi kesalahan:", e)
