import streamlit as st
import pandas as pd
import requests
import os

# 🔥 FIX PROXY ISSUE
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

#API = "http://127.0.0.1:8000"
API = "https://your-api-url.onrender.com"

st.set_page_config(page_title="DC MIS Dashboard", layout="wide")

st.sidebar.title("📊 DC MIS Dashboard")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Entry", "Edit Entry"])


# =========================
# SESSION INIT
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# =========================
# 🔐 SIMPLE USER STORE
# =========================
USERS = {
    "admin": "admin123",
    "paul": "1234"
}


def login(username, password):
    return USERS.get(username) == password



# =========================
# 🔐 LOGIN SCREEN
# =========================
if not st.session_state.logged_in:

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()


    
# =========================
# LOAD DATA
# =========================
def load_data():
    try:
        res = requests.get(f"{API}/dc/data", proxies={})
        if res.status_code == 200:
            df = pd.DataFrame(res.json())

            if not df.empty:
                df.columns = df.columns.str.lower()

                df.rename(columns={
                    "id": "ID",
                    "dc_date": "DC_Date",
                    "distributor": "Distributor",
                    "amount": "Amount"
                }, inplace=True)

            return df

        return pd.DataFrame()

    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

# =========================
# 📊 DASHBOARD (ADVANCED)
# =========================
if menu == "Dashboard":

    st.title("📊 DC MIS Dashboard")

    df = load_data()

    if not df.empty:

        # -------------------------
        # DATA CLEANING
        # -------------------------
        df["DC_Date"] = pd.to_datetime(df["DC_Date"], errors="coerce")
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

        # -------------------------
        # 📅 DATE FILTER
        # -------------------------
        st.sidebar.subheader("📅 Filter Data")

        min_date = df["DC_Date"].min()
        max_date = df["DC_Date"].max()

        start_date = st.sidebar.date_input("From", min_date)
        end_date = st.sidebar.date_input("To", max_date)

        filtered_df = df[
            (df["DC_Date"] >= pd.to_datetime(start_date)) &
            (df["DC_Date"] <= pd.to_datetime(end_date))
        ]

        if filtered_df.empty:
            st.warning("No data for selected date range")
            st.stop()

        # -------------------------
        # 📊 KPIs
        # -------------------------
        total_amount = filtered_df["Amount"].sum()
        total_records = len(filtered_df)

        latest_date = filtered_df["DC_Date"].max()
        latest_date = latest_date.strftime("%d-%m-%Y")

        top_dist = (
            filtered_df.groupby("Distributor")["Amount"]
            .sum()
            .idxmax()
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("💰 Total Amount", f"₹ {total_amount:,.0f}")
        col2.metric("📄 Records", total_records)
        col3.metric("📅 Latest Entry", latest_date)
        col4.metric("🏆 Top Distributor", top_dist)

        st.divider()

        # -------------------------
        # 📈 TREND CHART (DATE)
        # -------------------------
        st.subheader("📈 Daily Trend")

        trend = (
            filtered_df.groupby("DC_Date")["Amount"]
            .sum()
            .reset_index()
        )

        st.line_chart(trend.set_index("DC_Date"))

        # -------------------------
        # 📊 DISTRIBUTOR ANALYSIS
        # -------------------------
        st.subheader("📊 Distributor Performance")

        dist_chart = (
            filtered_df.groupby("Distributor")["Amount"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(dist_chart)

        # -------------------------
        # 📅 MONTHLY MIS
        # -------------------------
        st.subheader("📅 Monthly MIS")

        filtered_df["Month"] = filtered_df["DC_Date"].dt.to_period("M").astype(str)

        monthly = (
            filtered_df.groupby("Month")["Amount"]
            .sum()
            .reset_index()
        )

        st.dataframe(monthly, use_container_width=True)

        st.bar_chart(monthly.set_index("Month"))

        # -------------------------
        # 📋 EDITABLE TABLE
        # -------------------------
        st.subheader("📋 Editable Data")

        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("💾 Save Changes"):
            for _, row in edited_df.iterrows():
                requests.put(
                    f"{API}/dc/edit/{row['ID']}",
                    json={
                        "dc_date": str(row["DC_Date"]),
                        "distributor": row["Distributor"],
                        "amount": float(row["Amount"])
                    },
                    proxies={}
                )

            st.success("Changes saved")
            st.rerun()

        # -------------------------
        # 📥 DOWNLOAD
        # -------------------------
        if st.button("⬇️ Download Report"):
            res = requests.get(f"{API}/dc/download", proxies={})

            if res.status_code == 200:
                st.download_button(
                    "Download Excel",
                    res.content,
                    file_name="DC_Report.xlsx"
                )
            else:
                st.error("Download failed")

    else:
        st.warning("No data available")
        

        # DELETE
        st.subheader("🗑 Delete Entry")
        delete_id = st.number_input("Enter ID to delete", min_value=1)

        if st.button("Delete"):
            res = requests.delete(f"{API}/dc/delete/{delete_id}", proxies={})
            if res.status_code == 200:
                st.success("Deleted successfully")
                st.rerun()
            else:
                st.error("Delete failed")

        else:
            st.warning("No data available")


# =========================
# ➕ ADD ENTRY
# =========================
elif menu == "Add Entry":

    st.title("➕ Add Entry")

    with st.form("add_form"):
        dc_date = st.date_input("Date")
        distributor = st.text_input("Distributor")
        amount = st.number_input("Amount", min_value=0)

        submit = st.form_submit_button("Add Entry")

        if submit:
            res = requests.post(
                f"{API}/dc/add",
                json={
                    "dc_date": str(dc_date),
                    "distributor": distributor,
                    "amount": amount
                },
                proxies={}
            )

            if res.status_code == 200:
                st.success("✅ Entry Added Successfully")
                st.rerun()
            else:
                st.error(f"❌ Failed ({res.status_code})")


# =========================
# ✏️ EDIT ENTRY (FORM BASED)
# =========================
elif menu == "Edit Entry":

    st.title("✏️ Edit Entry")

    df = load_data()

    if df.empty:
        st.warning("No data available")
    else:

        if "ID" not in df.columns:
            st.error("ID column missing from API response")
            st.stop()

        edit_id = st.selectbox("Select ID to Edit", df["ID"])

        row = df[df["ID"] == edit_id]

        if not row.empty:
            row = row.iloc[0]

            new_date = st.date_input("Date", pd.to_datetime(row["DC_Date"]))
            new_dist = st.text_input("Distributor", row["Distributor"])
            new_amt = st.number_input("Amount", value=float(row["Amount"]))

            if st.button("Update"):
                res = requests.put(
                    f"{API}/dc/edit/{edit_id}",
                    json={
                        "dc_date": str(new_date),
                        "distributor": new_dist,
                        "amount": new_amt
                    },
                    proxies={}
                )

                if res.status_code == 200:
                    st.success("Updated successfully")
                    st.rerun()
                else:
                    st.error("Update failed")


if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()
