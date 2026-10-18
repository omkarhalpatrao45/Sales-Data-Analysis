from datetime import date
from pathlib import Path
from typing import Literal, Sequence, cast

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter


st.set_page_config(
    page_title="Coffee Shop Sales Dashboard",
    page_icon="☕",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "coffee_shop_cleaned.csv"
REQUIRED_COLUMNS = {
    "transaction_id",
    "transaction_date",
    "transaction_qty",
    "unit_price",
    "store_location",
    "product_category",
    "product_detail",
    "Revenue",
}


@st.cache_data
def load_data(path: str, modified_time: float) -> pd.DataFrame:
    """Load the cleaned CSV, coercing expected numeric and date fields."""
    del modified_time  # Part of the cache key so a regenerated CSV is reloaded.
    data = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    data["transaction_date"] = pd.to_datetime(
        data["transaction_date"], errors="coerce"
    )
    for column in ["transaction_id", "transaction_qty", "unit_price", "Revenue"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def resolve_date_range(
    selection: object, minimum: date, maximum: date
) -> tuple[date, date]:
    """Handle a single day, an incomplete picker range, or a full date range."""
    if isinstance(selection, date):
        return selection, selection
    if isinstance(selection, (tuple, list)):
        values = cast(Sequence[object], selection)
        if len(values) == 2 and isinstance(values[0], date) and isinstance(values[1], date):
            start, end = values[0], values[1]
            return (start, end) if start <= end else (end, start)
        if len(values) == 1 and isinstance(values[0], date):
            return values[0], values[0]
    return minimum, maximum


def create_figure(figsize: tuple[float, float]) -> tuple[Figure, Axes]:
    figure, axes = plt.subplots(figsize=figsize, dpi=140)  # pyright: ignore[reportUnknownMemberType]
    return figure, axes


def render_figure(figure: Figure) -> None:
    """Render responsively across the legacy and current Streamlit APIs."""
    streamlit_version = tuple(int(part) for part in st.__version__.split(".")[:2])
    if streamlit_version >= (1, 50):
        st.pyplot(figure, width="stretch")
    else:
        st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def style_axes(
    figure: Figure,
    axes: Axes,
    title: str,
    x_label: str,
    y_label: str,
    grid_axis: Literal["x", "y"],
) -> None:
    """Apply the dashboard's coffee palette and legible chart defaults."""
    figure.patch.set_facecolor("#FFFDFA")
    axes.set_facecolor("#FFFDFA")
    axes.set_title(title, loc="left", fontsize=13, fontweight="semibold", color="#4D4036", pad=14)  # pyright: ignore[reportUnknownMemberType]
    axes.set_xlabel(x_label, color="#64564A", labelpad=8)  # pyright: ignore[reportUnknownMemberType]
    axes.set_ylabel(y_label, color="#64564A", labelpad=8)  # pyright: ignore[reportUnknownMemberType]
    axes.tick_params(colors="#64564A", labelsize=9)  # pyright: ignore[reportUnknownMemberType]
    axes.grid(axis=grid_axis, color="#EDE5DB", linewidth=0.8)  # pyright: ignore[reportUnknownMemberType]
    axes.set_axisbelow(True)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.spines["left"].set_color("#D7C8B7")
    axes.spines["bottom"].set_color("#D7C8B7")


def add_bar_labels(axes: Axes, bars: BarContainer, maximum: float) -> None:
    """Place compact numeric labels just beyond horizontal bars."""
    for bar in cast(Sequence[Rectangle], bars.patches):
        value = float(bar.get_width())
        axes.annotate(  # pyright: ignore[reportUnknownMemberType]
            f"{value:,.0f}",
            xy=(value, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            ha="left",
            fontsize=8,
            color="#64564A",
        )
    axes.set_xlim(0, maximum * 1.16 if maximum > 0 else 1)


def format_number(value: float, _position: int) -> str:
    return f"{value:,.0f}"


st.markdown(
    """
    <style>
      :root { color-scheme: light; }
      .stApp { background: #F7F3EC; color: #34291F; }
      [data-testid="stAppViewContainer"] > .main { background: transparent; }
      .block-container { max-width: 1500px; padding: 2rem 2.4rem 3rem; }
      [data-testid="stSidebar"] { background: #EFE6D9; border-right: 1px solid #E1D4C5; }
      [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #4D4036; }
      h1 { color: #3B2B20; letter-spacing: -0.035em; padding-bottom: .15rem; }
      h2, h3 { color: #4D4036; letter-spacing: -0.015em; }
      [data-testid="stCaptionContainer"] { color: #75675A; }
      [data-testid="stMetric"] {
        background: #FFFDFA; border: 1px solid #E6D9C9; border-radius: 14px;
        padding: 1rem 1.15rem; box-shadow: 0 3px 12px rgba(76, 52, 31, .055);
        min-height: 112px;
      }
      [data-testid="stMetricLabel"] { color: #75675A; font-weight: 600; }
      [data-testid="stMetricValue"] { color: #513A2B; font-size: clamp(1.35rem, 2vw, 2rem); }
      [data-testid="stHorizontalBlock"] { gap: 1rem; }
      hr { border-color: #E3D7C9; }
      @media (max-width: 760px) {
        .block-container { padding: 1.2rem 1rem 2rem; }
        [data-testid="stMetric"] { padding: .8rem; min-height: 96px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("☕ Coffee Shop Sales")
st.caption("A clear view of revenue, customer activity, and product performance.")

if not DATA_PATH.is_file():
    st.error(f"Cleaned CSV not found: {DATA_PATH}")
    st.stop()

try:
    df = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Could not load a valid sales dataset: {exc}")
    st.stop()

if df.empty:
    st.error("The cleaned CSV contains no records.")
    st.stop()

required_values = ["transaction_date", "transaction_id", "transaction_qty", "Revenue"]
unusable = df[required_values].isna().any(axis=1)
if unusable.any():
    st.warning(
        f"{int(unusable.sum()):,} rows have missing or invalid required values "
        "and are excluded from analysis. Review the cleaning output."
    )
df = df.loc[~unusable].copy()
if df.empty:
    st.error("No records have valid dates, transaction IDs, quantities, and revenue.")
    st.stop()

missing_label = "(Missing)"
for column in ["store_location", "product_category", "product_detail"]:
    df[column] = (
        df[column]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna(missing_label)
    )

locations = sorted(df["store_location"].unique().tolist())
categories = sorted(df["product_category"].unique().tolist())
all_locations = "All locations"
all_categories = "All categories"

st.sidebar.header("Filters")
selected_locations = st.sidebar.multiselect(
    "Store locations",
    [all_locations, *locations],
    default=locations,
    help="Select All locations to reset, or clear this field to choose a smaller set.",
)
selected_categories = st.sidebar.multiselect(
    "Product categories",
    [all_categories, *categories],
    default=categories,
    help="Select All categories to reset, or clear this field to choose a smaller set.",
)

min_date = df["transaction_date"].min().date()
max_date = df["transaction_date"].max().date()
selected_dates = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Both the start date and end date are included.",
)

location_values = (
    locations if all_locations in selected_locations else selected_locations
)
category_values = (
    categories if all_categories in selected_categories else selected_categories
)
location_filtered = df.loc[df["store_location"].isin(location_values)].copy()
category_filtered = location_filtered.loc[
    location_filtered["product_category"].isin(category_values)
].copy()

start_date, end_date = resolve_date_range(selected_dates, min_date, max_date)
date_values = category_filtered["transaction_date"]
date_mask = date_values.ge(pd.Timestamp(start_date)) & date_values.lt(
    pd.Timestamp(end_date) + pd.Timedelta(days=1)
)
filtered = category_filtered.loc[date_mask].copy()

st.sidebar.caption(f"After locations: {len(location_filtered):,} rows")
st.sidebar.caption(f"After categories: {len(category_filtered):,} rows")
st.sidebar.caption(f"After dates: {len(filtered):,} rows")
st.caption(
    f"Showing {len(filtered):,} of {len(df):,} valid records · "
    f"{start_date:%b %d, %Y} – {end_date:%b %d, %Y}"
)

total_revenue = filtered["Revenue"].sum()
total_transactions = filtered["transaction_id"].nunique()
total_quantity = filtered["transaction_qty"].sum()
average_order_value = total_revenue / total_transactions if total_transactions else 0

st.subheader("Key performance indicators")
kpi_columns = st.columns(4)
kpi_columns[0].metric("Total revenue", f"{total_revenue:,.2f}")
kpi_columns[1].metric("Transactions", f"{total_transactions:,}")
kpi_columns[2].metric("Items sold", f"{total_quantity:,.0f}")
kpi_columns[3].metric("Average order value", f"{average_order_value:,.2f}")

st.divider()

if filtered.empty:
    st.info("No sales match these filters. Adjust a location, category, or date range to see results.")
else:
    st.subheader("Monthly revenue")
    monthly = (
        filtered.set_index("transaction_date")
        .resample("MS")["Revenue"]
        .sum()
        .rename("Revenue")
    )
    monthly_figure, monthly_axes = create_figure((11, 3.8))
    monthly_axes.plot(  # pyright: ignore[reportUnknownMemberType]
        cast(pd.DatetimeIndex, monthly.index).to_pydatetime(),
        monthly.to_numpy(dtype=float),
        color="#765238",
        linewidth=2.8,
        marker="o",
        markersize=4.5,
        markerfacecolor="#B8895B",
        markeredgecolor="#FFFDFA",
        markeredgewidth=1,
    )
    monthly_axes.xaxis.set_major_locator(
        mdates.MonthLocator(interval=max(1, (len(monthly) + 7) // 8))
    )
    monthly_axes.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    monthly_axes.yaxis.set_major_formatter(FuncFormatter(format_number))
    style_axes(
        monthly_figure,
        monthly_axes,
        "Revenue by month",
        "Month",
        "Revenue",
        "y",
    )
    monthly_figure.tight_layout()
    render_figure(monthly_figure)

    category_col, store_col = st.columns(2)
    with category_col:
        st.subheader("Revenue by product category")
        category_data: pd.DataFrame = (
            filtered.groupby("product_category", as_index=False)
            .agg({"Revenue": "sum"})
            .rename(columns={"product_category": "Category"})
        )
        category_data = category_data.sort_values("Revenue", ascending=False)
        category_figure, category_axes = create_figure(
            (7, max(3.2, 0.38 * len(category_data)))
        )
        category_bars = category_axes.barh(  # pyright: ignore[reportUnknownMemberType]
            category_data["Category"],
            category_data["Revenue"],
            color="#9B704C",
            height=0.66,
        )
        category_axes.invert_yaxis()
        category_axes.xaxis.set_major_formatter(
            FuncFormatter(format_number)
        )
        style_axes(
            category_figure,
            category_axes,
            "Revenue by product category",
            "Revenue",
            "",
            "x",
        )
        category_axes.set_ylabel("")  # pyright: ignore[reportUnknownMemberType]
        add_bar_labels(category_axes, category_bars, float(category_data["Revenue"].max()))
        category_figure.tight_layout()
        render_figure(category_figure)

    with store_col:
        st.subheader("Revenue by store location")
        store_data: pd.DataFrame = (
            filtered.groupby("store_location", as_index=False)
            .agg({"Revenue": "sum"})
            .rename(columns={"store_location": "Store location"})
        )
        store_data = store_data.sort_values("Revenue", ascending=False)
        store_figure, store_axes = create_figure(
            (7, max(3.2, 0.65 * len(store_data)))
        )
        store_bars = store_axes.barh(  # pyright: ignore[reportUnknownMemberType]
            store_data["Store location"],
            store_data["Revenue"],
            color="#B8895B",
            height=0.58,
        )
        store_axes.invert_yaxis()
        store_axes.xaxis.set_major_formatter(
            FuncFormatter(format_number)
        )
        style_axes(
            store_figure,
            store_axes,
            "Revenue by store location",
            "Revenue",
            "",
            "x",
        )
        store_axes.set_ylabel("")  # pyright: ignore[reportUnknownMemberType]
        add_bar_labels(store_axes, store_bars, float(store_data["Revenue"].max()))
        store_figure.tight_layout()
        render_figure(store_figure)

    st.subheader("Top 10 products by quantity sold")
    top_products: pd.DataFrame = (
        filtered.groupby("product_detail", as_index=False)
        .agg({"transaction_qty": "sum"})
        .nlargest(n=10, columns=["transaction_qty"])
        .sort_values("transaction_qty", ascending=False)
        .rename(columns={"product_detail": "Product", "transaction_qty": "Quantity sold"})
    )
    product_figure, product_axes = create_figure((11, 5))
    product_bars = product_axes.barh(  # pyright: ignore[reportUnknownMemberType]
        top_products["Product"],
        top_products["Quantity sold"],
        color="#765238",
        height=0.68,
    )
    product_axes.invert_yaxis()
    product_axes.xaxis.set_major_formatter(
        FuncFormatter(format_number)
    )
    style_axes(
        product_figure,
        product_axes,
        "Top products by quantity sold",
        "Items sold",
        "",
        "x",
    )
    product_axes.set_ylabel("")  # pyright: ignore[reportUnknownMemberType]
    add_bar_labels(
        product_axes, product_bars, float(top_products["Quantity sold"].max())
    )
    product_figure.tight_layout()
    render_figure(product_figure)

st.subheader("Filtered sales records")
st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="coffee_shop_sales_filtered.csv",
    mime="text/csv",
    disabled=filtered.empty,
)
with st.expander("View filtered sales data", expanded=False):
    streamlit_version = tuple(int(part) for part in st.__version__.split(".")[:2])
    if streamlit_version >= (1, 50):
        st.dataframe(filtered, width="stretch", hide_index=True)  # pyright: ignore[reportUnknownMemberType]
    else:
        st.dataframe(filtered, use_container_width=True, hide_index=True)  # pyright: ignore[reportUnknownMemberType]

st.caption("Coffee Shop Sales · Interactive analytics")
