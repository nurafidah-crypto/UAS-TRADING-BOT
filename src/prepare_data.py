import pandas as pd

INPUT_FILE = "data/btcidr_3tahun.csv"
OUTPUT_FILE = "data/btcidr_clean.csv"

df = pd.read_csv(INPUT_FILE)

# Urutkan berdasarkan waktu
df = df.sort_values("Time").reset_index(drop=True)

# Pastikan kolom numerik
columns = ["Open", "High", "Low", "Close", "Volume"]

for col in columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Tandai candle yang memiliki volume
df["Valid_Trading"] = df["Volume"] > 0

# Simpan data
df.to_csv(OUTPUT_FILE, index=False)

print("PERSIAPAN DATA SELESAI")
print("======================")
print("Total candle:", len(df))
print("Candle volume positif:", df["Valid_Trading"].sum())
print("Candle volume nol:", (~df["Valid_Trading"]).sum())
print("File tersimpan:", OUTPUT_FILE)