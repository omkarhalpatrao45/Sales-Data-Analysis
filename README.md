# Coffee Shop Sales Analysis

A Python data analysis project and Streamlit dashboard for exploring coffee shop transactions. It includes the source Excel workbook, cleaned and review CSV outputs, and Jupyter notebooks for inspection and exploratory analysis.

## Project files

- `app.py` — Streamlit dashboard with date, store, and product category filters, KPI cards, charts, and filtered data export.
- `data/Coffee_Shop_Sales.xlsx` — original source workbook. Keep this file unchanged.
- `data/coffee_shop_cleaned.csv` — cleaned dataset loaded by the dashboard.
- `data/coffee_shop_review.csv` — records set aside for review during cleaning.
- `data/coffee_shop_cleaned.csv.*.bak` — preserved backup of an earlier cleaned CSV.
- `notebooks/01_Data_Inspection.ipynb` — initial data inspection.
- `notebooks/Coffee_Sales_Analysis.ipynb` — exploratory analysis and visualizations.

## Requirements and setup (Windows PowerShell)

Use Python 3.10 or newer. From the project directory, create and activate a virtual environment, then install the project dependencies:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the dashboard from that environment:

```powershell
python -m streamlit run app.py
```

If activation is disabled in your PowerShell session, invoke the environment directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local address printed by Streamlit (usually `http://localhost:8501`). Using the virtual environment ensures the dashboard runs with the project's installed Streamlit and chart dependencies rather than a potentially different system installation.

## Run the notebooks

With the environment active, start Jupyter:

```powershell
python -m jupyter notebook
```

Open a notebook under `notebooks/` in Jupyter or VS Code and select the `.venv` Python interpreter as its kernel.

## Dashboard notes

The dashboard reads `data/coffee_shop_cleaned.csv` relative to `app.py`. Its sidebar filters the available reporting dates, store locations, and product categories. KPI totals and charts are based on the rows remaining after those filters; the dashboard also provides a filtered sales table and CSV download.

The valid reporting period is derived from dates present in the cleaned CSV. The app does not extend the date range beyond the data. If the CSV is regenerated, the dashboard reloads it based on its modification time.

## Development checks

Optional type-checking tools are listed separately in `requirements-dev.txt`. Install them after the main requirements when needed:

```powershell
python -m pip install -r requirements-dev.txt
python -m pyright
```

