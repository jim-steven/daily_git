import streamlit as st
import sqlite3
import pandas as pd
import dateutil.parser
from datetime import datetime, timedelta
import re

# Function to get data from the database
def get_data_from_db(db_path='git_logs.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists, if not create it
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS git_logs (
            date TEXT,
            repo TEXT,
            author TEXT,
            title TEXT,
            issue TEXT,
            summary TEXT,
            description TEXT,
            link TEXT
        )
    ''')
    conn.commit()

    query = "SELECT * FROM git_logs ORDER BY date DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to parse and format the date
def parse_date(date_string):
    try:
        date = dateutil.parser.parse(date_string)
        return date.strftime("%Y-%m-%d")
    except ValueError:
        return date_string

# Function to remove email from author name
def remove_email(author):
    return re.sub(r'\s*<.*?@.*?>', '', author).strip()

# Streamlit app
st.title('Daily Git Summaries')

# Load data
df = get_data_from_db()

# Check if the dataframe is empty
if df.empty:
    st.warning("No data available. The git_logs table is empty.")
else:
    df['date'] = df['date'].apply(parse_date)
    df['author'] = df['author'].apply(remove_email)

    # Date range selector
    date_range = st.date_input(
        "Select date range",
        value=(datetime.now() - timedelta(days=7), datetime.now()),
        max_value=datetime.now()
    )

    # Filter data based on date range
    mask = (df['date'] >= str(date_range[0])) & (df['date'] <= str(date_range[1]))
    filtered_df = df.loc[mask]

    # Group data by date and repo, and sort by date (most recent first)
    grouped = filtered_df.groupby(['date', 'repo']).apply(lambda x: x).reset_index(drop=True)
    grouped = grouped.sort_values('date', ascending=False)

    # Display summaries
    for date, group in grouped.groupby('date', sort=False):
        for repo, repo_group in group.groupby('repo'):
            st.header(f"{date} - {repo.capitalize()}")
            for _, row in repo_group.iterrows():
                tweet_it = " 📢 " if "release" in row['title'].lower() else ""
                st.markdown(f"<span style='font-weight: bold; font-size: 17px;'>[{row['author']}] {row['title']} [({row['issue']})]({row['links']}) {tweet_it} {tweet_it} {tweet_it} </span>", unsafe_allow_html=True)
                st.write(f"Summary: {row['summary']}")
                with st.expander("⨁ Description"):
                    st.write(row['description'])

    # Add a download button for CSV
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="git_summaries.csv",
        mime="text/csv",
    )
