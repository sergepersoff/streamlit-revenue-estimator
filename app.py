import pandas as pd
import streamlit as st
import plotly.express as px

file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

try:
    df = pd.read_csv(file_url, dtype={"charge_code": str}) 
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_") 

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        st.error("Missing required column: 'DATE'. Please check your dataset.")
        st.stop()

    required_columns = {"insurance", "charge_description", "charge_code", "paid", "date"}
    if not required_columns.issubset(df.columns):
        st.error("CSV file is missing required columns. Please check your dataset.")
    else:
        df["charge_code"] = df["charge_code"].astype(str)

        df["paid"] = df["paid"].abs()

        df = df[df["paid"] > 0]

        st.title("Revenue Estimation Tool")

        # Date Range Selection in sidebar
        st.sidebar.header("Filter by Date")
        min_date = df["date"].min()
        max_date = df["date"].max()
        start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        # Filter data based on selected date range
        df_filtered = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        # Calculate grand total for all insurances and procedures based on date filter
        grand_total_all = df_filtered["paid"].sum().round(2)
        
        # Display grand total at the top of the main panel
        st.subheader("All Insurance Payments")
        st.metric("Total Payments (All Insurances)", f"${grand_total_all:,.2f}")
        
        # Select Insurance dropdown
        insurance_options = df_filtered["insurance"].unique()
        selected_insurance = st.selectbox("Select Insurance:", insurance_options)

        # Filter for selected insurance
        df_insurance_filtered = df_filtered[df_filtered["insurance"] == selected_insurance]

        # Create summary for selected insurance
        payer_summary = df_insurance_filtered.groupby(["charge_code", "charge_description"]).agg(
            avg_paid=("paid", "mean"),
            total_paid=("paid", "sum"),
            total_claims=("charge_code", "count")
        ).reset_index()

        payer_summary["avg_paid"] = payer_summary["avg_paid"].round(1)
        payer_summary["total_paid"] = payer_summary["total_paid"].round(1)

        # Add Grand Total row
        grand_total = pd.DataFrame({
            "charge_code": ["GRAND TOTAL"],
            "charge_description": [""],
            "avg_paid": [payer_summary["avg_paid"].mean().round(1)],
            "total_paid": [payer_summary["total_paid"].sum().round(1)],
            "total_claims": [payer_summary["total_claims"].sum()]
        })

        payer_summary = pd.concat([payer_summary, grand_total], ignore_index=True)

        # Display options in sidebar
        st.sidebar.header("Display Options")
        compact_view = st.sidebar.checkbox("Compact View", value=False, help="Hide charge descriptions in the summary table")

        # Display summary table
        st.subheader(f"Summary for {selected_insurance}")
        
        if compact_view:
            display_summary = payer_summary[["charge_code", "avg_paid", "total_paid", "total_claims"]]
        else:
            display_summary = payer_summary
            
        st.write(display_summary)

        # Procedure selection
        payer_summary["procedure_display"] = payer_summary["charge_code"] + " - " + payer_summary["charge_description"]
        procedure_options = payer_summary[payer_summary["charge_code"] != "GRAND TOTAL"]["procedure_display"].unique()

        selected_procedure = st.selectbox("Select Procedure (CPT - Description):", procedure_options)

        selected_cpt_code, selected_procedure_desc = selected_procedure.split(" - ", 1)

        filtered_data = payer_summary[
            (payer_summary["charge_code"] == selected_cpt_code) &
            (payer_summary["charge_description"] == selected_procedure_desc)
        ]

        default_claims = int(filtered_data["total_claims"].values[0]) if not filtered_data.empty else 1

        entered_volume = st.number_input("Enter Estimated Procedure Volume:", min_value=1, value=default_claims)

        if not filtered_data.empty:
            avg_payment_per_procedure = filtered_data["avg_paid"].values[0]
            projected_revenue = avg_payment_per_procedure * entered_volume
            st.subheader(f"Projected Revenue: ${projected_revenue:,.2f}")
        else:
            st.warning("No data available for selected procedure and insurance.")
            
        # Create histogram of all procedures by all insurances
        # First, group by charge_code to get totals across all insurances
        all_procedures_summary = df_filtered.groupby("charge_code").agg(
            total_paid=("paid", "sum"),
        ).reset_index()
        
        # Sort by total_paid to show highest revenue procedures
        all_procedures_summary = all_procedures_summary.sort_values("total_paid", ascending=False)
        
        # Only show top 20 procedures for better visibility
        top_procedures = all_procedures_summary.head(20)
        
        st.subheader("Top 20 Procedures by Total Revenue (All Insurances)")
        
        # Create and display the histogram
        fig = px.bar(
            top_procedures,
            x="charge_code",
            y="total_paid",
            title=f"Top Procedures by Total Revenue (Date Range: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')})",
            labels={"charge_code": "CPT Code", "total_paid": "Total Revenue ($)"}
        )
        fig.update_layout(xaxis_title="CPT Code", yaxis_title="Total Revenue ($)")
        st.plotly_chart(fig)

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
