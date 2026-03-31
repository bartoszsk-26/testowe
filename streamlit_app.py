import streamlit as st
import pandas as pd

st.title("📊 Product Accuracy Dashboard")

# -----------------------
# Upload CSV
# -----------------------
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # clean columns
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "")
    )
    df = df.rename(columns={"products": "product"})

    # calculate change
    df["change"] = df["week3"] - df["week2"]

    # -----------------------
    # Top 5 biggest changes
    # -----------------------
    top5 = df.sort_values("change", ascending=False).head(5)
    st.subheader("🔥 Top 5 Products — Largest Increase")
    st.dataframe(top5)

    # -----------------------
    # Average accuracy
    # -----------------------
    avg_week2 = df["week2"].mean()
    avg_week3 = df["week3"].mean()
    avg_diff = avg_week3 - avg_week2

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Week 2", f"{avg_week2:.2f}%")
    col2.metric("Avg Week 3", f"{avg_week3:.2f}%")
    col3.metric("Difference", f"{avg_diff:.2f}%")

    # -----------------------
    # Trends classification
    # -----------------------
    up = (df["change"] > 0).sum()
    down = (df["change"] < 0).sum()
    no_change = (df["change"] == 0).sum()

    trend_df = pd.DataFrame({
        "Trend": ["Up", "Down", "No Change"],
        "Count": [up, down, no_change]
    })

    st.subheader("📈 Trend Distribution")
    st.bar_chart(trend_df.set_index("Trend"))

    st.subheader("Change per Product")
    st.bar_chart(df.set_index("product")["change"])

else:
    st.info("Upload a CSV file to start.")
