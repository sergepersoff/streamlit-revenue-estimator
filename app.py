import pandas as pd
import streamlit as st

# ✅ Load the dataset from GitHub
file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

# Try loading the CSV with error handling
try:
    df = pd.read_csv(file_url)

    # ✅ Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ✅ Ensure required columns exist
    required_columns = {"insurance", "charge_description", "paid"}
    if not required_columns.issubset(df.columns):
        st.error("CSV file is missing required columns. Please check your dataset.")
    else:
        # ✅ Calculate average payment per procedure per insurance
        avg_payment = df.groupby(["insurance", "charge_description"]).agg(
            avg_paid=("paid", "mean")
        ).reset_index()

        # ✅ Streamlit App Layout
        st.title("Revenue Estimation Tool")

        # Select Insurance & Procedure
        insurance_options = avg_payment["insurance"].unique()
        procedure_options = avg_payment["charge_description"].unique()

        selected_insurance = st.selectbox("Select Insurance:", insurance_options)
        selected_procedure = st.selectbox("Select Procedure:", procedure_options)
        entered_volume = st.number_input("Enter Estimated Procedure Volume:", min_value=1, value=10)

        # ✅ Filter Data
        filtered_data = avg_payment[
            (avg_payment["insurance"] == selected_insurance) & 
            (avg_payment["charge_description"] == selected_procedure)
        ]

        # ✅ Calculate Projected Revenue
        if not filtered_data.empty:
            avg_payment_per_procedure = filtered_data["avg_paid"].values[0]
            projected_revenue = avg_payment_per_procedure * entered_volume
            st.subheader(f"Projected Revenue: ${projected_revenue:,.2f}")
        else:
            st.warning("No data available for selected procedure and insurance.")

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
