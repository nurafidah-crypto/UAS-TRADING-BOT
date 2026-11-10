import pandas as pd

FILE = "data/btcidr_3tahun.csv"

df = pd.read_csv(FILE)

print("PEMERIKSAAN DATA BTC/IDR")
print("========================")
print("Total candle:", len(df))
print("Candle duplikat:", df["Time"].duplicated().sum())

df = df.sort_values("Time")
selisih = df["Time"].diff()
missing = (selisih > 3600).sum()

print("Jumlah celah candle:", missing)

kolom = ["Open", "High", "Low", "Close", "Volume"]

for col in kolom:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("\nData kosong:")
print(df[kolom].isna().sum())

print("\nData bernilai nol:")
print((df[kolom] <= 0).sum())

invalid = (
    (df["High"] < df["Low"]) |
    (df["High"] < df["Open"]) |
    (df["High"] < df["Close"]) |
    (df["Low"] > df["Open"]) |
    (df["Low"] > df["Close"])
)

print("\nCandle OHLC tidak valid:", invalid.sum())
print("\nPEMERIKSAAN SELESAI")