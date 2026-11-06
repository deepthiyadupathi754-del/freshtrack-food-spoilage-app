"""FreshTrack: simple perishable inventory and waste-prevention dashboard."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from db import DB_PATH, add_item, get_movements, init_db, list_items, record_sales, sales_summary, update_stock


st.set_page_config(page_title="FreshTrack | Perishable Inventory", page_icon="🥬", layout="wide")
init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
.stApp {background: linear-gradient(155deg,#f5faf5 0%,#f4f7f4 50%,#eef5f1 100%); color:#17251e;}
h1,h2,h3 {font-family:'Manrope',sans-serif!important; letter-spacing:-.035em;}
.block-container {padding-top:2.2rem; max-width:1440px;}
div[data-testid="stMetric"] {background:white; border:1px solid #e2ebe3; padding:18px 20px; border-radius:17px; box-shadow:0 5px 18px #203e2710;}
div[data-testid="stMetricLabel"] {color:#66766b;}
.hero {background:linear-gradient(120deg,#153b2d,#286147); color:white; padding:28px 32px; border-radius:22px; margin-bottom:18px;}
.hero p {color:#d5e8d9; margin-bottom:0;}
.hint {color:#607267; font-size:.9rem;}
button[kind="primary"] {background:#1f7149; border-color:#1f7149;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🥬 FreshTrack")
    st.caption("Perishable inventory, made easier")
    role = st.selectbox("Working as", ["Manager", "Staff"])
    page = st.radio("Workspace", ["Overview", "Inventory", "Record sales", "Stock movements"], label_visibility="collapsed")
    st.divider()
    st.caption(f"Local database: `{DB_PATH.name}`")
    st.caption("Role is a workspace view, not a sign-in security control.")

items = list_items()
today = date.today()
expiry_soon = [x for x in items if today <= date.fromisoformat(x["expiry_date"]) <= today + timedelta(days=3)]
expired = [x for x in items if date.fromisoformat(x["expiry_date"]) < today]
low = [x for x in items if x["quantity"] <= x["reorder_level"]]

if page == "Overview":
    st.markdown('<div class="hero"><h1>Less waste. Better stock decisions.</h1><p>Track what is on hand, act before items expire, and use your recorded sales to estimate short-term demand.</p></div>', unsafe_allow_html=True)
    st.subheader("Today at a glance")
    a,b,c,d = st.columns(4)
    a.metric("Tracked items", len(items))
    b.metric("Expiring in 3 days", len(expiry_soon))
    c.metric("Already past expiry", len(expired))
    d.metric("At or below reorder level", len(low))
    left,right = st.columns([1.2, .8])
    with left:
        st.markdown("### ⏳ Expiry watch")
        watch = [x for x in items if date.fromisoformat(x["expiry_date"]) <= today + timedelta(days=7)]
        if watch:
            df = pd.DataFrame(watch)[["name","category","location","quantity","unit","expiry_date"]]
            st.dataframe(df, hide_index=True, width="stretch")
        else:
            st.success("No tracked items expire in the next 7 days.")
    with right:
        st.markdown("### 🛒 Reorder watch")
        if low:
            st.dataframe(pd.DataFrame(low)[["name","location","quantity","unit","reorder_level"]], hide_index=True, width="stretch")
        else:
            st.success("No items are at or below their reorder level.")
    st.markdown("### 📈 Demand estimate from recorded sales")
    summary = sales_summary()
    if summary:
        chart = pd.DataFrame(summary).set_index("name")[["sold_7d"]]
        st.bar_chart(chart, color="#33845a")
        st.caption("Bars show sales entered for the last 7 days. This is an estimate, not an automatic order; record daily sales to improve it.")
    else:
        st.info("Add inventory and record sales to see a demand estimate. No sample transactions are included.")

elif page == "Inventory":
    st.title("Inventory")
    st.caption("Add perishable stock, search it, filter by location and expiry, and export the current view.")
    with st.expander("＋ Add an inventory item", expanded=not items):
        with st.form("add_item", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            name = c1.text_input("Item name *", placeholder="e.g. Tomatoes")
            category = c2.text_input("Category *", placeholder="Produce, dairy…")
            location = c3.text_input("Location *", placeholder="Kitchen A / Store 1")
            c1,c2,c3 = st.columns(3)
            quantity = c1.number_input("Current quantity *", min_value=0.0, step=1.0)
            unit = c2.selectbox("Unit *", ["kg", "g", "L", "mL", "pieces", "packs", "boxes"])
            reorder = c3.number_input("Reorder level", min_value=0.0, step=1.0)
            c1,c2 = st.columns(2)
            expiry = c1.date_input("Expiry / best-before date *", value=today)
            supplier = c2.text_input("Supplier (optional)")
            submit = st.form_submit_button("Save item", type="primary")
            if submit:
                try:
                    if expiry < today:
                        raise ValueError("Expiry date cannot be in the past when adding current stock.")
                    add_item({"name":name,"category":category,"location":location,"quantity":quantity,"unit":unit,"reorder_level":reorder,"expiry_date":expiry.isoformat(),"supplier":supplier})
                    st.success(f"{name.strip()} added to inventory.")
                    st.rerun()
                except (ValueError, TypeError) as e:
                    st.error(str(e))
    if items:
        c1,c2,c3 = st.columns([1.5,1,1])
        query = c1.text_input("Search items", placeholder="Name, category, supplier…")
        locations = sorted(set(x["location"] for x in items))
        selected_loc = c2.selectbox("Location", ["All locations"] + locations)
        expiry_filter = c3.selectbox("Expiry", ["Any date", "Next 7 days", "Expired", "Not expired"])
        filtered=[]
        for x in items:
            exp = date.fromisoformat(x["expiry_date"])
            if query and query.casefold() not in " ".join(str(x[k]) for k in ("name","category","supplier","location")).casefold(): continue
            if selected_loc != "All locations" and x["location"] != selected_loc: continue
            if expiry_filter == "Next 7 days" and not today <= exp <= today+timedelta(days=7): continue
            if expiry_filter == "Expired" and exp >= today: continue
            if expiry_filter == "Not expired" and exp < today: continue
            filtered.append(x)
        view = pd.DataFrame(filtered)[["name","category","location","quantity","unit","reorder_level","expiry_date","supplier"]]
        st.dataframe(view, hide_index=True, width="stretch")
        st.download_button("Download current view as CSV", view.to_csv(index=False).encode("utf-8"), "freshtrack_inventory.csv", "text/csv")
        st.markdown("#### Record a stock adjustment")
        options = {f'{x["name"]} — {x["location"]} (on hand: {x["quantity"]} {x["unit"]})': x for x in items}
        with st.form("adjust_stock"):
            c1,c2,c3 = st.columns(3)
            selected = c1.selectbox("Item", list(options))
            delta = c2.number_input("Change quantity (negative for waste/use)", value=0.0, step=1.0)
            reason = c3.selectbox("Reason", ["Delivery received", "Used in production", "Waste / spoilage", "Count correction", "Other"])
            note = st.text_input("Note (optional)")
            if st.form_submit_button("Save stock movement"):
                try:
                    update_stock(options[selected]["id"], delta, reason, note)
                    st.success("Stock movement recorded.")
                    st.rerun()
                except ValueError as e: st.error(str(e))
    else: st.info("Your inventory is empty. Use ‘Add an inventory item’ to get started.")

elif page == "Record sales":
    st.title("Record daily sales")
    st.write("Enter quantities sold for a date. These records feed the simple 7-day average demand estimate.")
    if not items: st.info("Add an inventory item first.")
    else:
        options = {f'{x["name"]} — {x["location"]} ({x["unit"]})': x for x in items}
        with st.form("sales_form"):
            label = st.selectbox("Item", list(options))
            sold_on = st.date_input("Sales date", value=today, max_value=today)
            qty = st.number_input("Quantity sold", min_value=0.0, step=1.0)
            if st.form_submit_button("Save sales record", type="primary"):
                try:
                    record_sales(options[label]["id"], sold_on.isoformat(), qty)
                    st.success("Sales record saved. A same-day entry is updated if entered again.")
                except (ValueError, TypeError) as e: st.error(str(e))
        summary = sales_summary()
        st.markdown("### Sales-based stock outlook")
        if summary:
            data=[]
            for row in summary:
                data.append({"Item":row["name"],"On hand":f'{row["quantity"]:g} {row["unit"]}',"Sold last 7 days":row["sold_7d"],"Average / day":round(row["daily_average"],2),"Estimated days of stock":round(row["days_of_stock"],1) if row["days_of_stock"] is not None else "Enter sales"})
            st.dataframe(pd.DataFrame(data),hide_index=True,width="stretch")
            st.caption("Estimate = on-hand quantity ÷ (sales over last 7 calendar days ÷ 7). It is a planning aid; it does not place orders.")

else:
    st.title("Stock movements")
    st.caption("Latest stock additions, usage, spoilage, and corrections entered by staff.")
    movements = get_movements()
    if movements:
        df=pd.DataFrame(movements).rename(columns={"name":"Item","change":"Quantity change","unit":"Unit","reason":"Reason","note":"Note","created_at":"Recorded at"})
        st.dataframe(df[["Recorded at","Item","Quantity change","Unit","Reason","Note"]],hide_index=True,width="stretch")
        st.download_button("Download movement log as CSV",df.to_csv(index=False).encode("utf-8"),"freshtrack_movements.csv","text/csv")
    else: st.info("No movements recorded yet.")

st.divider()
st.caption("FreshTrack uses only records entered by your team. Forecasts are simple historical estimates and should be reviewed by a manager.")
