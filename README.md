# FreshTrack — Perishable Inventory & Spoilage Prevention

FreshTrack is a beginner-friendly Streamlit application for restaurants, grocery stores, caterers, hotels, and food distributors. It helps a team record perishable stock, spot expiry and reorder risks, log stock movements, and estimate near-term demand from sales entered by staff.

## Problem addressed

Perishable businesses balance short shelf lives against uncertain customer demand. Over-ordering causes spoilage; under-ordering causes missed sales. FreshTrack makes stock, expiry, recorded waste, and recent sales visible in one place. It does not claim to predict demand from external data or place supplier orders automatically.

## Features

- Manager and Staff workspace choices (a convenience selector, **not** account authentication or access control).
- Inventory form with item, category, location, quantity, unit, reorder level, expiry date, and optional supplier.
- Search by item/category/location/supplier; filter by location and expiry status; download the visible inventory as CSV.
- Expiring-soon, expired, and low-stock dashboard alerts.
- Stock movement log for deliveries, production use, spoilage, and corrections; prevents stock from going negative.
- Daily sales entry and a transparent seven-calendar-day average sales / estimated days-of-stock view.
- SQLite local storage with additive schema initialization. The app starts empty; it does not contain fabricated transaction examples.

## Technology

Python 3.10+, Streamlit, Pandas, SQLite, and pytest.

## Run in Windows / VS Code / PowerShell

1. Install Python 3.10 or newer and open this folder in VS Code.
2. In VS Code, choose **Terminal → New Terminal** (PowerShell).
3. Create and activate an environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

4. Install the packages:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start FreshTrack:

   ```powershell
   streamlit run app.py
   ```

   Streamlit opens the app in your browser. Use **Ctrl+C** in the terminal to stop it. Inventory is stored in `freshtrack.db` next to `db.py` by default. To choose another SQLite file, set the `FRESHTRACK_DB` environment variable before starting the app.

## Run tests

```powershell
python -m pytest -q
```

Tests use temporary databases and do not modify your app's inventory database.

## How the main code works

- `app.py` builds the Streamlit user interface. It reads database records to render the dashboard and calls the functions below when a form is saved.
- `db.py` owns SQLite connections, creates tables only when missing, validates basic inventory values, records quantity movements, and summarizes entered sales.
- `items` stores current perishable stock. `stock_movements` is an audit trail of quantity changes. `sales_history` stores daily quantities sold per item. Foreign keys connect these records.
- The sales estimate adds quantities recorded during the last seven calendar days, divides by seven for average daily sales, then divides stock on hand by that average. With no sales records, the app clearly asks staff to enter sales instead of inventing a forecast.
- `tests/test_db.py` checks insertion, input validation, stock adjustment rules, sales calculations, and safe repeat initialization.

## Streamlit Community Cloud

The app can be deployed by connecting this repository and selecting `app.py` as the entry point. Streamlit Community Cloud's local filesystem may reset during redeploys or restarts, so its local SQLite file is suitable for a demo, not durable multi-user business storage. For persistent production use, move storage to a managed database and add real user authentication before exposing sensitive business data.

## Submission checklist

- Replace student and link placeholders in `outputs/Submission.md`.
- Push the complete source to a GitHub repository.
- Optionally deploy to Streamlit Community Cloud and add its URL.
- Record a demo of at most five minutes, upload it to YouTube, and add the video URL.
