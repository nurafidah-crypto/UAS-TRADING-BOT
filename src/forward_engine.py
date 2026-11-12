
import os
import json
import csv
import tempfile
from datetime import datetime, timezone

import pandas as pd

from src.forward_config import (
    INITIAL_CAPITAL,
    FEE_RATE,
    MAX_POSITIONS,
    MAX_ALLOCATION,
    DAILY_LOSS_LIMIT_PERCENT,
    PAIR_RULES,
)
from src.forward_execution import simulate_buy, simulate_sell


# ============================================================
# PATH DAN KONFIGURASI
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INDICATOR_DIR = os.path.join(
    BASE_DIR, "data", "forward_test", "indicators"
)

STATE_FILE = os.path.join(
    BASE_DIR, "data", "forward_test", "state.json"
)

TRADE_LOG = os.path.join(
    BASE_DIR, "data", "forward_test", "trades.csv"
)

EVENT_LOG = os.path.join(
    BASE_DIR, "logs", "forward_engine.log"
)

PAIRS = sorted(PAIR_RULES.keys())

TRADE_COLUMNS = [
    "Event_ID",
    "Timestamp",
    "Pair",
    "Side",
    "Quantity",
    "Average_Price",
    "Gross_Value",
    "Fee",
    "Total_Cost",
    "Signal_Candle_Time",
    "Net_Proceeds",
    "Net_PnL",
    "Entry_Time",
    "Exit_Candle_Time",
]


# ============================================================
# BOOLEAN VALIDATION
# ============================================================

def parse_bool(value):

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    if isinstance(value, (int, float)):

        if value == 1:
            return True

        if value == 0:
            return False

    normalized = str(value).strip().lower()

    if normalized in ("true", "1", "yes"):
        return True

    if normalized in ("false", "0", "no", ""):
        return False

    raise ValueError(
        f"Nilai boolean tidak dikenal: {value!r}"
    )


# ============================================================
# STATE
# ============================================================

def load_state():

    if not os.path.exists(STATE_FILE):

        raise FileNotFoundError(
            "State tidak ditemukan. Engine tidak akan "
            "menginisialisasi ulang secara otomatis."
        )

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        state = json.load(file)

    if state.get("mode") != "DRY_RUN":

        raise RuntimeError(
            "Mode bukan DRY_RUN. Engine dihentikan."
        )

    required = [
        "cash",
        "positions",
        "last_processed_candle",
        "total_trades",
        "kill_switch",
    ]

    for key in required:

        if key not in state:

            raise ValueError(
                f"State tidak memiliki field: {key}"
            )

    if not isinstance(state["positions"], dict):

        raise ValueError(
            "Format positions pada state tidak valid."
        )

    if not isinstance(
        state["last_processed_candle"],
        dict
    ):

        raise ValueError(
            "Format last_processed_candle tidak valid."
        )

    state["cash"] = float(state["cash"])
    state["total_trades"] = int(state["total_trades"])

    state["kill_switch"] = parse_bool(
        state["kill_switch"]
    )

    if state["cash"] < 0:

        raise ValueError(
            "Cash pada state tidak boleh negatif."
        )

    state.setdefault("daily_date", None)
    state.setdefault("daily_start_equity", None)
    state.setdefault("processed_events", [])

    if not isinstance(state["processed_events"], list):

        raise ValueError(
            "Format processed_events tidak valid."
        )

    for pair in PAIRS:

        state["last_processed_candle"].setdefault(
            pair,
            0
        )

    return state


def save_state(state):

    directory = os.path.dirname(STATE_FILE)

    os.makedirs(
        directory,
        exist_ok=True
    )

    fd, temp_path = tempfile.mkstemp(
        dir=directory,
        suffix=".tmp"
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                indent=4
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temp_path,
            STATE_FILE
        )

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)


def log_event(message):

    os.makedirs(
        os.path.dirname(EVENT_LOG),
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    with open(
        EVENT_LOG,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            f"{timestamp} | {message}\n"
        )

    print(message)


# ============================================================
# EVENT IDEMPOTENCY
# ============================================================

def is_event_processed(state, event_id):

    return event_id in set(
        state.get("processed_events", [])
    )


def mark_event_processed(state, event_id):

    if is_event_processed(state, event_id):
        return

    state.setdefault(
        "processed_events",
        []
    )

    state["processed_events"].append(event_id)

    save_state(state)


# ============================================================
# MIGRASI DAN NORMALISASI CSV TRANSAKSI
# ============================================================

def normalize_legacy_trade_row(header, row):

    normalized = {
        column: ""
        for column in TRADE_COLUMNS
    }

    if len(row) == 12:

        mapping = [
            "Event_ID",
            "Timestamp",
            "Pair",
            "Side",
            "Quantity",
            "Average_Price",
            "Gross_Value",
            "Fee",
            "Net_Proceeds",
            "Net_PnL",
            "Entry_Time",
            "Exit_Candle_Time",
        ]

        for index, column in enumerate(mapping):
            normalized[column] = row[index]

        return normalized

    if len(row) == len(header):

        old_record = dict(
            zip(header, row)
        )

        for column in TRADE_COLUMNS:

            if column in old_record:
                normalized[column] = old_record[column]

        return normalized

    raise ValueError(
        "Jumlah kolom CSV lama tidak dikenali: "
        f"{len(row)} kolom."
    )


def normalize_existing_trade_log():

    if not os.path.exists(TRADE_LOG):
        return

    with open(
        TRADE_LOG,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        rows = list(csv.reader(file))

    if not rows:
        return

    header = rows[0]

    normalized_rows = []
    seen_events = set()

    for row_number, row in enumerate(rows[1:], start=2):

        if not row:
            continue

        normalized = normalize_legacy_trade_row(
            header,
            row
        )

        event_id = normalized["Event_ID"]

        if not event_id:

            raise ValueError(
                f"Event_ID kosong pada baris {row_number}."
            )

        if event_id in seen_events:
            continue

        seen_events.add(event_id)

        normalized_rows.append(normalized)

    fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(TRADE_LOG),
        suffix=".csv.tmp"
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=TRADE_COLUMNS,
                extrasaction="ignore"
            )

            writer.writeheader()

            writer.writerows(
                normalized_rows
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temp_path,
            TRADE_LOG
        )

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)


# ============================================================
# LOG TRANSAKSI
# ============================================================

def record_trade(record):

    os.makedirs(
        os.path.dirname(TRADE_LOG),
        exist_ok=True
    )

    if "Event_ID" not in record:

        raise ValueError(
            "Record transaksi tidak memiliki Event_ID."
        )

    if record.get("Side") not in ("BUY", "SELL"):

        raise ValueError(
            "Side transaksi harus BUY atau SELL."
        )

    normalize_existing_trade_log()

    event_id = str(record["Event_ID"])

    if os.path.exists(TRADE_LOG):

        existing = pd.read_csv(
            TRADE_LOG,
            dtype={"Event_ID": str}
        )

        if event_id in set(
            existing["Event_ID"].dropna()
        ):

            return False

    normalized_record = {
        column: record.get(column, "")
        for column in TRADE_COLUMNS
    }

    new_row = pd.DataFrame(
        [normalized_record],
        columns=TRADE_COLUMNS
    )

    new_row.to_csv(
        TRADE_LOG,
        mode="a",
        header=not os.path.exists(TRADE_LOG),
        index=False
    )

    return True


def persist_trade(state, record):

    event_id = record["Event_ID"]

    if is_event_processed(state, event_id):
        return False

    # Jika CSV sudah memiliki Event_ID yang sama,
    # record_trade tidak akan menambahkan duplikat.
    record_trade(record)

    state.setdefault(
        "processed_events",
        []
    )

    if not is_event_processed(state, event_id):

        state["processed_events"].append(event_id)

    # Simpan state setelah perubahan saldo dan posisi
    # dilakukan oleh process_new_candles().
    save_state(state)

    return True


# ============================================================
# DATA INDIKATOR
# ============================================================

def load_indicator_data():

    data = {}

    required = [
        "Time",
        "Close",
        "Valid_Trading",
        "EMA_20",
        "EMA_50",
        "RSI_14",
        "Buy_Signal",
    ]

    for pair in PAIRS:

        path = os.path.join(
            INDICATOR_DIR,
            f"{pair}_indicators.csv"
        )

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"Indikator tidak ditemukan: {path}"
            )

        df = pd.read_csv(path)

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:

            raise ValueError(
                f"Kolom indikator {pair} tidak lengkap: {missing}"
            )

        for column in [
            "Time",
            "Close",
            "EMA_20",
            "EMA_50",
            "RSI_14",
        ]:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        for column in [
            "Valid_Trading",
            "Buy_Signal",
        ]:

            try:

                df[column] = df[column].apply(
                    parse_bool
                )

            except ValueError as error:

                raise ValueError(
                    f"Boolean tidak valid pada {pair}, "
                    f"kolom {column}: {error}"
                ) from error

        df = df.dropna(
            subset=["Time"]
        )

        df["Time"] = df["Time"].astype("int64")

        df = df.sort_values("Time")

        df = df.drop_duplicates(
            "Time",
            keep="last"
        )

        df = df.set_index("Time")

        data[pair] = df

        log_event(
            f"Indikator {pair} dimuat: "
            f"{len(df)} candle, "
            f"{int(df['Buy_Signal'].sum())} sinyal BUY."
        )

    return data


# ============================================================
# EQUITY
# ============================================================

def calculate_equity(state, data, timestamp):

    equity = float(state["cash"])

    for pair, position in state["positions"].items():

        df = data.get(pair)

        if df is None or df.empty:
            continue

        available = df[df.index <= timestamp]

        if available.empty:
            continue

        close_price = float(
            available.iloc[-1]["Close"]
        )

        if not pd.notna(close_price) or close_price <= 0:
            continue

        estimated_value = (
            float(position["quantity"])
            * close_price
            * (1 - FEE_RATE)
        )

        equity += estimated_value

    return equity


# ============================================================
# DAILY LOSS LIMIT
# ============================================================

def initialize_daily_baseline(state, equity, timestamp):

    candle_date = datetime.fromtimestamp(
        int(timestamp),
        timezone.utc
    ).date().isoformat()

    if state.get("daily_date") != candle_date:

        state["daily_date"] = candle_date
        state["daily_start_equity"] = float(equity)

        log_event(
            f"Baseline equity harian {candle_date}: "
            f"Rp{equity:,.2f}"
        )


def check_daily_loss(state, equity):

    start_equity = float(
        state.get("daily_start_equity") or 0
    )

    if start_equity <= 0:

        state["kill_switch"] = True

        log_event(
            "KILL SWITCH: baseline equity tidak valid."
        )

        return False

    loss_fraction = (
        start_equity - float(equity)
    ) / start_equity

    if loss_fraction >= DAILY_LOSS_LIMIT_PERCENT:

        state["kill_switch"] = True

        log_event(
            "KILL SWITCH: kerugian harian mencapai "
            f"{loss_fraction * 100:.2f}%."
        )

        return False

    return not state["kill_switch"]


# ============================================================
# VALIDASI HASIL EKSEKUSI
# ============================================================

def validate_execution_result(result, pair, side):

    if not isinstance(result, dict):

        raise TypeError(
            f"Hasil {side} {pair} bukan dictionary."
        )

    if "ok" not in result:

        raise ValueError(
            f"Hasil {side} {pair} tidak memiliki status ok."
        )

    if result["ok"] is False:

        reason = str(
            result.get("reason") or "Alasan tidak diketahui."
        )

        retryable = result.get("retryable", False)

        if not isinstance(retryable, bool):

            raise ValueError(
                f"Status retryable {side} {pair} harus boolean."
            )

        return None, reason, retryable

    if result["ok"] is not True:

        raise ValueError(
            f"Status hasil {side} {pair} tidak valid."
        )

    order = result.get("order")

    if not isinstance(order, dict):

        raise ValueError(
            f"Hasil {side} {pair} tidak memiliki order valid."
        )

    required = [
        "pair",
        "side",
        "quantity",
        "average_price",
        "gross_value",
        "fee",
    ]

    for field in required:

        if field not in order:

            raise ValueError(
                f"Order {side} {pair} tidak memiliki {field}."
            )

    if order["pair"] != pair or order["side"] != side:

        raise ValueError(
            f"Identitas order tidak cocok: {pair} {side}."
        )

    for field in [
        "quantity",
        "average_price",
        "gross_value",
        "fee",
    ]:

        value = float(order[field])

        if not pd.notna(value) or value <= 0:

            raise ValueError(
                f"Nilai order {field} tidak valid."
            )

    if side == "BUY":

        if "total_cost" not in order:

            raise ValueError(
                "Order BUY tidak memiliki total_cost."
            )

        if float(order["total_cost"]) <= 0:

            raise ValueError(
                "Total cost BUY tidak valid."
            )

    if side == "SELL":

        if "net_proceeds" not in order:

            raise ValueError(
                "Order SELL tidak memiliki net_proceeds."
            )

        if float(order["net_proceeds"]) <= 0:

            raise ValueError(
                "Net proceeds SELL tidak valid."
            )

    return order, None, False


# ============================================================
# PEMROSESAN CANDLE BARU
# ============================================================

def process_new_candles():

    state = load_state()

    if state["kill_switch"]:

        log_event(
            "Engine berhenti: kill switch aktif."
        )

        return

    data = load_indicator_data()

    new_times = set()

    for pair, df in data.items():

        last_time = int(
            state["last_processed_candle"].get(
                pair,
                0
            )
        )

        for timestamp in df.index:

            if int(timestamp) > last_time:
                new_times.add(int(timestamp))

    if not new_times:

        log_event(
            "Belum ada candle baru untuk diproses."
        )

        return

    for timestamp in sorted(new_times):

        retryable_failure = False

        previous_rows = {}

        for pair, df in data.items():

            earlier = df[df.index < timestamp]

            if not earlier.empty:
                previous_rows[pair] = earlier.iloc[-1]

        # ----------------------------------------------------
        # BASELINE EQUITY HARIAN
        # ----------------------------------------------------

        equity_before = calculate_equity(
            state,
            data,
            timestamp
        )

        initialize_daily_baseline(
            state,
            equity_before,
            timestamp
        )

        if not check_daily_loss(
            state,
            equity_before
        ):

            save_state(state)
            break

        # ----------------------------------------------------
        # 1. SELL DAHULU
        # ----------------------------------------------------

        for pair in sorted(
            list(state["positions"].keys())
        ):

            df = data[pair]

            if timestamp not in df.index:
                continue

            previous = previous_rows.get(pair)

            if previous is None:
                continue

            should_sell = (
                float(previous["EMA_20"])
                <= float(previous["EMA_50"])
                or float(previous["RSI_14"]) < 45
            )

            if not should_sell:
                continue

            event_id = f"{timestamp}:{pair}:SELL"

            if is_event_processed(state, event_id):
                continue

            position = state["positions"][pair]

            raw_result = simulate_sell(
                pair,
                position["quantity"]
            )

            result, reason, retryable = validate_execution_result(
                raw_result,
                pair,
                "SELL"
            )

            if result is None:

                log_event(
                    f"SELL DITOLAK {pair}: {reason}"
                )

                if retryable:

                    retryable_failure = True

                else:

                    mark_event_processed(
                        state,
                        event_id
                    )

                    log_event(
                        f"SELL {pair} ditandai selesai "
                        "untuk candle ini karena penolakan permanen."
                    )

                continue

            if (
                result["quantity"] + 1e-15
                < float(position["quantity"])
            ):

                log_event(
                    f"SELL DITOLAK {pair}: "
                    "hasil kuantitas lebih kecil dari posisi. "
                    "Checkpoint ditahan."
                )

                retryable_failure = True
                continue

            net_pnl = (
                result["net_proceeds"]
                - float(position["total_buy_cost"])
            )

            record = {
                "Event_ID": event_id,
                "Timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "Pair": pair,
                "Side": "SELL",
                "Quantity": result["quantity"],
                "Average_Price": result["average_price"],
                "Gross_Value": result["gross_value"],
                "Fee": result["fee"],
                "Net_Proceeds": result["net_proceeds"],
                "Net_PnL": net_pnl,
                "Entry_Time": position["entry_time"],
                "Exit_Candle_Time": timestamp,
            }

            # Perbarui saldo dan posisi sebelum menyimpan transaksi.
            state["cash"] += result["net_proceeds"]
            state["total_trades"] += 1

            del state["positions"][pair]

            persist_trade(
                state,
                record
            )

            log_event(
                f"SIMULATED SELL {pair}: "
                f"quantity={result['quantity']}, "
                f"net={result['net_proceeds']:.2f}, "
                f"PnL={net_pnl:.2f}"
            )

        # ----------------------------------------------------
        # 2. BUY BERDASARKAN SINYAL CANDLE SEBELUMNYA
        # ----------------------------------------------------

        for pair in PAIRS:

            if pair in state["positions"]:
                continue

            if len(state["positions"]) >= MAX_POSITIONS:
                break

            df = data[pair]

            if timestamp not in df.index:
                continue

            previous = previous_rows.get(pair)
            current = df.loc[timestamp]

            if previous is None:
                continue

            if not previous["Buy_Signal"]:
                continue

            if not current["Valid_Trading"]:
                continue

            event_id = f"{timestamp}:{pair}:BUY"

            if is_event_processed(state, event_id):
                continue

            allocation = min(
                float(state["cash"]),
                INITIAL_CAPITAL * MAX_ALLOCATION
            )

            if allocation <= 0:
                continue

            raw_result = simulate_buy(
                pair,
                allocation
            )

            result, reason, retryable = validate_execution_result(
                raw_result,
                pair,
                "BUY"
            )

            if result is None:

                log_event(
                    f"BUY DITOLAK {pair}: {reason}"
                )

                if retryable:

                    retryable_failure = True

                else:

                    mark_event_processed(
                        state,
                        event_id
                    )

                    log_event(
                        f"BUY {pair} ditandai selesai "
                        "untuk candle ini karena penolakan permanen."
                    )

                continue

            if result["total_cost"] > float(state["cash"]):

                log_event(
                    f"BUY DITOLAK {pair}: cash tidak cukup."
                )

                mark_event_processed(
                    state,
                    event_id
                )

                continue

            record = {
                "Event_ID": event_id,
                "Timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "Pair": pair,
                "Side": "BUY",
                "Quantity": result["quantity"],
                "Average_Price": result["average_price"],
                "Gross_Value": result["gross_value"],
                "Fee": result["fee"],
                "Total_Cost": result["total_cost"],
                "Signal_Candle_Time": timestamp,
            }

            # Perbarui saldo dan posisi sebelum menyimpan transaksi.
            state["cash"] -= result["total_cost"]

            state["positions"][pair] = {
                "entry_time": timestamp,
                "buy_price": result["average_price"],
                "quantity": result["quantity"],
                "buy_fee": result["fee"],
                "total_buy_cost": result["total_cost"],
            }

            persist_trade(
                state,
                record
            )

            log_event(
                f"SIMULATED BUY {pair}: "
                f"quantity={result['quantity']}, "
                f"cost={result['total_cost']:.2f}"
            )

        # ----------------------------------------------------
        # 3. TAHAN CHECKPOINT JIKA ADA KEGAGALAN SEMENTARA
        # ----------------------------------------------------

        if retryable_failure:

            log_event(
                f"CANDLE {timestamp} BELUM DI-CHECKPOINT. "
                "Ada kegagalan sementara. "
                "Candle akan dicoba ulang pada siklus berikutnya."
            )

            save_state(state)
            break

        # ----------------------------------------------------
        # 4. UPDATE CHECKPOINT
        # ----------------------------------------------------

        for pair, df in data.items():

            if timestamp in df.index:

                state["last_processed_candle"][pair] = timestamp

        # ----------------------------------------------------
        # 5. CHECK EQUITY DAN DAILY LOSS LIMIT
        # ----------------------------------------------------

        equity_after = calculate_equity(
            state,
            data,
            timestamp
        )

        if not check_daily_loss(
            state,
            equity_after
        ):

            log_event(
                "Trading dihentikan oleh kill switch."
            )

            save_state(state)
            break

        save_state(state)

    save_state(state)

    latest_timestamp = max(new_times)

    final_equity = calculate_equity(
        state,
        data,
        latest_timestamp
    )

    log_event(
        f"Pemrosesan selesai. "
        f"Cash={state['cash']:.2f}, "
        f"Equity={final_equity:.2f}, "
        f"Posisi={len(state['positions'])}, "
        f"Total trade selesai={state['total_trades']}"
    )


# ============================================================
# PROGRAM UTAMA
# ============================================================

if __name__ == "__main__":

    process_new_candles()
