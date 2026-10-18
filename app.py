from datetime import date
from pathlib import Path
from typing import cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Coffee Shop Sales",
    page_icon="☕",
    layout="wide",
)

DATA_PATH = (
    Path(__file__).parent
    / "data"
    / "coffee_shop_cleaned.csv"
)

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

COFFEE = "#684832"
COFFEE_LIGHT = "#A57952"
INK = "#38291F"
CREAM = "#F6F1E9"
CARD = "#FFFDFA"
SPARSE_MONTH_RECORD_THRESHOLD = 100


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================

@st.cache_data(show_spinner=False)
def load_data(path: str, modified_time: float) -> pd.DataFrame:
    """Load and validate the cleaned sales dataset."""
    del modified_time

    data = pd.read_csv(path)

    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    data["transaction_date"] = pd.to_datetime(
        data["transaction_date"],
        errors="coerce",
    )

    for column in [
        "transaction_id",
        "transaction_qty",
        "unit_price",
        "Revenue",
    ]:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    return data


def select_all(
    label: str,
    values: list[str],
    key: str,
) -> list[str]:
    """Create a multi-select filter with an All option."""
    choices = ["All", *values]

    selected = st.sidebar.multiselect(
        label,
        choices,
        default=["All"],
        key=key,
    )

    return values if "All" in selected else selected


def format_money(value: float) -> str:
    return f"${value:,.2f}"


def format_chart_money(value: float) -> str:
    """Use compact dollar labels that remain readable beside chart points."""
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


# ============================================================
# CHART HELPERS
# ============================================================

def chart_layout(
    fig: go.Figure,
    height: int = 340,
) -> go.Figure:
    """Apply consistent dashboard styling."""
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=35, t=26, b=30),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(
            family="Inter, Arial, sans-serif",
            color=INK,
            size=12,
        ),
        hoverlabel=dict(
            bgcolor="#fffaf3",
            font_color=INK,
        ),
        showlegend=False,
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#E7DCCE",
        zeroline=False,
        tickfont=dict(color="#55483D", size=11),
        title_font=dict(color=INK, size=12),
    )

    fig.update_yaxes(
        gridcolor="#EFE8DF",
        linecolor="#E7DCCE",
        zeroline=False,
        tickfont=dict(color="#55483D", size=11),
        title_font=dict(color=INK, size=12),
    )

    return fig


def render_chart(
    fig: go.Figure,
    config: dict[str, object],
) -> None:
    """Render a chart with Streamlit-compatible width settings."""
    version = tuple(
        int(part) for part in st.__version__.split(".")[:2]
    )

    if version >= (1, 50):
        st.plotly_chart(
            fig,
            width="stretch",
            config=config,
        )
    else:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=config,
        )


def render_table(data: pd.DataFrame) -> None:
    """Render a table across the available width."""
    version = tuple(
        int(part) for part in st.__version__.split(".")[:2]
    )

    if version >= (1, 50):
        st.dataframe(
            data,
            width="stretch",
            hide_index=True,
        )
    else:
        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# DASHBOARD CSS
# ============================================================

st.markdown(
    """
    <style>
      .stApp {
          background: #F6F1E9;
          color: #38291F;
      }

      [data-testid="stAppViewContainer"] > .main {
          background: transparent;
      }

      .block-container {
          max-width: 1560px;
          padding: 1.5rem 2rem 2.2rem;
      }

      [data-testid="stSidebar"] {
          background: #493326;
      }

      [data-testid="stSidebar"] * {
          color: #FFF9F1;
      }

      [data-testid="stSidebar"] [data-baseweb="select"] * {
          color: #38291F;
      }

      [data-testid="stSidebar"] input {
          color: #38291F;
      }

      h1 {
          color: #38291F;
          letter-spacing: -.035em;
          margin-bottom: 0;
      }

      h2, h3 {
          color: #493326;
      }

      [data-testid="stCaptionContainer"] {
          color: #75675A;
      }

      [data-testid="stMetric"] {
          background: #FFFDFA;
          border: 1px solid #E7DCCE;
          border-radius: 13px;
          padding: .85rem 1rem;
          min-height: 104px;
          box-shadow: 0 3px 12px rgba(76,52,31,.05);
      }

      [data-testid="stMetricLabel"] {
          color: #75675A;
          font-weight: 600;
      }

      [data-testid="stMetricValue"] {
          color: #513A2B;
          font-size: clamp(1.25rem, 2vw, 1.9rem);
      }

      [data-testid="stHorizontalBlock"] {
          gap: 1rem;
      }

      hr {
          border-color: #E7DCCE;
      }

      @media (max-width: 760px) {
          .block-container {
              padding: 1rem .8rem 1.5rem;
          }

          [data-testid="stMetric"] {
              padding: .7rem;
              min-height: 90px;
          }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_PATH.is_file():
    st.error(f"Cleaned CSV not found: {DATA_PATH}")
    st.stop()

try:
    df = load_data(
        str(DATA_PATH),
        DATA_PATH.stat().st_mtime,
    )
except (
    OSError,
    ValueError,
    pd.errors.ParserError,
    UnicodeDecodeError,
) as exc:
    st.error(f"Could not load a valid sales dataset: {exc}")
    st.stop()

if df.empty:
    st.error("The cleaned CSV contains no records.")
    st.stop()


# ============================================================
# DATA QUALITY CHECKS
# ============================================================

required = [
    "transaction_date",
    "transaction_id",
    "transaction_qty",
    "Revenue",
]

invalid = df[required].isna().any(axis=1)

if invalid.any():
    st.warning(
        f"{int(invalid.sum()):,} records with invalid required "
        "values were excluded."
    )

df = df.loc[~invalid].copy()

if df.empty:
    st.error(
        "No records have valid dates, transaction IDs, "
        "quantities, and revenue."
    )
    st.stop()

missing_label = "(Missing)"

for col in [
    "store_location",
    "product_category",
    "product_detail",
]:
    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna(missing_label)
    )


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Filters")

min_date = df["transaction_date"].min().date()
max_date = df["transaction_date"].max().date()

date_selection = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Start and end dates are inclusive.",
)

if isinstance(date_selection, date):
    start_date = end_date = date_selection

elif (
    isinstance(date_selection, (tuple, list))
    and len(date_selection) == 2
):
    start_date, end_date = cast(
        tuple[date, date],
        tuple(date_selection),
    )

else:
    start_date, end_date = min_date, max_date

if start_date > end_date:
    start_date, end_date = end_date, start_date

locations = sorted(
    df["store_location"].unique().tolist()
)

categories = sorted(
    df["product_category"].unique().tolist()
)

selected_locations = select_all(
    "Store location",
    locations,
    "location",
)

selected_categories = select_all(
    "Product category",
    categories,
    "category",
)

candidate = df.loc[
    df["store_location"].isin(selected_locations)
    & df["product_category"].isin(selected_categories)
]

products = sorted(
    candidate["product_detail"].unique().tolist()
)

selected_products = select_all(
    "Product",
    products,
    "product",
)


# ============================================================
# APPLY FILTERS
# ============================================================

date_mask = (
    df["transaction_date"].ge(pd.Timestamp(start_date))
    & df["transaction_date"].lt(
        pd.Timestamp(end_date) + pd.Timedelta(days=1)
    )
)

filtered = df.loc[
    date_mask
    & df["store_location"].isin(selected_locations)
    & df["product_category"].isin(selected_categories)
    & df["product_detail"].isin(selected_products)
].copy()


# ============================================================
# HEADER
# ============================================================

st.title("☕ Coffee Shop Sales")

st.caption(
    "A clear view of revenue, customer activity, "
    "and product performance."
)

st.caption(
    f"Showing {len(filtered):,} of {len(df):,} valid records "
    f"· {start_date:%b %d, %Y} – {end_date:%b %d, %Y}"
)


# ============================================================
# ROW 1: REVENUE BY CATEGORY AND STORE
# ============================================================

cat_col, store_col = st.columns(2)

with cat_col:
    st.subheader("Revenue by Product Category")

    if filtered.empty:
        st.info("No category revenue for these filters.")

    else:
        cat = (
            filtered.groupby("product_category", as_index=False)
            .agg(Revenue=("Revenue", "sum"))
            .sort_values(by="Revenue", ascending=False)
        )

        fig = px.bar(
            cat,
            x="Revenue",
            y="product_category",
            orientation="h",
            color_discrete_sequence=[COFFEE_LIGHT],
        )

        fig.update_traces(
            text=cat["Revenue"].map(
                lambda value: f"${value:,.0f}"
            ),
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>"
                "Revenue: $%{x:,.2f}"
                "<extra></extra>"
            ),
        )

        fig.update_xaxes(
            title="Revenue",
            tickprefix="$",
            tickformat=",.0f",
        )

        fig.update_yaxes(
            title=None,
            automargin=True,
        )

        render_chart(
            chart_layout(
                fig,
                max(300, min(440, 50 * len(cat) + 90)),
            ),
            {"displayModeBar": False},
        )


with store_col:
    st.subheader("Revenue by Store Location")

    if filtered.empty:
        st.info("No store revenue for these filters.")

    else:
        store = (
            filtered.groupby("store_location", as_index=False)
            .agg(Revenue=("Revenue", "sum"))
            .sort_values(by="Revenue", ascending=False)
        )

        fig = px.bar(
            store,
            x="Revenue",
            y="store_location",
            orientation="h",
            color_discrete_sequence=[COFFEE],
        )

        fig.update_traces(
            text=store["Revenue"].map(
                lambda value: f"${value:,.0f}"
            ),
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>"
                "Revenue: $%{x:,.2f}"
                "<extra></extra>"
            ),
        )

        fig.update_xaxes(
            title="Revenue",
            tickprefix="$",
            tickformat=",.0f",
        )

        fig.update_yaxes(
            title=None,
            automargin=True,
        )

        render_chart(
            chart_layout(
                fig,
                max(300, min(440, 50 * len(store) + 90)),
            ),
            {"displayModeBar": False},
        )


# ============================================================
# ROW 2: KEY PERFORMANCE INDICATORS
# ============================================================

st.subheader("Key Performance Indicators")

revenue = float(filtered["Revenue"].sum())

transactions = int(
    filtered["transaction_id"].nunique()
)

items = float(
    filtered["transaction_qty"].sum()
)

aov = revenue / transactions if transactions else 0.0

kpis = st.columns(4)

kpis[0].metric(
    "Total Revenue",
    format_money(revenue),
)

kpis[1].metric(
    "Transactions",
    f"{transactions:,}",
)

kpis[2].metric(
    "Items Sold",
    f"{items:,.0f}",
)

kpis[3].metric(
    "Average Order Value",
    format_money(aov),
)


# ============================================================
# ROW 3: MONTHLY REVENUE AND TOP PRODUCTS
# ============================================================

monthly_col, product_col = st.columns([3, 2])


with monthly_col:
    st.subheader("Monthly Revenue")

    if filtered.empty:
        st.info("No monthly revenue for these filters.")

    else:
        monthly_source = filtered.assign(
            month=(
                filtered["transaction_date"]
                .dt.to_period("M")
                .dt.to_timestamp()
            )
        )

        monthly = (
            monthly_source.groupby(
                "month",
                as_index=False,
            )
            .agg(
                Revenue=("Revenue", "sum"),
                Records=("Revenue", "size"),
            )
            .sort_values(by="month")
        )

        # Break the line at sparse months and unobserved calendar months. Sparse
        # records remain visible as their own points with their actual totals.
        month_number = monthly["month"].dt.year * 12 + monthly["month"].dt.month
        dense_month = monthly["Records"] >= SPARSE_MONTH_RECORD_THRESHOLD
        monthly["_line_run"] = (
            (~dense_month) | month_number.diff().ne(1)
        ).cumsum()
        dense_monthly = monthly.loc[dense_month]
        sparse_monthly = monthly.loc[~dense_month]

        split_scales = not dense_monthly.empty and not sparse_monthly.empty
        fig = make_subplots(
            rows=1,
            cols=2 if split_scales else 1,
            column_widths=[0.7, 0.3] if split_scales else [1.0],
            horizontal_spacing=0.14 if split_scales else 0.08,
            subplot_titles=(
                ["Higher-volume months", "Sparse observed months"]
                if split_scales
                else ["Monthly revenue"]
            ),
        )

        for run_number, run in dense_monthly.groupby("_line_run", sort=True):
            fig.add_trace(
                go.Scatter(
                    x=run["month"].tolist(),
                    y=run["Revenue"].to_numpy(dtype="float64").tolist(),
                    customdata=run[["Records"]].to_numpy(),
                    text=[
                        format_chart_money(float(value))
                        for value in run["Revenue"].tolist()
                    ],
                    mode="lines+markers+text",
                    textposition="top center",
                    textfont=dict(color=INK, size=10),
                    name="Monthly revenue trend",
                    legendgroup="dense-months",
                    showlegend=bool(
                        run_number == dense_monthly["_line_run"].min()
                    ),
                    line=dict(width=3, color=COFFEE),
                    marker=dict(size=7, color=COFFEE_LIGHT),
                    hovertemplate=(
                        "%{x|%b %Y}<br>"
                        "Revenue: $%{y:,.2f}<br>"
                        "Records: %{customdata[0]:,}"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )

        if not sparse_monthly.empty:
            sparse_column = 2 if split_scales else 1
            fig.add_trace(
                go.Bar(
                    x=sparse_monthly["month"].tolist(),
                    y=sparse_monthly["Revenue"].to_numpy(dtype="float64").tolist(),
                    customdata=sparse_monthly[["Records"]].to_numpy(),
                    text=[
                        format_chart_money(float(value))
                        for value in sparse_monthly["Revenue"].tolist()
                    ],
                    textposition="outside",
                    textfont=dict(color=INK, size=10),
                    name=f"Sparse month (< {SPARSE_MONTH_RECORD_THRESHOLD} records)",
                    marker=dict(color=COFFEE_LIGHT, line=dict(width=1, color=COFFEE)),
                    hovertemplate=(
                        "%{x|%b %Y}<br>"
                        "Revenue: $%{y:,.2f}<br>"
                        "Records: %{customdata[0]:,}"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=sparse_column,
            )

        fig.update_layout(
            height=350,
            margin=dict(l=58, r=22, t=54, b=48),
            paper_bgcolor=CARD,
            plot_bgcolor=CARD,
            font=dict(family="Inter, Arial, sans-serif", color=INK, size=12),
            hoverlabel=dict(bgcolor="#fffaf3", font_color=INK),
            showlegend=False,
            bargap=0.32,
        )
        fig.update_annotations(font=dict(color=INK, size=11))
        fig.update_xaxes(
            title=None,
            tickformat="%b",
            dtick="M1",
            tickangle=-25,
            showgrid=False,
            linecolor="#E7DCCE",
            zeroline=False,
            tickfont=dict(color="#55483D", size=10),
        )
        fig.update_yaxes(
            title="Revenue",
            tickprefix="$",
            tickformat=",.0f",
            gridcolor="#EFE8DF",
            linecolor="#E7DCCE",
            zeroline=False,
            tickfont=dict(color="#55483D", size=10),
            title_font=dict(color=INK, size=11),
        )
        if split_scales:
            dense_max = float(dense_monthly["Revenue"].max())
            sparse_max = float(sparse_monthly["Revenue"].max())
            fig.update_yaxes(range=[0, max(dense_max * 1.1, 1.0)], row=1, col=1)
            fig.update_yaxes(range=[0, max(sparse_max * 1.35, 1.0)], row=1, col=2)
        else:
            observed_max = float(monthly["Revenue"].max())
            fig.update_yaxes(range=[0, max(observed_max * 1.1, 1.0)], row=1, col=1)

        render_chart(
            fig,
            {"displayModeBar": False},
        )

        if split_scales:
            sparse_counts = ", ".join(
                f"{row.month:%b}: {int(cast(int, row.Records)):,}"
                for row in sparse_monthly.itertuples(index=False)
            )
            st.caption(
                "The panels use separate dollar scales so sparse observations remain "
                f"readable. Sparse-month record counts: {sparse_counts}."
            )

        with st.expander("Monthly revenue diagnostics"):
            diagnostic = monthly.copy()
            diagnostic["month"] = diagnostic["month"].dt.strftime(
                "%B %Y"
            )
            diagnostic["Revenue"] = diagnostic["Revenue"].round(2)

            render_table(diagnostic)


with product_col:
    st.subheader("Top 10 Products by Quantity Sold")

    if filtered.empty:
        st.info("No product quantities for these filters.")

    else:
        top = (
            filtered.groupby("product_detail", as_index=False)
            .agg(transaction_qty=("transaction_qty", "sum"))
            .sort_values(by="transaction_qty", ascending=False)
            .head(10)
            .sort_values(by="transaction_qty", ascending=True)
        )

        fig = px.bar(
            top,
            x="transaction_qty",
            y="product_detail",
            orientation="h",
            color_discrete_sequence=[COFFEE_LIGHT],
        )

        fig.update_traces(
            text=top["transaction_qty"].map(
                lambda value: f"{value:,.0f}"
            ),
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>"
                "Items sold: %{x:,.0f}"
                "<extra></extra>"
            ),
        )

        fig.update_xaxes(
            title="Items sold",
            tickformat=",.0f",
        )

        fig.update_yaxes(
            title=None,
            automargin=True,
        )

        render_chart(
            chart_layout(fig, 350),
            {"displayModeBar": False},
        )


# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

st.divider()

st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="coffee_shop_sales_filtered.csv",
    mime="text/csv",
    disabled=filtered.empty,
)

with st.expander("View filtered sales data"):
    render_table(filtered)


# ============================================================
# FOOTER
# ============================================================

st.caption("Coffee Shop Sales · Interactive analytics")
