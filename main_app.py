# main_app.py - NDA Dashboard with Spelling Quality Analysis from Column Q
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import json
import re
import os

# Page config
st.set_page_config(
    page_title="JMM Associates - NDA Dashboard",
    page_icon="📄",
    layout="wide"
)

# ==================== Quality Analysis Functions ====================
def parse_spelling_errors(spelling_text):
    """
    Parse the spelling error text from Column Q to extract detailed quality metrics
    """
    if pd.isna(spelling_text) or spelling_text == '' or spelling_text is None:
        return {
            'total_issues': 0,
            'typos': 0,
            'punctuation': 0,
            'grammar': 0,
            'typography': 0,
            'redundancy': 0,
            'casing': 0,
            'misc': 0,
            'quality_score': 100,
            'issue_details': []
        }
    
    # Convert to string and count different types of issues
    error_text = str(spelling_text)
    
    # Count different error types using regex
    typos = len(re.findall(r'TYPOS:', error_text))
    punctuation = len(re.findall(r'PUNCTUATION:', error_text))
    grammar = len(re.findall(r'GRAMMAR:', error_text))
    typography = len(re.findall(r'TYPOGRAPHY:', error_text))
    redundancy = len(re.findall(r'REDUNDANCY:', error_text))
    casing = len(re.findall(r'CASING:', error_text))
    misc = len(re.findall(r'MISC:', error_text))
    repetitions = len(re.findall(r'REPETITIONS_STYLE:', error_text))
    
    total_issues = typos + punctuation + grammar + typography + redundancy + casing + misc + repetitions
    
    # Extract individual issues
    issue_details = []
    
    # Parse each issue type
    patterns = {
        'TYPOS': r'([^;]+)\s*\(TYPOS:[^)]+\)',
        'PUNCTUATION': r'([^;]+)\s*\(PUNCTUATION:[^)]+\)',
        'GRAMMAR': r'([^;]+)\s*\(GRAMMAR:[^)]+\)',
        'TYPOGRAPHY': r'([^;]+)\s*\(TYPOGRAPHY:[^)]+\)',
        'REDUNDANCY': r'([^;]+)\s*\(REDUNDANCY:[^)]+\)',
        'CASING': r'([^;]+)\s*\(CASING:[^)]+\)',
        'MISC': r'([^;]+)\s*\(MISC:[^)]+\)',
        'REPETITIONS_STYLE': r'([^;]+)\s*\(REPETITIONS_STYLE:[^)]+\)'
    }
    
    for error_type, pattern in patterns.items():
        matches = re.findall(pattern, error_text)
        for match in matches:
            issue_details.append({
                'type': error_type,
                'text': match.strip()
            })
    
    # Calculate quality score based on issue count and severity
    # Start with 100 and deduct points based on issues
    quality_score = 100
    
    # Deduct points based on error severity
    quality_score -= typos * 5          # Typos are serious
    quality_score -= grammar * 4        # Grammar errors are important
    quality_score -= punctuation * 2    # Punctuation is less critical
    quality_score -= typography * 1     # Typography is minor
    quality_score -= redundancy * 2     # Redundancy affects readability
    quality_score -= casing * 2         # Casing issues are minor
    quality_score -= misc * 3           # Misc issues vary
    quality_score -= repetitions * 2    # Style issues
    
    # Ensure score stays between 0 and 100
    quality_score = max(0, min(100, quality_score))
    
    return {
        'total_issues': total_issues,
        'typos': typos,
        'punctuation': punctuation,
        'grammar': grammar,
        'typography': typography,
        'redundancy': redundancy,
        'casing': casing,
        'misc': misc + repetitions,
        'quality_score': quality_score,
        'issue_details': issue_details
    }

def categorize_quality_score(score):
    """Categorize quality score into bands"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Poor"
    else:
        return "Very Poor"

# ==================== Data Persistence Functions ====================
def save_data_to_cloud():
    """Save data to a persistent location"""
    if st.session_state.uploaded_data is not None:
        data_package = {
            'upload_time': datetime.now().isoformat(),
            'data': st.session_state.uploaded_data.to_json(orient='records', date_format='iso'),
            'dashboard_data': st.session_state.dashboard_data.to_json(orient='records', date_format='iso') if 'dashboard_data' in st.session_state and st.session_state.dashboard_data is not None else None,
            'run_log': st.session_state.run_log.to_json(orient='records', date_format='iso') if 'run_log' in st.session_state and st.session_state.run_log is not None else None,
            'last_updated_by': st.session_state.get('user_name', 'Admin')
        }
        
        st.session_state.shared_data = data_package
        
        with open('shared_dashboard_data.json', 'w') as f:
            json.dump(data_package, f)
        
        return True
    return False

def load_shared_data():
    """Load shared data if available"""
    if 'shared_data' in st.session_state:
        return st.session_state.shared_data
    
    if os.path.exists('shared_dashboard_data.json'):
        try:
            with open('shared_dashboard_data.json', 'r') as f:
                data_package = json.load(f)
                st.session_state.shared_data = data_package
                return data_package
        except:
            pass
    
    return None

def load_data_from_package(data_package):
    """Load data from a saved package"""
    if data_package:
        st.session_state.uploaded_data = pd.read_json(data_package['data'], orient='records')
        
        if data_package.get('dashboard_data'):
            st.session_state.dashboard_data = pd.read_json(data_package['dashboard_data'], orient='records')
        
        if data_package.get('run_log'):
            st.session_state.run_log = pd.read_json(data_package['run_log'], orient='records')
        
        st.session_state.last_upload_time = datetime.fromisoformat(data_package['upload_time'])
        st.session_state.last_updated_by = data_package.get('last_updated_by', 'Unknown')
        
        return True
    return False

# ==================== Access Control ====================
def check_access_mode():
    """Determine if user is in admin mode or viewer mode"""
    # For Streamlit, let's make it simpler - always show admin panel
    # You can add authentication later if needed
    return 'admin'  # Always admin mode for now so you can upload

# ==================== Initialize Session State ====================
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# ==================== Main App ====================
# Add mode selector at the top
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    access_mode = st.radio(
        "Select Access Mode",
        ["Admin (Can Upload)", "Viewer (Read Only)"],
        horizontal=True,
        index=0  # Default to Admin
    )
    access_mode = 'admin' if 'Admin' in access_mode else 'viewer'

# Title with mode indicator
if access_mode == 'admin':
    st.title("📄 JMM NDA Dashboard & Document QA System [Admin Mode]")
    st.markdown("**Document Quality Analysis**")
else:
    st.title("📄 JMM NDA Dashboard & Document QA System [View Only]")
    st.markdown("**Viewing shared dashboard with quality metrics**")

# Admin Panel
if access_mode == 'admin':
    with st.expander("🔧 Admin Panel", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📤 Upload New Data")
            uploaded_file = st.file_uploader(
                "Choose your NDA Tracker Excel file",
                type=['xlsx', 'xls'],
                help="Upload the Excel file with spelling data in Column Q"
            )
            
            if uploaded_file is not None:
                try:
                    excel_file = pd.ExcelFile(uploaded_file)
                    available_sheets = excel_file.sheet_names
                    
                    # Read Test Sheet with all columns including Q
                    if 'Test Sheet' in available_sheets:
                        # Read without headers first to get all columns
                        df_raw = pd.read_excel(uploaded_file, sheet_name='Test Sheet', header=None)
                        
                        # Use first row as headers
                        headers = df_raw.iloc[0].tolist()
                        df = df_raw[1:].copy()
                        
                        # Assign column names
                        column_names = []
                        for i, header in enumerate(headers):
                            if pd.notna(header):
                                column_names.append(str(header))
                            else:
                                # For column Q (index 16) which might not have a header
                                if i == 16:
                                    column_names.append('Spelling_Errors')
                                else:
                                    column_names.append(f'Column_{i}')
                        
                        df.columns = column_names
                        df.reset_index(drop=True, inplace=True)
                        
                    else:
                        df = pd.read_excel(uploaded_file, sheet_name=0)
                    
                    # Store in session state
                    st.session_state.uploaded_data = df
                    st.session_state.last_upload_time = datetime.now()
                    
                    # Read other sheets
                    if 'Dashboard' in available_sheets:
                        st.session_state.dashboard_data = pd.read_excel(uploaded_file, sheet_name='Dashboard')
                    
                    if 'Run Log' in available_sheets:
                        st.session_state.run_log = pd.read_excel(uploaded_file, sheet_name='Run Log')
                    
                    st.success(f"✅ Successfully loaded {len(df)} NDA records with spelling quality data")
                    
                    # Check if we have the spelling column
                    if 'Spelling_Errors' in df.columns:
                        non_empty = df['Spelling_Errors'].notna().sum()
                        st.info(f"📝 Found spelling data in {non_empty} documents")
                    
                    # Save for sharing
                    if save_data_to_cloud():
                        st.success("📤 Data saved and ready for sharing!")
                    
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        with col2:
            st.markdown("### 🔗 Share Dashboard")
            if st.session_state.uploaded_data is not None:
                base_url = "https://your-app.streamlit.app"
                viewer_url = f"{base_url}?mode=viewer"
                admin_url = f"{base_url}?admin=upload"
                
                st.text_input("Viewer Link (read-only):", value=viewer_url, disabled=True)
                st.text_input("Admin Link (can upload):", value=admin_url, disabled=True)
                
                st.caption("Share the viewer link with your team for read-only access")
            else:
                st.info("Upload data first to generate shareable links")
        
        with col3:
            st.markdown("### 📊 Data Status")
            if st.session_state.uploaded_data is not None:
                st.metric("Records Loaded", len(st.session_state.uploaded_data))
                st.metric("Last Updated", st.session_state.last_upload_time.strftime("%Y-%m-%d %H:%M"))
                
                if 'Spelling_Errors' in st.session_state.uploaded_data.columns:
                    has_quality = st.session_state.uploaded_data['Spelling_Errors'].notna().sum()
                    st.metric("Docs with Quality Data", has_quality)
            else:
                st.info("No data loaded")

# Load shared data if in viewer mode
if access_mode == 'viewer' or st.session_state.uploaded_data is None:
    shared_data = load_shared_data()
    if shared_data:
        if load_data_from_package(shared_data):
            st.info(f"📊 Viewing shared data (Last updated: {st.session_state.last_upload_time.strftime('%Y-%m-%d %H:%M')} by {st.session_state.last_updated_by})")
    elif access_mode == 'viewer':
        st.warning("⚠️ No shared data available. Please ask an admin to upload data.")
        st.stop()

# Main Dashboard
if st.session_state.uploaded_data is not None:
    df = st.session_state.uploaded_data
    
    # Add date columns
    if 'Timestamp' in df.columns:
        df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
        df['Week'] = pd.to_datetime(df['Timestamp']).dt.isocalendar().week
        df['Year'] = pd.to_datetime(df['Timestamp']).dt.year
        df['Day_of_Week'] = pd.to_datetime(df['Timestamp']).dt.day_name()
        df['Hour'] = pd.to_datetime(df['Timestamp']).dt.hour
    
    # Process spelling quality data from Column Q
    if 'Spelling_Errors' in df.columns:
        # Parse spelling errors for each document
        quality_metrics = df['Spelling_Errors'].apply(parse_spelling_errors)
        
        # Extract metrics into separate columns
        df['Quality_Score'] = quality_metrics.apply(lambda x: x['quality_score'])
        df['Total_Issues'] = quality_metrics.apply(lambda x: x['total_issues'])
        df['Typos_Count'] = quality_metrics.apply(lambda x: x['typos'])
        df['Grammar_Issues'] = quality_metrics.apply(lambda x: x['grammar'])
        df['Punctuation_Issues'] = quality_metrics.apply(lambda x: x['punctuation'])
        df['Typography_Issues'] = quality_metrics.apply(lambda x: x['typography'])
        df['Quality_Category'] = df['Quality_Score'].apply(categorize_quality_score)
        
        # Create issue summary
        df['Issue_Summary'] = df.apply(lambda row: f"Typos: {row['Typos_Count']}, Grammar: {row['Grammar_Issues']}, Punctuation: {row['Punctuation_Issues']}" if row['Total_Issues'] > 0 else "No issues", axis=1)
    else:
        # Fallback if no spelling data
        df['Quality_Score'] = 100
        df['Total_Issues'] = 0
        df['Quality_Category'] = 'No Data'
    
    # Calculate KPIs
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        total_ndas = len(df)
        st.metric("📥 Total NDAs", total_ndas)
    
    with col2:
        if 'Status' in df.columns:
            completed = len(df[df['Status'] == 'Completed'])
            completion_rate = (completed / total_ndas * 100) if total_ndas > 0 else 0
            st.metric("✅ Completed", completed, f"{completion_rate:.1f}%")
        else:
            st.metric("✅ Completed", "N/A")
    
    with col3:
        if 'Turnaround Time (hrs)' in df.columns:
            avg_turnaround = df['Turnaround Time (hrs)'].dropna().mean()
            st.metric("⏱️ Avg Turnaround", f"{avg_turnaround:.1f}h" if not pd.isna(avg_turnaround) else "N/A")
        else:
            st.metric("⏱️ Avg Turnaround", "N/A")
    
    with col4:
        avg_quality = df['Quality_Score'].mean()
        st.metric("📊 Avg Quality", f"{avg_quality:.0f}/100")
    
    with col5:
        if 'Total_Issues' in df.columns:
            total_issues = df['Total_Issues'].sum()
            st.metric("⚠️ Total Issues", total_issues)
        else:
            st.metric("⚠️ Total Issues", "N/A")
    
    with col6:
        if 'Typos_Count' in df.columns:
            total_typos = df['Typos_Count'].sum()
            st.metric("✍️ Total Typos", total_typos)
        else:
            st.metric("✍️ Total Typos", "N/A")
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📧 NDA Threads", 
        "🔍 Quality Analysis", 
        "📊 Daily Analytics",
        "📅 Weekly Analytics",
        "📈 Trends",
        "📋 Issue Details"
    ])
    
    # Tab 1: NDA Threads
    with tab1:
        st.header("NDA Email Threads with Quality Metrics")
        
        # Filters - First Row
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
                    options=sorted(df['Customer'].dropna().unique().tolist()),
                    default=[]
                )
            else:
                customer_filter = []
        
        with col3:
            if 'Quality_Category' in df.columns:
                quality_filter = st.multiselect(
                    "Filter by Quality",
                    options=df['Quality_Category'].unique().tolist(),
                    default=[]
                )
            else:
                quality_filter = []
        
        # Filters - Second Row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search in Subject", "")
        
        with col2:
            min_issues = st.number_input("Min Issues to Show", min_value=0, value=0)
        
        with col3:
            # Quality score range filter
            if 'Quality_Score' in df.columns:
                score_range = st.slider(
                    "Quality Score Range",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    step=5
                )
            else:
                score_range = (0, 100)
        
        # Apply filters
        filtered_df = df.copy()
        
        if status_filter and 'Status' in df.columns:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        
        if customer_filter and 'Customer' in df.columns:
            filtered_df = filtered_df[filtered_df['Customer'].isin(customer_filter)]
        
        if quality_filter and 'Quality_Category' in df.columns:
            filtered_df = filtered_df[filtered_df['Quality_Category'].isin(quality_filter)]
        
        if search_term and 'Subject' in df.columns:
            filtered_df = filtered_df[filtered_df['Subject'].str.contains(search_term, case=False, na=False)]
        
        if 'Total_Issues' in df.columns:
            filtered_df = filtered_df[filtered_df['Total_Issues'] >= min_issues]
        
        if 'Quality_Score' in df.columns:
            filtered_df = filtered_df[(filtered_df['Quality_Score'] >= score_range[0]) & 
                                     (filtered_df['Quality_Score'] <= score_range[1])]
        
        # Display
        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} records**")
        
        display_columns = ['Timestamp', 'Subject', 'Customer', 'Status', 'Quality_Score', 
                          'Total_Issues', 'Quality_Category', 'Issue_Summary']
        display_columns = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            height=400
        )
    
    # Tab 2: Quality Analysis
    with tab2:
        st.header("🔍 Document Quality Analysis")
        st.info("📝 Quality scores based on spelling and grammar check data from Column Q")
        
        # Quality overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_quality = df['Quality_Score'].mean()
            st.metric("Average Quality Score", f"{avg_quality:.0f}/100")
        
        with col2:
            excellent_docs = len(df[df['Quality_Score'] >= 90])
            st.metric("Excellent Quality (≥90)", excellent_docs)
        
        with col3:
            poor_docs = len(df[df['Quality_Score'] < 60])
            st.metric("Poor Quality (<60)", poor_docs)
        
        with col4:
            if 'Total_Issues' in df.columns:
                avg_issues = df['Total_Issues'].mean()
                st.metric("Avg Issues per Doc", f"{avg_issues:.1f}")
        
        # Issue type breakdown
        if all(col in df.columns for col in ['Typos_Count', 'Grammar_Issues', 'Punctuation_Issues', 'Typography_Issues']):
            st.subheader("Issue Type Distribution")
            
            issue_totals = {
                'Typos': df['Typos_Count'].sum(),
                'Grammar': df['Grammar_Issues'].sum(),
                'Punctuation': df['Punctuation_Issues'].sum(),
                'Typography': df['Typography_Issues'].sum()
            }
            
            issue_df = pd.DataFrame(list(issue_totals.items()), columns=['Issue Type', 'Count'])
            st.bar_chart(issue_df.set_index('Issue Type'))
        
        # Quality distribution
        st.subheader("Quality Score Distribution")
        quality_dist = df['Quality_Category'].value_counts()
        st.bar_chart(quality_dist)
        
        # Documents with most issues
        st.subheader("Documents with Most Issues")
        if 'Total_Issues' in df.columns:
            worst_docs = df.nlargest(10, 'Total_Issues')[['Subject', 'Customer', 'Quality_Score', 'Total_Issues', 'Issue_Summary']]
            st.dataframe(worst_docs, use_container_width=True)
        
        # Quality by customer
        if 'Customer' in df.columns:
            st.subheader("Quality by Customer")
            customer_quality = df.groupby('Customer').agg({
                'Quality_Score': 'mean',
                'Total_Issues': 'sum',
                'Subject': 'count'
            }).round(1)
            customer_quality.columns = ['Avg Quality Score', 'Total Issues', 'Document Count']
            customer_quality = customer_quality.sort_values('Avg Quality Score', ascending=False)
            st.dataframe(customer_quality, use_container_width=True)
    
    # Tab 3: Daily Analytics
    with tab3:
        st.header("Daily Analytics Dashboard")
        
        if 'Date' in df.columns:
            available_dates = sorted(df['Date'].unique(), reverse=True)
            selected_date = st.selectbox("Select Date", available_dates, index=0)
            
            daily_df = df[df['Date'] == selected_date]
            
            # Daily metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total NDAs", len(daily_df))
            
            with col2:
                daily_avg_quality = daily_df['Quality_Score'].mean()
                st.metric("Avg Quality", f"{daily_avg_quality:.0f}/100")
            
            with col3:
                if 'Total_Issues' in daily_df.columns:
                    daily_total_issues = daily_df['Total_Issues'].sum()
                    st.metric("Total Issues", daily_total_issues)
            
            with col4:
                if 'Typos_Count' in daily_df.columns:
                    daily_typos = daily_df['Typos_Count'].sum()
                    st.metric("Typos Found", daily_typos)
            
            # Quality distribution for the day
            st.subheader("Quality Distribution")
            if 'Quality_Category' in daily_df.columns:
                daily_quality_dist = daily_df['Quality_Category'].value_counts()
                st.bar_chart(daily_quality_dist)
    
    # Tab 4: Weekly Analytics
    with tab4:
        st.header("Weekly Analytics Dashboard")
        
        if 'Week' in df.columns and 'Year' in df.columns:
            df['Year_Week'] = df['Year'].astype(str) + '-W' + df['Week'].astype(str).str.zfill(2)
            available_weeks = sorted(df['Year_Week'].unique(), reverse=True)
            selected_week = st.selectbox("Select Week", available_weeks, index=0 if available_weeks else None)
            
            if selected_week:
                weekly_df = df[df['Year_Week'] == selected_week]
                
                # Weekly metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total NDAs", len(weekly_df))
                
                with col2:
                    weekly_avg_quality = weekly_df['Quality_Score'].mean()
                    st.metric("Avg Quality", f"{weekly_avg_quality:.0f}/100")
                
                with col3:
                    if 'Total_Issues' in weekly_df.columns:
                        weekly_issues = weekly_df['Total_Issues'].sum()
                        st.metric("Total Issues", weekly_issues)
                
                with col4:
                    excellent_week = len(weekly_df[weekly_df['Quality_Score'] >= 90])
                    st.metric("Excellent Docs", excellent_week)
                
                with col5:
                    poor_week = len(weekly_df[weekly_df['Quality_Score'] < 60])
                    st.metric("Poor Docs", poor_week)
                
                # Daily quality trend within week
                if 'Date' in weekly_df.columns:
                    st.subheader("Daily Quality Trend")
                    daily_quality = weekly_df.groupby('Date')['Quality_Score'].mean()
                    st.line_chart(daily_quality)
    
    # Tab 5: Trends
    with tab5:
        st.header("Quality Trends Over Time")
        
        if 'Date' in df.columns:
            # Quality score trend
            st.subheader("Quality Score Trend")
            quality_trend = df.groupby('Date')['Quality_Score'].mean()
            st.line_chart(quality_trend)
            
            # Issue count trend
            if 'Total_Issues' in df.columns:
                st.subheader("Total Issues Trend")
                issues_trend = df.groupby('Date')['Total_Issues'].sum()
                st.line_chart(issues_trend)
            
            # Issue type trends
            if all(col in df.columns for col in ['Typos_Count', 'Grammar_Issues', 'Punctuation_Issues']):
                st.subheader("Issue Types Over Time")
                issue_trends = df.groupby('Date').agg({
                    'Typos_Count': 'sum',
                    'Grammar_Issues': 'sum',
                    'Punctuation_Issues': 'sum'
                })
                st.line_chart(issue_trends)
    
    # Tab 6: Issue Details
    with tab6:
        st.header("📋 Detailed Issue Analysis")
        
        # Filter by issue type
        if 'Total_Issues' in df.columns:
            issue_threshold = st.slider("Minimum issues to display", 0, int(df['Total_Issues'].max()), 1)
            
            detailed_df = df[df['Total_Issues'] >= issue_threshold].copy()
            
            st.markdown(f"Showing {len(detailed_df)} documents with {issue_threshold}+ issues")
            
            # Show detailed breakdown
            for idx, row in detailed_df.head(20).iterrows():
                with st.expander(f"📄 {row['Subject'][:50]}... (Score: {row['Quality_Score']:.0f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Customer:** {row.get('Customer', 'N/A')}")
                        st.write(f"**Status:** {row.get('Status', 'N/A')}")
                        st.write(f"**Quality Score:** {row['Quality_Score']:.0f}/100")
                    
                    with col2:
                        st.write(f"**Total Issues:** {row['Total_Issues']}")
                        if 'Typos_Count' in row:
                            st.write(f"**Typos:** {row['Typos_Count']}")
                            st.write(f"**Grammar:** {row.get('Grammar_Issues', 0)}")
                            st.write(f"**Punctuation:** {row.get('Punctuation_Issues', 0)}")
                    
                    if 'Spelling_Errors' in row and pd.notna(row['Spelling_Errors']):
                        st.write("**Raw Issues Found:**")
                        st.text(row['Spelling_Errors'][:500] + "..." if len(str(row['Spelling_Errors'])) > 500 else row['Spelling_Errors'])

else:
    # Instructions
    if access_mode == 'admin':
        st.info("""
        ### 📤 Welcome Admin! Please upload your NDA Tracker
        
        Upload your Excel file with spelling check data in Column Q to see:
        - Automatic quality scoring based on spelling/grammar issues
        - Detailed breakdown of error types (typos, grammar, punctuation)
        - Quality trends and analytics
        - Customer quality rankings
        """)
    else:
        st.warning("⚠️ No data available. Please contact your administrator.")

# Sidebar
with st.sidebar:
    st.header("🔧 Dashboard Info")
    
    if access_mode == 'admin':
        st.success("👑 Admin Mode")
    else:
        st.info("👁️ Viewer Mode")
    
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        st.divider()
        st.header("📊 Quality Summary")
        
        if 'Quality_Score' in df.columns:
            st.metric("Avg Quality", f"{df['Quality_Score'].mean():.0f}/100")
            
            # Quality breakdown
            excellent = len(df[df['Quality_Score'] >= 90])
            good = len(df[(df['Quality_Score'] >= 75) & (df['Quality_Score'] < 90)])
            fair = len(df[(df['Quality_Score'] >= 60) & (df['Quality_Score'] < 75)])
            poor = len(df[df['Quality_Score'] < 60])
            
            st.write("**Quality Distribution:**")
            st.write(f"🌟 Excellent: {excellent}")
            st.write(f"✅ Good: {good}")
            st.write(f"⚠️ Fair: {fair}")
            st.write(f"❌ Poor: {poor}")
        
        if 'Total_Issues' in df.columns:
            st.divider()
            st.write("**Issue Statistics:**")
            st.write(f"📝 Total Issues: {df['Total_Issues'].sum()}")
            st.write(f"📊 Avg per Doc: {df['Total_Issues'].mean():.1f}")

# Footer
st.divider()
st.caption("JMM Associates NDA Dashboard v5.0 | Quality Analysis from Column Q Spelling Data | ©JMM310,LLC 2024")
