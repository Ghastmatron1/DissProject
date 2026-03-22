from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import os
from pathlib import Path

# small helper function to robustly parse dates with multiple possible formats
def _robust_parse_dates(series: pd.Series) -> pd.Series:
    """
    Try several common formats first (fast exact parsing), then fall back to
    pandas/dateutil flexible parsing. Returns a pd.Series of datetimes (NaT on failure).
    """
    formats = ("%Y-%m-%d", "%Y-%m", "%Y %b", "%Y %B", "%Y")
    # preserve original dtype/values by not coercing to str unless necessary
    for fmt in formats:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        if parsed.notna().any():
            # keep parsed where possible, fallback to flexible parsing for the rest
            return parsed.fillna(pd.to_datetime(series, errors="coerce"))
    # final fallback: flexible parsing
    return pd.to_datetime(series, errors="coerce")


class DataExtractor:
    """
    Utility class to load and clean datasets used by the simulator:
    - laod_earnings_2025: cleaned ONS AWE dataset for 2025
    - load_housing_data: cleaned housing price data
    - load_ehs: cleaned English Housing Survey data
    - load_land_registry: loads a cleaned time-series of prices
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    def _read_file(self, file_path: str, sheet_name: Optional[int | str] = None) -> pd.DataFrame:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".csv", ".txt"]:
            return pd.read_csv(file_path)
        elif ext in [".xls", ".xlsx"]:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def load_earnings_2025(self, file_path):
        """
        Loads the ONS AWE dataset from sheet '4. NSA sect monthly figs',
        cleans the messy layout, maps CDID codes to readable sector names,
        strips month labels, and returns only 2025 rows.
        """

        # 1. Load the raw sheet with NO headers
        df_raw = pd.read_excel(file_path, sheet_name="4. NSA sect monthly figs", header=None)
        # 2. Find the row where 'CDID' appears
        cdid_row_idx = df_raw.index[df_raw.iloc[:, 0] == "CDID"][0]
        # 3. Use the CDID row as header, and everything after as data
        df = df_raw.iloc[cdid_row_idx + 1:].copy()
        df.columns = df_raw.iloc[cdid_row_idx]
        # 4. Drop rows that are completely empty
        df = df.dropna(how="all")
        # 5. Rename the first column to 'Month'
        df.rename(columns={df.columns[0]: "Month"}, inplace=True)
        # 6. Clean the Month column (remove (p), (r), whitespace)
        df["Month"] = (
            df["Month"]
            .astype(str)
            .str.replace("(p)", "", regex=False)
            .str.replace("(r)", "", regex=False)
            .str.strip()
        )
        # 7. Map CDID codes → human-readable sector names
        rename_map = {
            "KA46": "Whole Economy AWE",
            "KA47": "Whole Economy Bonuses",
            "KA48": "Whole Economy Arrears",
            "KA4O": "Private Sector AWE",
            "KA4P": "Private Sector Bonuses",
            "KA4Q": "Private Sector Arrears",
            "KA4R": "Public Sector AWE",
            "KA4S": "Public Sector Bonuses",
            "KA4T": "Public Sector Arrears",
            "K550": "Services AWE",
            "K55P": "Services Bonuses",
            "K55Q": "Services Arrears",
            "K55U": "Finance & Business Services AWE",
            "K55V": "Finance & Business Services Bonuses",
            "K55W": "Finance & Business Services Arrears",
            "K55R": "Public excl. Financial Services AWE",
            "K55S": "Public excl. Financial Services Bonuses",
            "K55T": "Public excl. Financial Services Arrears",
        }

        df = df.rename(columns=rename_map)
        # 8. Keep only readable columns
        keep_cols = [col for col in df.columns if not str(col).startswith("Unnamed")]
        df = df[keep_cols]
        # 9. Filter to only 2025 rows
        df_2025 = df[df["Month"].str.startswith("2025")].copy()
        # 10. Keep only Average Weekly Earnings (AWE)
        awe_cols = ["Month"] + [col for col in df_2025.columns if col.endswith("AWE")]
        df_2025_awe = df_2025[awe_cols]
        return df_2025_awe

    # python
    # Replace the existing `load_housing_data` method and the `if __name__ == "__main__":` block
    # in `Algorithms/Data_Extraction.py` with the code below.

    def load_housing_data(self, file_path):
        """
        Loads housing price workbook (sheet index 4), strips column whitespace,
        normalises the date column robustly, and returns a single-row dataframe
        for the most recent time period.
        """
        df = pd.read_excel(file_path, sheet_name=4, skiprows=2)

        # strip whitespace from column names (fix trailing spaces like 'East ')
        df.columns = df.columns.str.strip()
        # debug
        print("Columns in housing data:", df.columns.tolist())

        # Identify time column (first column)
        time_period_col = df.columns[0]

        # Remove bracketed notes and whitespace from the time column
        df[time_period_col] = (
            df[time_period_col].astype(str)
            .str.replace(r"\[.*?\]", "", regex=True)
            .str.strip()
        )

        # Try a set of common formats first to avoid pandas' ambiguous inference warning
        formats = ['%Y-%m-%d', '%Y-%m', '%b %Y', '%B %Y', '%Y/%m/%d', '%d/%m/%Y']
        parsed = pd.to_datetime(df[time_period_col], format=formats[0], errors='coerce')

        for fmt in formats[1:]:
            mask = parsed.isna()
            if not mask.any():
                break
            parsed.loc[mask] = pd.to_datetime(df.loc[mask, time_period_col], format=fmt, errors='coerce')

        # final fallback to pandas inference (keeps old behaviour if none of the formats matched)
        parsed = parsed.fillna(_robust_parse_dates(df[time_period_col]))

        # store as datetime (or .dt.date if you prefer date objects)
        df[time_period_col] = parsed.dt.date

        most_recent_row = df.iloc[-1]
        most_recent_date = most_recent_row[time_period_col]
        print("Most recent date in housing data:", most_recent_date)

        headers = df.columns.tolist()
        prices = most_recent_row
        housing_prices_df = pd.DataFrame([prices], columns=headers)

        return housing_prices_df


    def load_ehs(self, file_path: str, usecols: Optional[List[str]] = None,
                 sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Loads English Housing Survey (CSV or Excel). Tries to detect common columns:
        - 'dwelling_age' or 'AGE' / 'age_band'
        - 'damp' / 'presence_of_damp' / 'damp_or_mould'
        - 'pests' / 'rats' / 'vermin'
        - 'tenure' / 'owner_tenure'
        If `usecols` provided, these are used to subset the file.
        Returns cleaned DataFrame with standardized column names where possible.
        """
        df = self._read_file(file_path, sheet_name=sheet_name)
        # Optional subset
        if usecols:
            df = df[[c for c in usecols if c in df.columns]]

        # Lowercase columns for matching
        col_map: Dict[str, str] = {}
        lowercols = {c.lower(): c for c in df.columns}

        def find_any(keys: List[str]) -> Optional[str]:
            for k in keys:
                if k in lowercols:
                    return lowercols[k]
            return None


        mappings = {
            "age": ["dwelling_age", "age", "age_band", "yr_built", "year_built"],
            "damp": ["damp", "presence_of_damp", "damp_or_mould", "mould"],
            "rats": ["rats", "vermin", "pests", "rodents"],
            "tenure": ["tenure", "owner_tenure", "tenure_type"],
            "condition": ["condition_score", "repair_needs", "disrepair"]
        }

        for std, keys in mappings.items():
            found = find_any(keys)
            if found:
                col_map[found] = std

        # rename matched columns
        if col_map:
            df = df.rename(columns=col_map)

         # Basic cleaning: ensure numeric age, booleans for damp/rats where possible
        if "age" in df.columns:
            df["age"] = pd.to_numeric(df["age"], errors="coerce")
        if "damp" in df.columns:
            df["damp"] = df["damp"].apply(lambda x: self._to_bool(x))
        if "rats" in df.columns:
            df["rats"] = df["rats"].apply(lambda x: self._to_bool(x))
        if "condition" in df.columns:
            df["condition"] = pd.to_numeric(df["condition"], errors="coerce")

        return df.reset_index(drop=True)

    def load_land_registry_prices(self, file_path: str, date_col: str = "Date", price_col: Optional[str] = None) -> pd.DataFrame:
        """
        Loads Land Registry / price time series data.
        Expects a table with a date column and either a single price column or multiple columns (regions).
        Returns a tidy DataFrame with columns [date, region?, price].
        """
        df = self._read_file(file_path)
        # try to find date column automatically if not provided
        if date_col not in df.columns:
            # choose first datetime-like column
            for c in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[c]) or df[c].astype(str).str.match(r"\d{4}-\d{2}").any():
                    date_col = c
                    break

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        # If price_col provided, return subset
        if price_col and price_col in df.columns:
            return df[[date_col, price_col]].rename(columns={date_col: "date", price_col: "price"}).dropna().reset_index(drop=True)

        # Otherwise, melt all non-date columns
        value_cols = [c for c in df.columns if c != date_col]
        tidy = df.melt(id_vars=[date_col], value_vars=value_cols, var_name="region", value_name="price")
        tidy = tidy.dropna(subset=["price"])
        tidy["date"] = pd.to_datetime(tidy[date_col]).dt.date
        return tidy[["date", "region", "price"]].reset_index(drop=True)

    @staticmethod
    def _to_bool(val) -> Optional[bool]:
        if pd.isna(val):
            return None
        if isinstance(val, (bool, np.bool_)):
            return bool(val)
        s = str(val).strip().lower()
        if s in {"yes", "y", "true", "1", "t"}:
            return True
        if s in {"no", "n", "false", "0", "f"}:
            return False
        # numeric heuristics
        try:
            n = float(s)
            return n > 0
        except Exception:
            return None


    def clean_and_melt_housing(self, df, time_col='Time period'):
        """
        - Strip whitespace from column names
        - Parse `time_col` robustly (try '%Y-%m-%d' first, then fall back to infer)
        - Melt wide dataframe to long form with columns: Time period, Region, Price
        """
        #work on a copy of the dataframe to avoid modifying the original
        df = df.copy()
        # strip whitespace from column names
        df.columns = df.columns.str.strip()

        if time_col not in df.columns:
            raise KeyError(f"Missing column: `{time_col}`")

        # Try a set of common format first, then fall back to infer_datetime_format
        formats = ['%Y-%m-%d', '%Y-%m', '%b %Y', '%B %Y', '%Y/%m/%d', '%d/%m/%Y']
        parsed = pd.to_datetime(df[time_col], format='%Y-%m-%d', errors='coerce')

        for fmt in formats[1:]:
            if not parsed.isna().any():
                break
            mask = parsed.isna()
            parsed.loc[mask] = pd.to_datetime(df.loc[mask, time_col], format=fmt, errors='coerce')

        #final fallback to pandas inference
        parsed = parsed.fillna(_robust_parse_dates(df[time_col]))
        df[time_col] = parsed

        #show most recent date for sanity check
        most_recent = df[time_col].max()
        print("Most recent date in housing data:", most_recent)

        #melt wide format to long form
        long = df.melt(id_vars=[time_col], var_name='Region', value_name='Price')
        long = long.dropna(subset=['Price']).reset_index(drop=True)

        return long


# python
# ---- main guard: ensure output directory exists before saving ----
if __name__ == "__main__":
    extractor = DataExtractor(seed=42)

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # earnings
    file_path = data_dir / "earn02nov2025 (1).xls"
    try:
        earnings = extractor.load_earnings_2025(str(file_path))
        print(earnings.head())
        earnings.to_csv(data_dir / "earnings_2025_awe.csv", index=False)
    except Exception as e:
        print("Failed to load earnings:", e)

        # housing
        housing_file_path = data_dir / "Housing Prices.xlsx"
        try:
            housing = extractor.load_housing_data(str(housing_file_path))
            print(housing.head())
            # optional: convert to long form and save
            try:
                housing_long = extractor.clean_and_melt_housing(housing, time_col=housing.columns[0])
                housing_long.to_csv(data_dir / "housing_long.csv", index=False)
                print("Housing long shape:", housing_long.shape)
            except Exception:
                # if cleaning/melting fails, still save the single-row wide snapshot
                housing.to_csv(data_dir / "housing_latest_row.csv", index=False)
        except Exception as e:
            print("Failed to load housing data:", e)

# Example usage (not executed in library import):
# extractor = DataExtractor(seed=42)
# awe_2025 = extractor.load_earnings_2025(r`data/earn02nov2025 (1).xls`)
# housing_latest = extractor.load_housing_data(r`data/Housing Prices.xlsx`)
# ehs = extractor.load_ehs(r`data/ehs_sample.csv`)
# lr = extractor.load_land_registry_prices(r`data/land_registry_prices.csv`)
