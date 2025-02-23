import pandas as pd
import streamlit as st

# ✅ Load the dataset from GitHub
file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

try:
    df = pd.read_csv(file_url)  # ✅ Load CSV
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")  # ✅ Normalize column names

    # ✅ Convert the 'DATE' column to datetime format
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        st.error("Missing required column: 'DATE'. Please check your dataset.")
        st.stop()

    # ✅ Ensure required columns exist
    required_columns = {"insurance", "charge_description", "charge_code", "paid", "date"}
    if not required_columns.issubset(df.columns):
        st.error("CSV file is missing required columns. Please check your dataset.")
    else:
        # ✅ Streamlit App Layout
        st.title("Revenue Estimation Tool")

        # 📅 Date Range Selection
        st.sidebar.header("Filter by Date")
        min_date = df["date"].min()
        max_date = df["date"].max()
        start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        # ✅ Filter data based on selected date range
        df_filtered = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        # 📌 Select Insurance & Procedure
        insurance_options = df_filtered["insurance"].unique()
        selected_insurance = st.selectbox("Select Insurance:", insurance_options)

        # ✅ Summary Table for Selected Insurance
        payer_summary = df_filtered[df_filtered["insurance"] == selected_insurance].groupby(["charge_code", "charge_description"]).agg(
            avg_paid=("paid", "mean"),
            total_paid=("paid", "sum"),
            total_claims=("charge_code", "count")
        ).reset_index()

        st.subheader(f"Summary for {selected_insurance}")
        st.write(payer_summary)

        # 📌 Select Procedure for Revenue Projection
        procedure_options = payer_summary["charge_description"].unique()
        selected_procedure = st.selectbox("Select Procedure:", procedure_options)
        entered_volume = st.number_input("Enter Estimated Procedure Volume:", min_value=1, value=10)

        # ✅ Filter Data for Selected Procedure
        filtered_data = payer_summary[payer_summary["charge_description"] == selected_procedure]

        # ✅ Calculate Projected Revenue
        if not filtered_data.empty:
            avg_payment_per_procedure = filtered_data["avg_paid"].values[0]
            projected_revenue = avg_payment_per_procedure * entered_volume
            st.subheader(f"Projected Revenue: ${projected_revenue:,.2f}")
        else:
            st.warning("No data available for selected procedure and insurance.")

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
