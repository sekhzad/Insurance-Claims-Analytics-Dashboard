import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Insurance Claims Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("insurance_claims_data.csv", parse_dates=['Date'])
    if 'Claim ID' not in df.columns:
        df.insert(0, 'Claim ID', range(1, len(df) + 1))
    return df

# Load data
df = load_data()

st.title("📑 Insurance Claims Analytics Dashboard")

# Sidebar filters
st.sidebar.header("🔧 Filter Claims")
regions = st.sidebar.multiselect("Select Region", df['Region'].unique(), default=df['Region'].unique())
policy_types = st.sidebar.multiselect("Select Policy Type", df['Policy Type'].unique(), default=df['Policy Type'].unique())
vehicle_types = st.sidebar.multiselect("Select Vehicle Type", df['Vehicle Type'].unique(), default=df['Vehicle Type'].unique())
genders = st.sidebar.multiselect("Select Gender", df['Gender'].unique(), default=df['Gender'].unique())
status_filter = st.sidebar.multiselect("Select Claim Status", df['Claim Status'].unique(), default=df['Claim Status'].unique())

date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])

filtered_df = df[
    (df['Region'].isin(regions)) &
    (df['Policy Type'].isin(policy_types)) &
    (df['Vehicle Type'].isin(vehicle_types)) &
    (df['Gender'].isin(genders)) &
    (df['Claim Status'].isin(status_filter)) &
    (df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Claims", f"${filtered_df['Claim Amount'].sum():,.2f}")
col2.metric("Average Claim", f"${filtered_df['Claim Amount'].mean():,.2f}")
approved_claims = filtered_df[filtered_df['Claim Status'] == 'Approved']['Claim Amount'].sum()
col3.metric("Approved Claims", f"${approved_claims:,.2f}")

# Dynamic Summary Statistics
st.subheader("📈 Summary Statistics")
summary_cols = st.multiselect("Select statistics to display", ['count','mean','std','min','25%','50%','75%','max'], default=['count','mean','min','max'])
summary = filtered_df['Claim Amount'].describe()[summary_cols].apply(lambda x: f"{x:,.2f}")
st.dataframe(summary)

# Claims Count by Status
claim_status_counts = filtered_df['Claim Status'].value_counts()
st.write("### Claims Count by Status")
st.bar_chart(claim_status_counts)

# Correlation Heatmap
st.write("### 🔥 Correlation Heatmap")
corr = filtered_df.select_dtypes(include=[np.number]).corr()
fig_heatmap, ax = plt.subplots()
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
st.pyplot(fig_heatmap)

# Charts
st.subheader("📊 Visual Analytics")
fig1 = px.line(filtered_df, x='Date', y='Claim Amount', color='Policy Type', title='Claim Amount Over Time')
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(filtered_df, x='Region', y='Claim Amount', color='Claim Status', barmode='group', title='Claims by Region and Status')
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.bar(filtered_df, x='Policy Type', y='Claim Amount', color='Claim Status', barmode='group', title='Claims by Policy Type')
st.plotly_chart(fig3, use_container_width=True)

fig4 = px.box(filtered_df, x='Vehicle Type', y='Claim Amount', color='Vehicle Type', title='Distribution of Claim Amounts by Vehicle Type')
st.plotly_chart(fig4, use_container_width=True)

# Data Table
with st.expander("🔎 View Detailed Claims Data"):
    st.dataframe(filtered_df[['Claim ID', 'Date', 'Region', 'Policy Type', 'Claim Amount', 'Claim Status', 'Customer Age', 'Gender', 'Vehicle Type', 'Previous Claims']].sort_values(by='Date', ascending=False))

# PDF Report Generation
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "Insurance Claims Report", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_summary(self, total, avg, approved):
        self.set_font("Arial", size=12)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, f"Total Claims: ${total:,.2f}", ln=True)
        self.cell(0, 10, f"Average Claim: ${avg:,.2f}", ln=True)
        self.cell(0, 10, f"Approved Claims: ${approved:,.2f}", ln=True)
        self.ln(5)

    def add_statistics(self, description):
        self.set_font("Arial", size=10)
        self.set_text_color(20, 20, 20)
        for index, value in description.items():
            self.cell(0, 8, f"{index}: {value}", ln=True)
        self.ln(5)

    def add_table(self, dataframe):
        self.set_font("Arial", "B", 10)
        self.set_fill_color(240, 240, 240)
        for col in ['Claim ID', 'Date', 'Region', 'Policy Type', 'Claim Amount', 'Claim Status']:
            self.cell(32, 8, col, border=1, fill=True)
        self.ln()

        self.set_font("Arial", size=9)
        for _, row in dataframe.iterrows():
            self.cell(32, 8, str(row['Claim ID']), border=1)
            self.cell(32, 8, row['Date'].strftime('%Y-%m-%d'), border=1)
            self.cell(32, 8, str(row['Region']), border=1)
            self.cell(32, 8, str(row['Policy Type']), border=1)
            self.cell(32, 8, f"${row['Claim Amount']:,.2f}", border=1)
            self.cell(32, 8, str(row['Claim Status']), border=1)
            self.ln()

if st.button("📄 Generate PDF Report"):
    pdf = PDF()
    pdf.add_page()
    pdf.add_summary(filtered_df['Claim Amount'].sum(), filtered_df['Claim Amount'].mean(), approved_claims)
    pdf.add_statistics(filtered_df['Claim Amount'].describe().apply(lambda x: f"{x:,.2f}").to_dict())
    pdf.add_table(filtered_df.head(30))  # Limit rows for readability
    st.download_button("⬇️ Download PDF", data=bytes(pdf.output(dest='S')), file_name="insurance_claims_report.pdf")

# Download button for CSV
st.download_button("⬇️ Download Filtered Data", filtered_df.to_csv(index=False), "filtered_claims.csv")