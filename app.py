import pandas as pd
import streamlit as st
import plotly.express as px

# ✅ Load the dataset from GitHub
file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

try:
    df = pd.read_csv(file_url, dtype={"charge_code": str, "account": str})  # ✅ Ensure 'charge_code' & 'account' are strings
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")  # ✅ Normalize column names

    # ✅ Convert 'DATE' column to datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        st.error("Missing required column: 'DATE'. Please check your dataset.")
        st.stop()

    # ✅ Ensure required columns exist
    required_columns = {"account", "insurance", "charge_description", "charge_code", "paid", "date"}
    if not required_columns.issubset(df.columns):
        st.error("CSV file is missing required columns. Please check your dataset.")
    else:
        df["charge_code"] = df["charge_code"].astype(str)
        df["paid"] = df["paid"].abs()  # ✅ Ensure 'paid' is always positive
        df = df[df["paid"] > 0]  # ✅ Remove rows where 'paid' is 0

        # ✅ Streamlit App Layout
        st.title("Revenue Estimation Tool")

        # 📅 **Date Range Selection**
        st.sidebar.header("Filter by Date")
        min_date = df["date"].min()
        max_date = df["date"].max()
        start_date, end_date = st.sidebar.date_input(
            "Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date
        )

        # ✅ Filter data based on selected date range
        df_filtered = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        # 📌 **Select Insurance (Includes "All Insurances" Option)**
        insurance_options = ["All Insurances"] + list(df_filtered["insurance"].unique())
        selected_insurance = st.selectbox("Select Insurance:", insurance_options)

        # ✅ Filter Data Based on Insurance Selection
        if selected_insurance == "All Insurances":
            df_insurance_filtered = df_filtered  # Show all insurances
        else:
            df_insurance_filtered = df_filtered[df_filtered["insurance"] == selected_insurance]

        # 📊 **Visits Over Time (Unique Accounts per DOS)**
        st.subheader("📈 Visits Over Time (Filtered by Date & Insurance)")

        # ✅ Count unique accounts per DOS
        visits_over_time = df_insurance_filtered.groupby("date")["account"].nunique().reset_index()
        visits_over_time = visits_over_time.sort_values("date")

        # ✅ Calculate Total Visits
        total_visits = visits_over_time["account"].sum()
        st.metric(label="Total Visits", value=f"{total_visits:,}")

        # ✅ Plot Interactive Line Chart using Plotly
        fig_visits = px.line(
            visits_over_time,
            x="date",
            y="account",
            markers=True,
            title=f"Visits Over Time ({selected_insurance})",
            labels={"account": "Unique Visits", "date": "Date of Service (DOS)"},
            template="plotly_dark",  # ✅ Dark mode theme
        )

        # ✅ Customize hover tooltip
        fig_visits.update_traces(
            hovertemplate="<b>Date:</b> %{x}<br><b>Visits:</b> %{y}<extra></extra>"
        )

        # ✅ Display the plot
        st.plotly_chart(fig_visits, use_container_width=True)

        # 📌 **Dynamically Update "Paid" Metric**
        total_paid_selected = df_insurance_filtered["paid"].sum()
        st.metric(label="Paid", value=f"${total_paid_selected:,.2f}")

        # 📊 **Total Payments Per CPT Code (Filtered by Date & Insurance)**
        st.subheader("📊 Total Payments Per CPT Code")

        # ✅ Aggregate total paid per CPT code based on insurance selection
        cpt_totals = df_insurance_filtered.groupby("charge_code")["paid"].sum().reset_index()

        # ✅ Sort by highest paid first
        cpt_totals = cpt_totals.sort_values(by="paid", ascending=True)

        # ✅ Plot Interactive Bar Chart using Plotly
        fig_cpt = px.bar(
            cpt_totals,
            x="paid",
            y="charge_code",
            orientation="h",
            title=f"Total Payments Per CPT Code ({selected_insurance})",
            labels={"paid": "Total Paid ($)", "charge_code": "CPT Code"},
            template="plotly_dark",  # ✅ Dark mode theme
            text_auto=".2s"  # ✅ Show values on bars
        )

        # ✅ Display the plot
        st.plotly_chart(fig_cpt, use_container_width=True)

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
