"""東証上場銘柄の5年間の株価を取得し、価格レンジ内の位置を表示する。"""

from datetime import date, timedelta
from pathlib import Path
import time

import pandas as pd
import yfinance as yf

PRICE_COLUMNS = ["最安値", "最高値", "現在値", "スケール(0-100)"]
MARKET_COLUMN = "市場・商品区分"
LISTING_FILE = Path(__file__).resolve().parents[1] / "data" / "data_j.xls"


def _as_series(value: pd.Series | pd.DataFrame | None) -> pd.Series | None:
    if isinstance(value, pd.DataFrame):
        return value.iloc[:, 0] if value.shape[1] else None
    return value


def _find_ticker_series(
    stock_df: pd.DataFrame, ticker: str, field_names: list[str]
) -> pd.Series | None:
    columns = stock_df.columns
    if isinstance(columns, pd.MultiIndex):
        for field in field_names:
            for key in ((ticker, field), (field, ticker)):
                if key in columns:
                    return _as_series(stock_df[key])
    else:
        for column in columns:
            label = str(column)
            if label.startswith(ticker) and any(
                field.casefold() in label.casefold() for field in field_names
            ):
                return _as_series(stock_df[column])
    return None


def compute_ticker_stats(stock_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if isinstance(stock_df.columns, pd.MultiIndex):
        tickers = sorted({str(column[0]) for column in stock_df.columns})
    else:
        tickers = sorted(
            {str(column).split()[0].split("_")[0] for column in stock_df.columns}
        )

    for ticker in tickers:
        high_series = _find_ticker_series(stock_df, ticker, ["High", "HIGH"])
        low_series = _find_ticker_series(stock_df, ticker, ["Low", "LOW"])
        close_series = _find_ticker_series(
            stock_df, ticker, ["Close", "Adj Close", "Adj_Close"]
        )
        if high_series is None or low_series is None or close_series is None:
            continue

        close_series = close_series.dropna()
        if close_series.empty:
            continue

        high = high_series.max()
        low = low_series.min()
        current = close_series.iloc[-1]
        scaled = (
            (current - low) / (high - low) * 100
            if pd.notna(high) and pd.notna(low) and high > low
            else float("nan")
        )
        rows.append(
            {
                "ticker": ticker,
                "最安値": low,
                "最高値": high,
                "現在値": current,
                "スケール(0-100)": scaled,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=PRICE_COLUMNS,
            index=pd.Index([], name="ticker"),
        )
    return pd.DataFrame(rows).set_index("ticker")


def add_listing_metadata(
    stats_df: pd.DataFrame, listing_df: pd.DataFrame
) -> pd.DataFrame:
    catalog = listing_df.drop_duplicates("コード").copy()
    catalog["コード"] = catalog["コード"].astype(str)
    catalog = catalog.set_index("コード")

    result = stats_df.copy()
    codes = result.index.to_series().astype(str).str.split(".", n=1).str[0]
    result["銘柄名"] = codes.map(catalog["銘柄名"])
    if MARKET_COLUMN in catalog.columns:
        result[MARKET_COLUMN] = codes.map(catalog[MARKET_COLUMN])
    else:
        result[MARKET_COLUMN] = None

    columns = ["銘柄名", MARKET_COLUMN] + [
        column for column in result.columns if column not in ("銘柄名", MARKET_COLUMN)
    ]
    return result[columns]


def download_batch(
    batch: list[str],
    start_date: date,
    end_date: date,
    ticker_data: dict[str, pd.DataFrame],
) -> None:
    batch_df = yf.download(
        batch,
        start=start_date,
        end=end_date,
        group_by="ticker",
        threads=False,
        progress=False,
    )
    if batch_df.empty:
        return

    for ticker in batch:
        if isinstance(batch_df.columns, pd.MultiIndex):
            if ticker in batch_df.columns.get_level_values(0):
                ticker_df = batch_df[ticker]
            elif ticker in batch_df.columns.get_level_values(1):
                ticker_df = batch_df.xs(ticker, axis=1, level=1)
            else:
                continue
        elif len(batch) == 1:
            ticker_df = batch_df
        else:
            continue

        close_series = _as_series(ticker_df.get("Close"))
        if close_series is not None and close_series.notna().any():
            ticker_data[ticker] = ticker_df


def download_batches(
    tickers: list[str],
    start_date: date,
    end_date: date,
    ticker_data: dict[str, pd.DataFrame],
    batch_size: int = 50,
    pause_seconds: int = 2,
) -> None:
    for start in range(0, len(tickers), batch_size):
        batch = tickers[start : start + batch_size]
        download_batch(batch, start_date, end_date, ticker_data)
        if start + batch_size < len(tickers):
            time.sleep(pause_seconds)


def main() -> None:
    listing_df = pd.read_excel(LISTING_FILE)
    print("columns:", listing_df.columns.tolist())
    print(listing_df.head(3).to_string(index=False))

    tickers = [f"{code}.T" for code in listing_df["コード"].to_list()]
    print("日本株ティッカー例:", tickers[:5])
    tickers = list(dict.fromkeys(tickers))

    today = date.today()
    start_date = today - timedelta(days=365 * 5)
    retry_wait_seconds = [30, 60]
    ticker_data: dict[str, pd.DataFrame] = {}

    download_batches(tickers, start_date, today, ticker_data)
    for retry_number, wait_seconds in enumerate(retry_wait_seconds, start=1):
        failed_tickers = [ticker for ticker in tickers if ticker not in ticker_data]
        if not failed_tickers:
            break
        print(
            f"未取得 {len(failed_tickers)} 銘柄。{wait_seconds} 秒待って再試行します "
            f"({retry_number}/{len(retry_wait_seconds)})。"
        )
        time.sleep(wait_seconds)
        download_batches(failed_tickers, start_date, today, ticker_data)

    failed_tickers = [ticker for ticker in tickers if ticker not in ticker_data]
    stock_df = pd.concat(ticker_data, axis=1) if ticker_data else pd.DataFrame()
    print(
        f"日本株ダウンロード完了。成功: {len(ticker_data)}/{len(tickers)} 銘柄、"
        f"失敗: {len(failed_tickers)} 銘柄"
    )
    if failed_tickers:
        print("失敗銘柄の先頭30件:", failed_tickers[:30])

    stats_df = compute_ticker_stats(stock_df)
    stats_df = stats_df.sort_values("スケール(0-100)", ascending=False)
    stats_df = add_listing_metadata(stats_df, listing_df)
    df_sorted = stats_df.sort_values("スケール(0-100)", ascending=True).copy()
    df_sorted.loc[:, PRICE_COLUMNS] = df_sorted[PRICE_COLUMNS].round(2)
    print(df_sorted.to_string())


if __name__ == "__main__":
    main()
