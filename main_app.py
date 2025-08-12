# main_app.py - Simple working version that will display correctly
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="NDA Dashboard",
    page_icon="📄",
    layout="wide"
)

# Initialize data in session state
if 'threads' not in st.session_state:
    st.session_state.threads = [
        {
            'Thread ID': 'T001',
            'Subject': 'NDA Agreement - Acme Corp',
            'Client': 'Acme Corp',
            'Status': '🟡 Pending',
            'Priority': 'High',
            'Received': datetime.now() - timedelta(hours=2),
            'Deadline': datetime.now() + timedelta(hours=22)
        },
        {
            'Thread ID': 'T002',
            'Subject': 'Confidentiality Agreement - TechCo',
            'Client': 'TechCo',
            'Status': '🔵 In Review',
            'Priority': 'Medium',
            'Received': datetime.now() - timedelta(hours=5),
            'Deadline': datetime.now() + timedelta(hours=19)
        },
        {
            'Thread ID': 'T003',
            'Subject': 'NDA - StartupXYZ',
            'Client': 'StartupXYZ',
            'Status': '🟢 Completed',
            'Priority': 'Low',
            'Received': datetime.now() - timedelta(days=1),
            'Deadline': datetime.now() + timedelta(hours=10)
        }
    ]

# Title
st.title("📄 NDA Dashboard & Document QA System")
st.markdown("**Real-time monitoring of NDA emails and document quality**")

# Calculate KPIs
total_threads = len(st.session_state.threads)
pending = len([t for t in st.session_state.threads if 'Pending' in t['Status']])
in_review = len([t for t in st.session_state.threads if 'In Review' in t['Status']])
completed = len([t for t in st.session_state.threads if 'Completed' in t['Status']])
overdue = len([t for t in st.session_state.threads if t['Deadline'] < datetime.now() and 'Completed' not in t['Status']])

# KPI Cards
st.markdown("### 📊 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="📥 Total Threads",
        value=total_threads,
        delta="Active"
    )

with col2:
    st.metric(
        label="⏳ Pending",
        value=pending,
        delta="To process"
    )

with col3:
    st.metric(
        label="👀 In Review",
        value=in_review,
        delta="Processing"
    )

with col4:
    st.metric(
        label="✅ Completed",
        value=completed,
        delta="Done"
    )

with col5:
    st.metric(
        label="⚠️ Overdue",
        value=overdue,
        delta="Urgent" if overdue > 0 else "On track"
    )

# Divider
st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📧 Email Threads", "📊 Document Quality", "📝 Feedback & Settings"])

# Tab 1: Email Threads
with tab1:
    st.header("Email Threads Monitor")
    
    # Add new thread section
    with st.expander("➕ Add New Thread"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject")
            client = st.selectbox("Client", ["Acme Corp", "TechCo", "StartupXYZ", "Other"])
        with col2:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            status = st.selectbox("Status", ["🟡 Pending", "🔵 In Review", "🟢 Completed"])
        
        if st.button("Add Thread", type="primary"):
            new_thread = {
                'Thread ID': f'T{len(st.session_state.threads)+1:03d}',
                'Subject': subject or f'New NDA - {client}',
                'Client': client,
                'Status': status,
                'Priority': priority,
                'Received': datetime.now(),
                'Deadline': datetime.now() + timedelta(hours=24)
            }
            st.session_state.threads.append(new_thread)
            st.success("✅ Thread added successfully!")
            st.rerun()
    
    # Display threads
    if st.session_state.threads:
        df = pd.DataFrame(st.session_state.threads)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Quick stats
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Status Distribution")
            status_data = pd.DataFrame({
                'Status': ['Pending', 'In Review', 'Completed'],
                'Count': [pending, in_review, completed]
            })
            st.bar_chart(status_data.set_index('Status'))
        
        with col2:
            st.subheader("Priority Breakdown")
            priority_counts = df['Priority'].value_counts()
            st.bar_chart(priority_counts)
    else:
        st.info("No threads to display. Add a new thread to get started!")

# Tab 2: Document Quality
with tab2:
    st.header("Document Quality Analysis")
    
    # Sample quality data
    quality_data = pd.DataFrame({
        'Document': ['nda_acme_v1.docx', 'agreement_techco.docx', 'confidential_startup.docx'],
        'Quality Score': [85, 92, 78],
        'Spelling Issues': [2, 0, 4],
        'Tracked Changes': [1, 0, 3],
        'Status': ['✅ Reviewed', '✅ Reviewed', '⚠️ Needs Review']
    })
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_quality = quality_data['Quality Score'].mean()
        st.metric("Average Quality Score", f"{avg_quality:.1f}/100")
    with col2:
        total_issues = quality_data['Spelling Issues'].sum() + quality_data['Tracked Changes'].sum()
        st.metric("Total Issues Found", total_issues)
    with col3:
        reviewed = len(quality_data[quality_data['Status'].str.contains('Reviewed')])
        st.metric("Documents Reviewed", f"{reviewed}/{len(quality_data)}")
    
    # Document details
    st.subheader("Document Details")
    st.dataframe(quality_data, use_container_width=True, hide_index=True)
    
    # Upload new document
    st.subheader("Upload Document for Analysis")
    uploaded_file = st.file_uploader("Choose a file", type=['docx', 'pdf', 'txt'])
    if uploaded_file is not None:
        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
        if st.button("Analyze Document"):
            with st.spinner("Analyzing document..."):
                # Simulate analysis
                import time
                time.sleep(2)
            st.success("Analysis complete! Quality Score: 88/100")

# Tab 3: Feedback & Settings
with tab3:
    st.header("Feedback & System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Submit Feedback")
        feedback_type = st.selectbox("Feedback Type", ["Bug Report", "Feature Request", "Quality Issue"])
        feedback_text = st.text_area("Your Feedback")
        if st.button("Submit Feedback", type="primary"):
            st.success("Thank you for your feedback!")
    
    with col2:
        st.subheader("System Settings")
        st.slider("SLA Hours", 1, 72, 24)
        st.checkbox("Enable Email Notifications", value=True)
        st.checkbox("Auto-classify Emails", value=True)
        st.selectbox("Quality Check Model", ["Basic", "Advanced", "AI-Powered"])
        
        if st.button("Save Settings"):
            st.success("Settings saved!")

# Sidebar
with st.sidebar:
    st.header("🔧 Quick Actions")
    
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()
    
    if st.button("📊 Export Report", use_container_width=True):
        st.success("Report exported!")
    
    if st.button("🔍 Run Quality Check", use_container_width=True):
        with st.spinner("Running..."):
            import time
            time.sleep(1)
        st.success("Check complete!")
    
    st.divider()
    
    st.header("📈 System Status")
    st.success("✅ System Online")
    st.info(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
    
    st.divider()
    
    st.header("ℹ️ Info")
    st.write("""
    **Version:** 1.0.0  
    **Mode:** Demo  
    **Database:** Session State  
    """)

# Footer
st.divider()
st.caption("NDA Dashboard v1.0 | Built with Streamlit | © 2024")
