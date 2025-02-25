import pandas as pd
import streamlit as st
import plotly.express as px

file_url = "https://raw.githubusercontent.com/sergepersoff/streamlit-revenue-estimator/main/ABC%20Billing%20report%20through%2002112024%20by%20DOS%20compiled.csv"

try:
    df = pd.read_csv(file_url, dtype={"charge_code": str, "account": str})  
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")  

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        st.error("Missing required column: 'DATE'. Please check your dataset.")
        st.stop()

    required_columns = {"account", "insurance", "charge_description", "charge_code", "paid", "date"}
    if not required_columns.issubset(df.columns):
        st.error("CSV file is missing required columns. Please check your dataset.")
    else:
        df["charge_code"] = df["charge_code"].astype(str)
        df["paid"] = df["paid"].abs()  
        df = df[df["paid"] > 0]  
        st.title("Revenue Estimation Tool")

        st.sidebar.header("Filter by Date")
        min_date = df["date"].min()
        max_date = df["date"].max()
        start_date, end_date = st.sidebar.date_input(
            "Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date
        )

        df_filtered = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        insurance_options = ["All Insurances"] + list(df_filtered["insurance"].unique())
        selected_insurance = st.selectbox("Select Insurance:", insurance_options)

        if selected_insurance == "All Insurances":
            df_insurance_filtered = df_filtered  # Show all insurances
        else:
            df_insurance_filtered = df_filtered[df_filtered["insurance"] == selected_insurance]

        st.subheader("📈 Visits Over Time (Filtered by Date & Insurance)")

        visits_over_time = df_insurance_filtered.groupby("date")["account"].nunique().reset_index()
        visits_over_time = visits_over_time.sort_values("date")

        total_visits = visits_over_time["account"].sum()
        st.metric(label="Total Visits", value=f"{total_visits:,}")

        fig_visits = px.line(
            visits_over_time,
            x="date",
            y="account",
            markers=True,
            title=f"Visits Over Time ({selected_insurance})",
            labels={"account": "Unique Visits", "date": "Date of Service (DOS)"},
            template="plotly_dark",
        )

        fig_visits.update_traces(
            hovertemplate="<b>Date:</b> %{x}<br><b>Visits:</b> %{y}<extra></extra>"
        )

        st.plotly_chart(fig_visits, use_container_width=True)

        total_paid_selected = df_insurance_filtered["paid"].sum()
        st.metric(label="Paid", value=f"${total_paid_selected:,.2f}")

        payer_summary = df_insurance_filtered.groupby(["charge_code", "charge_description"]).agg(
            avg_paid=("paid", "mean"),
            total_paid=("paid", "sum"),
            total_claims=("charge_code", "count")
        ).reset_index()

        payer_summary["avg_paid"] = payer_summary["avg_paid"].round(1)
        payer_summary["total_paid"] = payer_summary["total_paid"].round(1)

        grand_total = pd.DataFrame({
            "charge_code": ["GRAND TOTAL"],
            "charge_description": [""],
            "avg_paid": [payer_summary["avg_paid"].mean().round(1)],
            "total_paid": [payer_summary["total_paid"].sum().round(1)],
            "total_claims": [payer_summary["total_claims"].sum()]
        })

        payer_summary = pd.concat([payer_summary, grand_total], ignore_index=True)

        st.sidebar.header("Display Options")
        compact_view = st.sidebar.checkbox("Compact View", value=False, help="Hide charge descriptions in the summary table")

        st.subheader(f"Summary for {selected_insurance}")
        if compact_view:
            display_summary = payer_summary[["charge_code", "avg_paid", "total_paid", "total_claims"]]
        else:
            display_summary = payer_summary
            
        st.dataframe(display_summary, hide_index=True, use_container_width=True)

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

        st.subheader("📊 Total Payments Per CPT Code")

        sorted_payer_summary = payer_summary[payer_summary["charge_code"] != "GRAND TOTAL"].sort_values(by="total_paid", ascending=False)

        fig_cpt = px.bar(
            sorted_payer_summary,
            x="total_paid",
            y="charge_code",
            orientation="h",
            title=f"Total Payments Per CPT Code ({selected_insurance})",
            labels={"total_paid": "Total Paid ($)", "charge_code": "CPT Code"},
            template="plotly_dark",
            text_auto=True
        )
        st.plotly_chart(fig_cpt, use_container_width=True)

except Exception as e:
    st.error(f"Error loading CSV file: {e}")
