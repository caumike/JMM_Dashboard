# main_app.py - NDA Dashboard with Excel Upload Feature
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# Page config
st.set_page_config(
    page_title="NDA Dashboard",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []

# Title
st.title("📄 NDA Dashboard & Document QA System")
st.markdown("**Upload your daily NDA tracker to monitor performance**")

# File Upload Section
with st.container():
    st.markdown("### 📤 Upload Today's NDA Tracker")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose your NDA Tracker Excel file",
            type=['xlsx', 'xls'],
            help="Upload the daily Excel file from your Google Drive"
        )
    
    with col2:
        st.markdown("#### Quick Stats")
        if st.session_state.uploaded_data is not None:
            st.success("✅ File Loaded")
            st.metric("Last Update", datetime.now().strftime("%H:%M"))
        else:
            st.info("📁 No file loaded")

# Process uploaded file
if uploaded_file is not None:
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(uploaded_file)
        
        # Check which sheets are available
        available_sheets = excel_file.sheet_names
        
        # Try to read the Test Sheet (which has the actual data)
        if 'Test Sheet' in available_sheets:
            df = pd.read_excel(uploaded_file, sheet_name='Test Sheet')
        elif 'Sheet1' in available_sheets:
            df = pd.read_excel(uploaded_file, sheet_name='Sheet1')
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0)  # Read first sheet
        
        # Store in session state
        st.session_state.uploaded_data = df
        st.session_state.last_upload_time = datetime.now()
        
        # Also read Dashboard sheet if available
        if 'Dashboard' in available_sheets:
            st.session_state.dashboard_data = pd.read_excel(uploaded_file, sheet_name='Dashboard')
        
        # Read Run Log if available
        if 'Run Log' in available_sheets:
            st.session_state.run_log = pd.read_excel(uploaded_file, sheet_name='Run Log')
        
        st.success(f"✅ Successfully loaded {len(df)} NDA records from '{uploaded_file.name}'")
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

# Display KPIs if data is loaded
if st.session_state.uploaded_data is not None:
    df = st.session_state.uploaded_data
    
    # Calculate KPIs
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ndas = len(df)
        st.metric("📥 Total NDAs", total_ndas)
    
    with col2:
        if 'Status' in df.columns:
            assigned = len(df[df['Status'] == 'Assigned'])
            st.metric("📋 Assigned", assigned)
        else:
            st.metric("📋 Assigned", "N/A")
    
    with col3:
        if 'Status' in df.columns:
            completed = len(df[df['Status'] == 'Completed'])
            st.metric("✅ Completed", completed)
        else:
            st.metric("✅ Completed", "N/A")
    
    with col4:
        if 'Turnaround Time (hrs)' in df.columns:
            avg_turnaround = df['Turnaround Time (hrs)'].dropna().mean()
            st.metric("⏱️ Avg Turnaround", f"{avg_turnaround:.1f}h" if not pd.isna(avg_turnaround) else "N/A")
        else:
            st.metric("⏱️ Avg Turnaround", "N/A")
    
    with col5:
        if 'Customer' in df.columns:
            unique_customers = df['Customer'].nunique()
            st.metric("🏢 Customers", unique_customers)
        else:
            st.metric("🏢 Customers", "N/A")
    
    st.divider()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📧 NDA Threads", "📊 Analytics", "📈 Trends", "📋 Run Log"])
    
    # Tab 1: NDA Threads
    with tab1:
        st.header("NDA Email Threads")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Status' in df.columns:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=df['Status'].dropna().unique().tolist(),
                    default=df['Status'].dropna().unique().tolist()
                )
            else:
                status_filter = []
        
        with col2:
            if 'Customer' in df.columns:
                customer_filter = st.multiselect(
                    "Filter by Customer",
                    options=df['Customer'].dropna().unique().tolist(),
                    default=[]
                )
            else:
                customer_filter = []
        
        with col3:
            search_term = st.text_input("🔍 Search in Subject", "")
        
        # Apply filters
        filtered_df = df.copy()
        
        if status_filter and 'Status' in df.columns:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        
        if customer_filter and 'Customer' in df.columns:
            filtered_df = filtered_df[filtered_df['Customer'].isin(customer_filter)]
        
        if search_term and 'Subject' in df.columns:
            filtered_df = filtered_df[filtered_df['Subject'].str.contains(search_term, case=False, na=False)]
        
        # Display filtered data
        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} records**")
        
        # Format the dataframe for display
        display_columns = []
        if 'Timestamp' in filtered_df.columns:
            display_columns.append('Timestamp')
        if 'From' in filtered_df.columns:
            display_columns.append('From')
        if 'Subject' in filtered_df.columns:
            display_columns.append('Subject')
        if 'Status' in filtered_df.columns:
            display_columns.append('Status')
        if 'Customer' in filtered_df.columns:
            display_columns.append('Customer')
        if 'Turnaround Time (hrs)' in filtered_df.columns:
            display_columns.append('Turnaround Time (hrs)')
        
        if display_columns:
            st.dataframe(
                filtered_df[display_columns],
                use_container_width=True,
                height=400
            )
        else:
            st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # Export filtered data
        if len(filtered_df) > 0:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"nda_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Tab 2: Analytics
    with tab2:
        st.header("Analytics Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Status Distribution")
            if 'Status' in df.columns:
                status_counts = df['Status'].value_counts()
                st.bar_chart(status_counts)
            else:
                st.info("Status column not found in data")
        
        with col2:
            st.subheader("Top Customers")
            if 'Customer' in df.columns:
                customer_counts = df['Customer'].value_counts().head(10)
                st.bar_chart(customer_counts)
            else:
                st.info("Customer column not found in data")
        
        # Turnaround time analysis
       # Fix for the Analytics tab - replace the problematic section around line 240-250

        # Turnaround time analysis
        if 'Turnaround Time (hrs)' in df.columns:
            st.subheader("Turnaround Time Analysis")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_time = df['Turnaround Time (hrs)'].dropna().mean()
                st.metric("Average", f"{avg_time:.1f} hours" if not pd.isna(avg_time) else "N/A")
            
            with col2:
                median_time = df['Turnaround Time (hrs)'].dropna().median()
                st.metric("Median", f"{median_time:.1f} hours" if not pd.isna(median_time) else "N/A")
            
            with col3:
                max_time = df['Turnaround Time (hrs)'].dropna().max()
                st.metric("Maximum", f"{max_time:.1f} hours" if not pd.isna(max_time) else "N/A")
            
            # Distribution chart - FIXED VERSION
            turnaround_data = df['Turnaround Time (hrs)'].dropna()
            if len(turnaround_data) > 0:
                st.subheader("Turnaround Time Distribution")
                
                # Create bins and count
                bins = [0, 6, 12, 24, 48, 72, 100, 200, 500]
                labels = ['0-6h', '6-12h', '12-24h', '24-48h', '48-72h', '72-100h', '100-200h', '200h+']
                
                # Categorize the data
                binned_data = pd.cut(turnaround_data, bins=bins, labels=labels, include_lowest=True)
                bin_counts = binned_data.value_counts().sort_index()
                
                # Create a proper DataFrame for the chart
                chart_df = pd.DataFrame({
                    'Time Range': bin_counts.index.astype(str),
                    'Count': bin_counts.values
                })
                
                # Display as bar chart
                st.bar_chart(chart_df.set_index('Time Range'))
