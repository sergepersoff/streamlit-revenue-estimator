import pandas as pd
import streamlit as st

# ✅ Load the dataset from GitHub
file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

try:
    df = pd.read_csv(file_url, dtype={"charge_code": str})  # ✅ Force 'charge_code' (CPT) as string
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
        # ✅ Force 'charge_code' (CPT) as a string again, just in case
        df["charge_code"] = df["charge_code"].astype(str)

        # ✅ Ensure 'paid' is always positive
        df["paid"] = df["paid"].abs()

        # ✅ Remove procedures where 'paid' = 0
        df = df[df["paid"] > 0]

        # ✅ Streamlit App Layout
        st.title("Revenue Estimation Tool")

        # 📅 Date Range Selection
        st.sidebar.header("Filter by Date")
        min_date = df["date"].min()
        max_date = df["date"].max()
        start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        # ✅ Filter data based on selected date range
        df_filtered = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        # 📌 Select Insurance
        insurance_options = df_filtered["insurance"].unique()
        selected_insurance = st.selectbox("Select Insurance:", insurance_options)

        # ✅ Filter Procedures Based on Selected Insurance
        df_insurance_filtered = df_filtered[df_filtered["insurance"] == selected_insurance]

        # ✅ Summary Table for Selected Insurance (EXCLUDES $0 Payments)
        payer_summary = df_insurance_filtered.groupby(["charge_code", "charge_description"]).agg(
            avg_paid=("paid", "mean"),
            total_paid=("paid", "sum"),
            total_claims=("charge_code", "count")
        ).reset_index()

        # ✅ Round avg_paid and total_paid to 1 decimal place
        payer_summary["avg_paid"] = payer_summary["avg_paid"].round(1)
        payer_summary["total_paid"] = payer_summary["total_paid"].round(1)

        # ✅ Add Grand Total Row
        grand_total = pd.DataFrame({
            "charge_code": ["GRAND TOTAL"],
            "charge_description": [""],
            "avg_paid": [payer_summary["avg_paid"].mean().round(1)],
            "total_paid": [payer_summary["total_paid"].sum().round(1)],
            "total_claims": [payer_summary["total_claims"].sum()]
        })

        # ✅ Append Grand Total to Summary Table
        payer_summary = pd.concat([payer_summary, grand_total], ignore_index=True)

        # ✅ Display Summary Table
        st.subheader(f"Summary for {selected_insurance}")
        st.write(payer_summary)

        # 📌 **Update Procedure Selection to Only Show Procedures for Selected Insurance**
        payer_summary["procedure_display"] = payer_summary["charge_code"] + " - " + payer_summary["charge_description"]
        procedure_options = payer_summary[payer_summary["charge_code"] != "GRAND TOTAL"]["procedure_display"].unique()  # Exclude Grand Total from dropdown

        selected_procedure = st.selectbox("Select Procedure (CPT - Description):", procedure_options)

        # ✅ Extract Selected CPT Code & Procedure
        selected_cpt_code, selected_procedure_desc = selected_procedure.split(" - ", 1)

        # ✅ Filter Data for Selected Procedure
        filtered_data = payer_summary[
            (payer_summary["charge_code"] == selected_cpt_code) &
            (payer_summary["charge_description"] == selected_procedure_desc)
        ]

        # ✅ Get the default total_claims for the selected procedure
        default_claims = int(filtered_data["total_claims"].values[0]) if not filtered_data.empty else 1

        # 📌 **Enter Estimated Procedure Volume (Defaults to total_claims)**
        entered_volume = st.number_input("Enter Estimated Procedure Volume:", min_value=1, value=default_claims)

        # ✅ Calculate Projected Revenue
        if not filtered_data.empty:
            avg_payment_per_procedure = filtered_data["avg_paid"].values[0]
            projected_revenue = avg_payment_per_procedure * entered_volume
            st.subheader(f"Projected Revenue: ${projected_revenue:,.2f}")
        else:
            st.warning("No data available for selected procedure and insurance.")

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
