import pandas as pd

df = pd.read_csv("data/btcidr_3tahun.csv")

df["Time"] = pd.to_numeric(df["Time"])
df["Volume"] = pd.to_numeric(df["Volume"])

zero = df[df["Volume"] == 0].copy()

zero["Tanggal"] = pd.to_datetime(
    zero["Time"], unit="s", utc=True
)

print("JUMLAH CANDLE VOLUME NOL:", len(zero))

print("\n10 DATA PERTAMA:")
print(zero[["Tanggal", "Open", "High", "Low", "Close", "Volume"]].head(10))

print("\nRENTANG TANGGAL:")
print("Pertama:", zero["Tanggal"].min())
print("Terakhir:", zero["Tanggal"].max())

print("\nJUMLAH CANDLE VOLUME NOL PER TAHUN:")
print(zero.groupby(zero["Tanggal"].dt.year).size())