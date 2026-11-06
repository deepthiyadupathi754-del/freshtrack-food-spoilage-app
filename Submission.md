# FreshTrack — Project Submission

**Student name:** [Enter your name]  
**Roll number:** [Enter your roll number]  
**Subject:** Python Programming  
**Sector:** Food Spoilage Prevention

## Project overview

FreshTrack is a perishable-inventory tracking application for restaurants, supermarkets, hotels, caterers, and food distributors. It helps staff see what stock is on hand, which items need attention before expiry, and which items are at or below their chosen reorder level.

## Problem statement

Businesses handling food with short shelf lives must estimate demand while customer traffic changes. Over-ordering can create food waste; under-ordering can cause stockouts and lost sales. Inventory and expiry information may be incomplete, and staff may not consistently record stock changes. FreshTrack provides forms and a simple shared workflow for recording inventory, expiry dates, stock movements, and daily sales. Its short-term demand estimate is based only on sales data entered by the business.

## Main features

- Inventory entry with category, location, quantity, unit, reorder level, expiry date, and optional supplier.
- Search and filters for location and expiry status, plus CSV export.
- Dashboard alerts for items expiring soon, expired items, and low stock.
- Stock adjustment log for deliveries, use, spoilage, and corrections.
- Daily sales entry and a transparent seven-day average sales and estimated days-of-stock calculation.
- SQLite data storage and validation to prevent negative inventory.

## Technologies

Python, Streamlit, Pandas, SQLite, and pytest.

## Student and project links

- **Name:** [Enter your name]
- **Roll number:** [Enter your roll number]
- **GitHub repository:** [ADD AFTER CREATING REPOSITORY]
- **Live app:** [ADD IF DEPLOYED]
- **YouTube demo video:** [ADD AFTER UPLOADING VIDEO]

## How to run

Install Python 3.10+, open the project folder in VS Code, then run these commands in the PowerShell terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

See `README.md` for troubleshooting and tests.
