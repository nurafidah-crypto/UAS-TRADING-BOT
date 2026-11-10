import pandas as pd

INPUT_FILE = "data/btcidr_clean.csv"
OUTPUT_FILE = "data/btcidr_indicators.csv"

df = pd.read_csv(INPUT_FILE)

# Hitung EMA
df["EMA_20"] = df["Close"].ewm(
    span=20, adjust=False
).mean()

df["EMA_50"] = df["Close"].ewm(
    span=50, adjust=False
).mean()

# Hitung RSI 14
delta = df["Close"].diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.ewm(
    alpha=1/14, adjust=False, min_periods=14
).mean()

avg_loss = loss.ewm(
    alpha=1/14, adjust=False, min_periods=14
).mean()

rs = avg_gain / avg_loss

df["RSI_14"] = 100 - (100 / (1 + rs))

# Tandai kondisi indikator
df["Buy_Signal"] = (
    (df["EMA_20"] > df["EMA_50"]) &
    (df["RSI_14"] > 50) &
    (df["RSI_14"] < 70) &
    (df["Valid_Trading"] == True)
)

df.to_csv(OUTPUT_FILE, index=False)

print("INDIKATOR BERHASIL DIBUAT")
print("=========================")
print("Total candle:", len(df))
print("EMA 20 selesai")
print("EMA 50 selesai")
print("RSI 14 selesai")
print("Jumlah sinyal beli:", df["Buy_Signal"].sum())
print("File:", OUTPUT_FILE)

print("\n5 DATA TERAKHIR:")
print(df[[
    "Close", "EMA_20", "EMA_50",
    "RSI_14", "Buy_Signal"
]].tail())