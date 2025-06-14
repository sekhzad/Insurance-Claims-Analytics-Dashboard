import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.express as px
import pandas as pd
# Load dataset
df = pd.read_csv('sales_data.csv')

# Example cleaning steps
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna()

fig = px.line(df, x='Date', y='Sales Amount', color='Region')
fig.show()


st.set_page_config(page_title="Sales Dashboard", layout="wide")

# Title
st.title("📊 Sales Analytics Dashboard")

# Sidebar filters
regions = st.sidebar.multiselect("Select Region", df['Region'].unique(), default=df['Region'].unique())
filtered_df = df[df['Region'].isin(regions)]

# KPIs
total_sales = filtered_df['Sales Amount'].sum()
avg_sales = filtered_df['Sales Amount'].mean()

st.metric("Total Sales", f"${total_sales:,.2f}")
st.metric("Average Sales", f"${avg_sales:,.2f}")

# Visualizations
fig = px.line(filtered_df, x='Date', y='Sales Amount', color='Region')
st.plotly_chart(fig, use_container_width=True)

with st.expander("View raw data"):
    st.dataframe(filtered_df)

