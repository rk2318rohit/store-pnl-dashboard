"""
Kitchen P&L Analytics Dashboard
Made By : Rohit Kumar
Date    : May 2026

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Kitchen P&L Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Description
st.title("Kitchen P&L Analytics Dashboard")
st.markdown(
    "Profit & Loss analysis across cloud kitchen stores, cities, and zones. "
    "Data covers Oct 2023 - Mar 2024."
)
st.markdown("---")


# Data Loading (with caching for performance)

@st.cache_data
def load_data():
    df = pd.read_csv('data/kitchen_pnl_prepared.csv')
    df['MONTH'] = pd.to_datetime(df['MONTH'])
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filters")

selected_cities = st.sidebar.multiselect(
    "City",
    options=sorted(df['CITY'].unique()),
    default=sorted(df['CITY'].unique())
)

selected_zones = st.sidebar.multiselect(
    "Zone",
    options=sorted(df['ZONE MAPPING'].unique()),
    default=sorted(df['ZONE MAPPING'].unique())
)

selected_months = st.sidebar.multiselect(
    "Month",
    options=sorted(df['MONTH'].unique()),
    default=sorted(df['MONTH'].unique()),
    format_func=lambda x: pd.Timestamp(x).strftime('%b %Y')
)

selected_ebitda_cat = st.sidebar.multiselect(
    "EBITDA Category",
    options=sorted(df['EBITDA CATEGORY'].unique()),
    default=sorted(df['EBITDA CATEGORY'].unique())
)

selected_revenue_cat = st.sidebar.multiselect(
    "Revenue Category",
    options=sorted(df['REVENUE CATEGORY'].dropna().unique()),
    default=sorted(df['REVENUE CATEGORY'].dropna().unique())
)

st.sidebar.markdown("---")
st.sidebar.subheader("Range Filters")

ebitda_min, ebitda_max = float(df['KITCHEN EBITDA'].min()), float(df['KITCHEN EBITDA'].max())
ebitda_range = st.sidebar.slider(
    "EBITDA Range (₹)",
    min_value=ebitda_min,
    max_value=ebitda_max,
    value=(ebitda_min, ebitda_max),
    format="%.0f"
)

cm_min, cm_max = float(df['CM %'].min()), float(df['CM %'].max())
cm_range = st.sidebar.slider(
    "CM % Range",
    min_value=cm_min,
    max_value=cm_max,
    value=(cm_min, cm_max),
    format="%.2f"
)

revenue_min, revenue_max = float(df['NET REVENUE'].min()), float(df['NET REVENUE'].max())
revenue_range = st.sidebar.slider(
    "Net Revenue Range (₹)",
    min_value=revenue_min,
    max_value=revenue_max,
    value=(revenue_min, revenue_max),
    format="%.0f"
)

# Apply Filters
filtered_df = df[
    (df['CITY'].isin(selected_cities)) &
    (df['ZONE MAPPING'].isin(selected_zones)) &
    (df['MONTH'].isin(selected_months)) &
    (df['EBITDA CATEGORY'].isin(selected_ebitda_cat)) &
    (df['REVENUE CATEGORY'].isin(selected_revenue_cat)) &
    (df['KITCHEN EBITDA'].between(ebitda_range[0], ebitda_range[1])) &
    (df['CM %'].between(cm_range[0], cm_range[1])) &
    (df['NET REVENUE'].between(revenue_range[0], revenue_range[1]))
]

# Tabs: Dashboard 1 (Kitchen PNL) and Dashboard 2 (Variance PNL)
tab1, tab2 = st.tabs(["Kitchen-Level PNL", "Variance-Level PNL"])

# TAB 1 — KITCHEN-LEVEL PNL
with tab1:
    # KPI Cards
    st.subheader("Key Metrics (filtered)")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Revenue", f"₹{filtered_df['NET REVENUE'].sum()/10**7:.2f} Cr")
    with col2:
        st.metric("Total EBITDA", f"₹{filtered_df['KITCHEN EBITDA'].sum()/10**7:.2f} Cr")
    with col3:
        st.metric("Avg EBITDA %", f"{filtered_df['EBITDA %'].mean():.2f}%")
    with col4:
        st.metric("Unique Kitchens", f"{filtered_df.groupby(['CITY', 'STORE', 'ZONE MAPPING']).ngroups}")
    with col5:
        st.metric("Avg Variance %", f"{filtered_df['VARIANCE %'].mean():.2f}%")

    st.markdown("---")

    # Kitchen Snapshot Table
    st.subheader("Kitchen Snapshot")
    st.write(f"Showing **{len(filtered_df):,}** of **{len(df):,}** total rows")

    snapshot_cols = [
        'MONTH', 'CITY', 'STORE', 'ZONE MAPPING', 'STATUS',
        'NET REVENUE', 'GROSS MARGIN', 'KITCHEN EBITDA',
        'GM %', 'CM %', 'EBITDA %', 'VARIANCE %',
        'REVENUE CATEGORY', 'EBITDA CATEGORY'
    ]
    snapshot_df = filtered_df[snapshot_cols].copy()
    snapshot_df['MONTH'] = snapshot_df['MONTH'].dt.strftime('%b %Y')

    st.dataframe(
        snapshot_df.style.format({
            'NET REVENUE'    : '₹{:,.0f}',
            'GROSS MARGIN'   : '₹{:,.0f}',
            'KITCHEN EBITDA' : '₹{:,.0f}',
            'GM %'           : '{:.2f}%',
            'CM %'           : '{:.2f}%',
            'EBITDA %'       : '{:.2f}%',
            'VARIANCE %'     : '{:.2f}%',
        }).background_gradient(
            subset=['EBITDA %'],
            cmap='RdYlGn',
            vmin=-30,
            vmax=50
        ),
        height=500,
        use_container_width=True
    )

    # Monthly Trend Chart
    st.subheader("Monthly EBITDA Trend")
    monthly_trend = filtered_df.groupby(
        filtered_df['MONTH'].dt.strftime('%Y-%m')
    ).agg(
        total_revenue=('NET REVENUE', 'sum'),
        total_ebitda=('KITCHEN EBITDA', 'sum'),
    ).reset_index()
    st.line_chart(monthly_trend, x='MONTH', y=['total_revenue', 'total_ebitda'], height=400)

    # Download button
    st.download_button(
        label="Download filtered data as CSV",
        data=snapshot_df.to_csv(index=False).encode('utf-8'),
        file_name='kitchen_snapshot_filtered.csv',
        mime='text/csv'
    )


# ==================================================================
# TAB 2 — VARIANCE-LEVEL PNL
# ==================================================================
with tab2:
    st.subheader("Variance-Level PNL")
    st.markdown(
        "Variance analysis by revenue cohort. "
        "Use the Variance Category filter below to drill into specific wastage levels."
    )

    # Variance Category filter (specific to this tab)
    variance_cats_available = sorted(df['VARIANCE CATEGORY'].dropna().unique())
    selected_variance_cats = st.multiselect(
        "Variance Category",
        options=variance_cats_available,
        default=variance_cats_available,
        key="variance_cat_filter"
    )

    # Apply the variance category filter on top of the sidebar filters
    variance_df = filtered_df[
        filtered_df['VARIANCE CATEGORY'].isin(selected_variance_cats)
    ].copy()

    # Add formatted month column for clean pivot headers
    variance_df['MONTH_LABEL'] = variance_df['MONTH'].dt.strftime('%b %Y')

    # Determine chronological month order
    month_order = variance_df.sort_values('MONTH')['MONTH_LABEL'].unique().tolist()

    st.write(f"Working with **{len(variance_df):,}** rows after filtering.")
    st.markdown("---")

    # === Sub-dashboard A — Average Variance % by Revenue Cohort × Month ===
    st.subheader("Sub-dashboard A: Average Variance % by Revenue Cohort and Month")
    st.markdown(
        "_The table below summarizes the average variance % of kitchens "
        "under each revenue category across months._"
    )

    pivot_a = pd.pivot_table(
        variance_df,
        index='REVENUE CATEGORY',
        columns='MONTH_LABEL',
        values='VARIANCE %',
        aggfunc='mean',
        observed=True,
        margins=True,
        margins_name='Grand total'
    )
    pivot_a = pivot_a[month_order + ['Grand total']]

    st.dataframe(
        pivot_a.style.format('{:.2f}%', na_rep='-'),
        use_container_width=True
    )

    st.markdown("---")

    # === Sub-dashboard B — Store Count by Revenue Cohort × Month ===
    st.subheader("Sub-dashboard B: Store Count by Revenue Cohort and Month")
    st.markdown(
        "_The table below shows the count of unique kitchen stores "
        "for each revenue category, by month, filtered by the selected variance category._"
    )

    pivot_b = pd.pivot_table(
        variance_df,
        index='REVENUE CATEGORY',
        columns='MONTH_LABEL',
        values='STORE',
        aggfunc='nunique',
        observed=True,
        margins=True,
        margins_name='Grand total'
    )
    pivot_b = pivot_b[month_order + ['Grand total']]

    st.dataframe(
        pivot_b.style.format('{:.0f}', na_rep='-'),
        use_container_width=True
    )