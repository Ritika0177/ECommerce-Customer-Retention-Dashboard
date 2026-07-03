"""
Customer Attrition & Workforce Retention System
--------------------------------------------------
Flipkart-style portfolio project bundling:
  1. A self-provisioning SQLite persistence layer (customer_retention.db)
  2. A Streamlit executive dashboard for churn monitoring

Run with:  streamlit run retention_app.py
"""

import os
import sqlite3
import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns


# CONFIG / CONSTANTS

DB_PATH = "customer_retention.db"
TABLE_NAME = "customer_logs"
REGIONS = ["North", "South", "East", "West"]
DEVICE_TYPES = ["Mobile", "Desktop"]
RISK_THRESHOLD_DAYS = 45
MIN_SEED_ROWS = 60  # comfortably clears the 50+ requirement

sns.set_style("whitegrid")



# 1. DATABASE LAYER

def _generate_signup_month_pool(months_back: int = 12) -> list:
    """Rolling window of 'Mon-YYYY' labels so charts read chronologically."""
    today = datetime.today().replace(day=1)
    pool = []
    for offset in range(months_back, 0, -1):
        month_date = today - timedelta(days=offset * 30)
        pool.append(month_date.strftime("%b-%Y"))
    return pool


def _synthesize_customer_row(customer_id: int, signup_pool: list) -> tuple:
    """
    Builds one logically-correlated mock record. Churn probability is not
    random noise -- it's biased by recency-of-purchase, mirroring how
    real attrition models behave (dormant customers churn more).
    """
    region = random.choice(REGIONS)
    device = random.choice(DEVICE_TYPES)
    signup_month = random.choice(signup_pool)
    days_since_last_purchase = random.randint(1, 120)
    total_purchases = max(1, int(random.gauss(18, 9)))

    # Correlated churn logic: dormancy past ~60 days sharply raises risk
    churn_probability = 0.05
    if days_since_last_purchase > 90:
        churn_probability = 0.85
    elif days_since_last_purchase > 60:
        churn_probability = 0.55
    elif days_since_last_purchase > 45:
        churn_probability = 0.30
    churn_status = 1 if random.random() < churn_probability else 0

    return (
        customer_id,
        signup_month,
        region,
        device,
        days_since_last_purchase,
        total_purchases,
        churn_status,
    )


def initialize_database(db_path: str = DB_PATH) -> None:
    """Creates the schema and seeds mock rows only on first run."""
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                Customer_ID INTEGER PRIMARY KEY,
                Signup_Month TEXT NOT NULL,
                Region TEXT NOT NULL,
                Device_Type TEXT NOT NULL,
                Days_Since_Last_Purchase INTEGER NOT NULL,
                Total_Purchases INTEGER NOT NULL,
                Churn_Status INTEGER NOT NULL
            )
            """
        )
        connection.commit()

        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        existing_row_count = cursor.fetchone()[0]

        if existing_row_count == 0:
            signup_pool = _generate_signup_month_pool()
            seed_rows = [
                _synthesize_customer_row(cid, signup_pool)
                for cid in range(1001, 1001 + MIN_SEED_ROWS)
            ]
            cursor.executemany(
                f"""
                INSERT INTO {TABLE_NAME}
                (Customer_ID, Signup_Month, Region, Device_Type,
                 Days_Since_Last_Purchase, Total_Purchases, Churn_Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                seed_rows,
            )
            connection.commit()

    except sqlite3.Error as db_error:
        st.error(f"Database provisioning failed: {db_error}")
    finally:
        connection.close()


@st.cache_data(show_spinner=False)
def load_customer_logs(db_path: str = DB_PATH) -> pd.DataFrame:
    """Pulls the full customer_logs table into a DataFrame for the UI layer."""
    try:
        connection = sqlite3.connect(db_path)
        retention_df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", connection)
        return retention_df
    except sqlite3.Error as db_error:
        st.error(f"Unable to read customer_logs: {db_error}")
        return pd.DataFrame()
    finally:
        connection.close()


# ------------------------------------------------------------------
# 2. STREAMLIT DASHBOARD
# ------------------------------------------------------------------
def render_sidebar_filters(source_df: pd.DataFrame) -> tuple:
    st.sidebar.header("Dashboard Filters")

    region_options = ["All"] + sorted(source_df["Region"].unique().tolist())
    device_options = ["All"] + sorted(source_df["Device_Type"].unique().tolist())

    selected_region = st.sidebar.selectbox("Region", region_options)
    selected_device = st.sidebar.selectbox("Device Type", device_options)

    return selected_region, selected_device


def apply_dashboard_filters(
    source_df: pd.DataFrame, region_choice: str, device_choice: str
) -> pd.DataFrame:
    filtered_retention_df = source_df.copy()

    if region_choice != "All":
        filtered_retention_df = filtered_retention_df[
            filtered_retention_df["Region"] == region_choice
        ]
    if device_choice != "All":
        filtered_retention_df = filtered_retention_df[
            filtered_retention_df["Device_Type"] == device_choice
        ]

    return filtered_retention_df


def render_executive_tiles(filtered_retention_df: pd.DataFrame) -> None:
    total_customers = len(filtered_retention_df)

    if total_customers == 0:
        avg_days_since_purchase = 0
        churn_rate_pct = 0.0
    else:
        avg_days_since_purchase = filtered_retention_df["Days_Since_Last_Purchase"].mean()
        churn_rate_pct = (
            filtered_retention_df["Churn_Status"].sum() / total_customers
        ) * 100

    tile_1, tile_2, tile_3 = st.columns(3)
    tile_1.metric("Total Scanned Customers", f"{total_customers:,}")
    tile_2.metric("Avg. Days Since Last Purchase", f"{avg_days_since_purchase:.1f}")
    tile_3.metric("Current Churn Rate", f"{churn_rate_pct:.1f}%")


def render_engagement_chart(filtered_retention_df: pd.DataFrame) -> None:
    st.subheader("Engagement by Signup Cohort")

    if filtered_retention_df.empty:
        st.warning("No records match the current filter combination.")
        return

    cohort_engagement = (
        filtered_retention_df.groupby(["Signup_Month", "Device_Type"])["Total_Purchases"]
        .sum()
        .reset_index()
    )

    pivoted_cohort = cohort_engagement.pivot(
        index="Signup_Month", columns="Device_Type", values="Total_Purchases"
    ).fillna(0)

    fig, ax = plt.subplots(figsize=(10, 5))
    pivoted_cohort.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")
    ax.set_xlabel("Signup Month")
    ax.set_ylabel("Total Purchases (Engagement)")
    ax.set_title("Purchase Engagement Stacked by Device Type per Cohort")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig)


def render_risk_zone_table(filtered_retention_df: pd.DataFrame) -> None:
    st.subheader("High-Risk Zone — Dormant Customers")

    risk_matrix_mask = (
        filtered_retention_df["Days_Since_Last_Purchase"] > RISK_THRESHOLD_DAYS
    )
    risk_zone_df = (
        filtered_retention_df[risk_matrix_mask]
        .sort_values(by="Days_Since_Last_Purchase", ascending=False)
        .reset_index(drop=True)
    )

    if risk_zone_df.empty:
        st.success("No customers currently exceed the dormancy risk threshold.")
        return

    st.dataframe(risk_zone_df, use_container_width=True)

    st.download_button(
        label="Export Risk Zone Segment (CSV)",
        data=risk_zone_df.to_csv(index=False).encode("utf-8"),
        file_name="high_risk_customer_segment.csv",
        mime="text/csv",
    )
    st.caption(
        f"{len(risk_zone_df)} customer(s) flagged with "
        f">{RISK_THRESHOLD_DAYS} days of inactivity."
    )


def main() -> None:
    st.set_page_config(
        page_title="Customer Attrition & Workforce Retention System",
        layout="wide",
    )
    st.title("Customer Attrition & Workforce Retention System")
    st.caption("Flipkart-style operational retention monitoring dashboard")

    try:
        if not os.path.exists(DB_PATH):
            initialize_database()
        else:
            initialize_database()  # no-op on existing populated DB

        retention_df = load_customer_logs()

        if retention_df.empty:
            st.error("No data available. Check database provisioning logs above.")
            return

        selected_region, selected_device = render_sidebar_filters(retention_df)
        filtered_retention_df = apply_dashboard_filters(
            retention_df, selected_region, selected_device
        )

        render_executive_tiles(filtered_retention_df)
        st.divider()
        render_engagement_chart(filtered_retention_df)
        st.divider()
        render_risk_zone_table(filtered_retention_df)

    except Exception as unexpected_error:
        st.error(f"Dashboard failed to render: {unexpected_error}")


if __name__ == "__main__":
    main()