# main_app.py - Complete NDA Dashboard with Excel Upload Feature (FIXED VERSION)
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
        
        # Turnaround time analysis - FIXED VERSION
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
        
        # Dashboard data if available
        if 'dashboard_data' in st.session_state:
            st.subheader("Summary from Dashboard Sheet")
            st.dataframe(st.session_state.dashboard_data, use_container_width=True)
    
    # Tab 3: Trends
    with tab3:
        st.header("Trend Analysis")
        
        if 'Timestamp' in df.columns:
            # Convert timestamp to datetime
            df_copy = df.copy()
            df_copy['Date'] = pd.to_datetime(df_copy['Timestamp']).dt.date
            
            # Daily volume trend
            daily_counts = df_copy.groupby('Date').size().reset_index(name='Count')
            
            st.subheader("Daily NDA Volume")
            st.line_chart(daily_counts.set_index('Date'))
            
            # Status trend over time
            if 'Status' in df_copy.columns:
                st.subheader("Status Trend Over Time")
                status_trend = df_copy.groupby(['Date', 'Status']).size().unstack(fill_value=0)
                st.area_chart(status_trend)
            
            # Customer activity over time
            if 'Customer' in df_copy.columns:
                st.subheader("Top 5 Most Active Customers Over Time")
                top_customers = df_copy['Customer'].value_counts().head(5).index
                customer_trend = df_copy[df_copy['Customer'].isin(top_customers)].groupby(['Date', 'Customer']).size().unstack(fill_value=0)
                st.line_chart(customer_trend)
        else:
            st.info("Timestamp column not found - unable to show trends")
    
    # Tab 4: Run Log
    with tab4:
        st.header("Processing Run Log")
        
        if 'run_log' in st.session_state:
            run_log = st.session_state.run_log
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_runs = len(run_log)
                st.metric("Total Runs", total_runs)
            
            with col2:
                if 'NDAs Processed' in run_log.columns:
                    total_processed = run_log['NDAs Processed'].sum()
                    st.metric("Total NDAs Processed", int(total_processed))
            
            with col3:
                if 'Completed Count' in run_log.columns:
                    total_completed = run_log['Completed Count'].sum()
                    st.metric("Total Completed", int(total_completed))
            
            # Display run log
            st.subheader("Recent Runs (Last 20)")
            display_log = run_log.tail(20).copy()
            
            # Format the timestamp if it exists
            if 'Run Timestamp' in display_log.columns:
                display_log['Run Timestamp'] = pd.to_datetime(display_log['Run Timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(display_log, use_container_width=True)
            
            # Processing trend
            if 'Run Timestamp' in run_log.columns and 'NDAs Processed' in run_log.columns:
                st.subheader("Processing Trend")
                run_log_copy = run_log.copy()
                run_log_copy['Date'] = pd.to_datetime(run_log_copy['Run Timestamp']).dt.date
                daily_processing = run_log_copy.groupby('Date')['NDAs Processed'].sum()
                if len(daily_processing) > 0:
                    st.line_chart(daily_processing)
        else:
            st.info("Run Log sheet not found in uploaded file")

else:
    # Show instructions when no file is uploaded
    st.info("""
    ### 📤 How to use this dashboard:
    
    1. **Download your NDA Tracker** from Google Drive
    2. **Upload the Excel file** using the uploader above
    3. **View your KPIs and analytics** instantly
    
    The dashboard will automatically:
    - Parse all sheets in your Excel file
    - Calculate KPIs and metrics
    - Show status distribution and trends
    - Provide filtering and search capabilities
    - Allow data export in CSV format
    
    **Supported columns:**
    - Timestamp, From, Subject, Status, Customer
    - Thread ID, File Link, Completed Timestamp
    - Turnaround Time (hrs), Message Count, Audit Flag
    """)

# Sidebar
with st.sidebar:
    st.header("🔧 Dashboard Controls")
    
    if st.button("🔄 Clear Data", use_container_width=True):
        st.session_state.uploaded_data = None
        st.session_state.dashboard_data = None
        st.session_state.run_log = None
        st.rerun()
    
    st.divider()
    
    st.header("📊 Quick Stats")
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        st.success("✅ Data Loaded")
        st.metric("Total Records", len(df))
        if 'Status' in df.columns:
            st.metric("Unique Statuses", df['Status'].nunique())
        if 'Customer' in df.columns:
            st.metric("Unique Customers", df['Customer'].nunique())
    else:
        st.info("No data loaded")
    
    st.divider()
    
    st.header("⚡ Quick Actions")
    
    if st.session_state.uploaded_data is not None:
        # Quick filter for overdue items
        if 'Turnaround Time (hrs)' in st.session_state.uploaded_data.columns:
            if st.button("🚨 Show Overdue (>24h)", use_container_width=True):
                overdue = st.session_state.uploaded_data[
                    st.session_state.uploaded_data['Turnaround Time (hrs)'] > 24
                ]
                st.metric("Overdue Items", len(overdue))
        
        # Quick stats
        if st.button("📈 Show Today's Stats", use_container_width=True):
            today_data = st.session_state.uploaded_data[
                pd.to_datetime(st.session_state.uploaded_data['Timestamp']).dt.date == datetime.now().date()
            ] if 'Timestamp' in st.session_state.uploaded_data.columns else pd.DataFrame()
            
            if len(today_data) > 0:
                st.metric("Today's NDAs", len(today_data))
            else:
                st.info("No data for today")
    
    st.divider()
    
    st.header("ℹ️ System Info")
    st.write("""
    **Version:** 2.0.1  
    **Mode:** File Upload  
    **Status:** Active  
    """)
    
    # Show last update time
    if 'last_upload_time' in st.session_state:
        st.caption(f"Last upload: {st.session_state.last_upload_time.strftime('%H:%M:%S')}")

# Footer
st.divider()
st.caption("JMM Associates NDA Dashboard v2.0.1 | Upload-based solution - No API required | ©JMM310,LLC 2024")
