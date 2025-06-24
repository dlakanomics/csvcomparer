import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("CSV Comparator: Old vs New")

# File upload
st.sidebar.header("Upload CSV Files")
old_file = st.sidebar.file_uploader("Upload OLD CSV", type="csv")
new_file = st.sidebar.file_uploader("Upload NEW CSV", type="csv")

if old_file and new_file:
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)

    st.success("Files loaded successfully!")

    # Check column match
    if not all(col in new_df.columns for col in old_df.columns):
        st.error("Both CSVs must have the same columns.")
    else:
        st.sidebar.header("Comparison Settings")

        # Select identifier column
        id_col = st.sidebar.selectbox("Select identifier column", old_df.columns)

        # Select value column to compare
        compare_col = st.sidebar.selectbox("Select column to compare", [col for col in old_df.columns if col != id_col])

        # Merge on identifier column
        merged = pd.merge(
            old_df[[id_col, compare_col]].rename(columns={compare_col: "old_val"}),
            new_df[[id_col, compare_col]].rename(columns={compare_col: "new_val"}),
            on=id_col,
            how="inner"
        )

        # Optional: filter by pasted IDs (comma or newline separated)
        st.sidebar.markdown("### Filter by IDs (optional)")
        id_text = st.sidebar.text_area("Paste IDs (comma or newline separated)", height=150)

        if id_text.strip():
            raw_ids = [s.strip() for s in id_text.replace('\n', ',').split(',')]
            raw_ids = [s for s in raw_ids if s]  # remove empty strings

            # Try to cast to the right type if possible
            try:
                merged_id_type = merged[id_col].dtype
                if pd.api.types.is_numeric_dtype(merged_id_type):
                    raw_ids = [float(x) if '.' in x else int(x) for x in raw_ids]
            except Exception:
                pass  # fallback: use as-is

            merged = merged[merged[id_col].isin(raw_ids)]


        # Compute difference
        merged["diff"] = merged["new_val"] - merged["old_val"]

        # Show table preview
        st.subheader("Difference Table")
        st.dataframe(merged[[id_col, "old_val", "new_val", "diff"]])

        # Plot histogram
        st.subheader("Histogram of Differences")
        fig, ax = plt.subplots()
        ax.hist(merged["diff"], bins=20, edgecolor='black')
        ax.set_xlabel("Difference (new - old)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

        # Summary
        num_pos = (merged["diff"] > 0).sum()
        num_neg = (merged["diff"] < 0).sum()
        num_zero = (merged["diff"] == 0).sum()

        st.subheader("Summary")
        st.markdown(f"- 🔼 Positive differences: **{num_pos}**")
        st.markdown(f"- 🔽 Negative differences: **{num_neg}**")
        st.markdown(f"- ⚖️ Zero differences: **{num_zero}**")

        # Bar chart per ID
        st.subheader("Per-ID Difference Bar Chart")

        sorted_diff = merged.sort_values("diff", ascending=False)

        fig2, ax2 = plt.subplots(figsize=(10, 5))
        bar_colors = sorted_diff["diff"].apply(lambda x: "green" if x > 0 else "red" if x < 0 else "gray")
        ax2.bar(sorted_diff[id_col].astype(str), sorted_diff["diff"], color=bar_colors)
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.set_ylabel("Difference (new - old)")
        ax2.set_xlabel(id_col)
        ax2.set_title("Change per ID")
        plt.xticks(rotation=90)
        st.pyplot(fig2)

else:
    st.info("Please upload both old and new CSV files.")
