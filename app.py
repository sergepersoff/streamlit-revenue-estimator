import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ✅ Load the dataset from GitHub
file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

try:
    df = pd.read_csv(file_url, dtype={"charge_code": str})  # ✅ Ensure 'charge_code' (CPT) is a string
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")  # ✅ Normalize column names

    # ✅ Convert 'DATE' column to datetime
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

        # 📌 **Grand Total of All Payments**
        grand_total_paid = df_filtered["paid"].sum()
        st.metric(label="💰 Total Payments Across All Insurances", value=f"${grand_total_paid:,.2f}")

        # 📌 **Select Insurance**
        insurance_options = df_filtered["insurance"].unique()
        selected_insurance = st.selectbox("Select Insurance:", insurance_options)

        # ✅ Filter Procedures Based on Selected Insurance
        df_insurance_filtered = df_filtered[df_filtered["insurance"] == selected_insurance]

        # ✅ Summary Table for Selected Insurance
        payer_summary = df_insurance_filtered.groupby(["charge_code", "charge_description"]).agg(
            avg_paid=("paid", "mean"),
            total_paid=("paid", "sum"),
            total_claims=("charge_code", "count")
        ).reset_index()

        # ✅ Round avg_paid and total_paid to 1 decimal place
        payer_summary["avg_paid"] = payer_summary["avg_paid"].round(1)
        payer_summary["total_paid"] = payer_summary["total_paid"].round(1)

        # ✅ Add Grand Total Row for the selected insurance
        grand_total = pd.DataFrame({
            "charge_code": ["GRAND TOTAL"],
            "charge_description": [""],
            "avg_paid": [payer_summary["avg_paid"].mean().round(1)],
            "total_paid": [payer_summary["total_paid"].sum().round(1)],
            "total_claims": [payer_summary["total_claims"].sum()]
        })

        # ✅ Append Grand Total to Summary Table
        payer_summary = pd.concat([payer_summary, grand_total], ignore_index=True)

        # 📱 **Compact View Toggle**
        st.sidebar.header("Display Options")
        compact_view = st.sidebar.checkbox("Compact View", value=False, help="Hide charge descriptions in the summary table")

        # ✅ Display Summary Table
        st.subheader(f"Summary for {selected_insurance}")
        if compact_view:
            display_summary = payer_summary[["charge_code", "avg_paid", "total_paid", "total_claims"]]
        else:
            display_summary = payer_summary
            
        st.dataframe(display_summary, hide_index=True, use_container_width=True)

        # 📌 **Update Procedure Selection to Show CPT Code + Description**
        payer_summary["procedure_display"] = payer_summary["charge_code"] + " - " + payer_summary["charge_description"]
        procedure_options = payer_summary[payer_summary["charge_code"] != "GRAND TOTAL"]["procedure_display"].unique()

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

        # 📊 **Dark-Themed Bar Chart with CPT Codes on X-Axis**
        st.subheader("📊 Total Payments Per CPT Code (Filtered by Date)")

        # ✅ Aggregate total paid per CPT code
        cpt_totals = df_filtered.groupby("charge_code")["paid"].sum().reset_index()

        # ✅ Sort by highest paid first
        cpt_totals = cpt_totals.sort_values(by="paid", ascending=False)

        # ✅ Dark mode styling
        plt.style.use("dark_background")

        # ✅ Plot bar chart (X-axis = CPT Codes, Y-axis = Total Paid)
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(cpt_totals["charge_code"], cpt_totals["paid"], color="deepskyblue")

        # ✅ Rotate X-axis labels to avoid overlap
        ax.set_xticks(range(len(cpt_totals["charge_code"])))
        ax.set_xticklabels(cpt_totals["charge_code"], rotation=45, ha="right")

        # ✅ Add value labels to each bar
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"${bar.get_height():,.0f}", ha='center', va='bottom', fontsize=10, color='white')

        ax.set_xlabel("CPT Code")
        ax.set_ylabel("Total Paid ($)")
        ax.set_title("Total Payments Per CPT Code (Filtered by Date)")
        st.pyplot(fig)

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
