import pandas as pd

INITIAL_CAPITAL = 100_000_000
FEE_RATE = 0.003

df = pd.read_csv("data/btcidr_indicators.csv")
trades = pd.read_csv("data/backtest_trades_revised.csv")
equity = pd.read_csv("data/equity_curve_revised.csv")

# Metrik strategi
equity_values = [INITIAL_CAPITAL] + equity["Equity"].tolist()

equity_series = pd.Series(equity_values)

peak = equity_series.cummax()
drawdown = (equity_series - peak) / peak * 100
max_drawdown = drawdown.min()

elapsed_days = (
    df.iloc[-1]["Time"] - df.iloc[1]["Time"]
) / 86400

final_equity = equity_values[-1]

cagr = (
    (final_equity / INITIAL_CAPITAL) ** (365 / elapsed_days) - 1
) * 100

wins = trades[trades["Profit_Loss"] > 0]
losses = trades[trades["Profit_Loss"] < 0]

avg_win = wins["Profit_Loss"].mean() if len(wins) else 0
avg_loss = losses["Profit_Loss"].mean() if len(losses) else 0

total_fees = (
    trades["Entry_Cost"].sum() * FEE_RATE
    + trades["Exit_Revenue"].sum() * FEE_RATE / (1 - FEE_RATE)
)

# Benchmark buy-and-hold
start_price = df.iloc[1]["Open"]
end_price = df.iloc[-1]["Close"]

btc_quantity = INITIAL_CAPITAL * (1 - FEE_RATE) / start_price
benchmark_final = btc_quantity * end_price * (1 - FEE_RATE)

benchmark_return = (
    benchmark_final / INITIAL_CAPITAL - 1
) * 100

print("EVALUASI BACKTEST")
print("=================")
print("CAGR strategi:", round(cagr, 2), "%")
print("Maximum drawdown:", round(max_drawdown, 2), "%")
print("Rata-rata profit per transaksi: Rp", round(avg_win))
print("Rata-rata loss per transaksi: Rp", round(avg_loss))
print("Estimasi total fee: Rp", round(total_fees))

print("\nBENCHMARK BTC BUY AND HOLD")
print("=========================")
print("Harga awal BTC:", round(start_price))
print("Harga akhir BTC:", round(end_price))
print("Nilai akhir benchmark: Rp", round(benchmark_final))
print("Return benchmark:", round(benchmark_return, 2), "%")