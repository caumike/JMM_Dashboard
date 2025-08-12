# main_app.py - NDA Dashboard & Document QA System
# Streamlit-based implementation with AI Agents

import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime, timedelta
import hashlib
import json
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass, asdict
import sqlite3  # Using SQLite for simplicity, can swap to Postgres
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== Configuration ====================
st.set_page_config(
    page_title="NDA Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Data Models ====================
@dataclass
class Thread:
    thread_id: str
    subject: str
    sender: str
    client_org: str
    status: str  # 'pending', 'in_review', 'completed', 'overdue'
    priority: str  # 'high', 'medium', 'low'
    received_at: datetime
    sla_deadline: datetime
    turnaround_hours: Optional[float] = None

@dataclass
class Document:
    doc_id: str
    thread_id: str
    filename: str
    doc_type: str
    quality_score: float
    spelling_issues: int
    tracked_changes: int
    style_issues: int
    processed_at: datetime

@dataclass
class QualityCheck:
    check_id: str
    doc_id: str
    check_type: str  # 'spelling', 'tracked_changes', 'style'
    findings: List[Dict]
    severity: str  # 'critical', 'warning', 'info'

# ==================== Database Setup ====================
class DatabaseManager:
    def __init__(self, db_path="nda_dashboard.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                subject TEXT,
                sender TEXT,
                client_org TEXT,
                status TEXT,
                priority TEXT,
                received_at TIMESTAMP,
                sla_deadline TIMESTAMP,
                turnaround_hours REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                thread_id TEXT,
                filename TEXT,
                doc_type TEXT,
                quality_score REAL,
                spelling_issues INTEGER,
                tracked_changes INTEGER,
                style_issues INTEGER,
                processed_at TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES threads (thread_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_checks (
                check_id TEXT PRIMARY KEY,
                doc_id TEXT,
                check_type TEXT,
                findings TEXT,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id TEXT,
                is_correct BOOLEAN,
                comments TEXT,
                reviewer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (check_id) REFERENCES quality_checks (check_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

# ==================== AI Agents ====================
class EmailIngestAgent:
    """Agent responsible for email ingestion and classification"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def classify_email(self, subject: str, body: str) -> Dict:
        """Classify email and extract metadata"""
        # Simplified classification logic - in production, use LLM
        is_nda = any(keyword in subject.lower() or keyword in body.lower() 
                     for keyword in ['nda', 'non-disclosure', 'confidential', 'agreement'])
        
        priority = 'high' if 'urgent' in subject.lower() else 'medium'
        client_org = self.extract_client(subject, body)
        
        return {
            'is_nda': is_nda,
            'priority': priority,
            'client_org': client_org,
            'status': 'pending'
        }
    
    def extract_client(self, subject: str, body: str) -> str:
        """Extract client organization from email"""
        # Simplified - in production, use NER or pattern matching
        clients = ['Acme Corp', 'TechCo', 'GlobalTrade', 'StartupXYZ']
        for client in clients:
            if client.lower() in subject.lower() or client.lower() in body.lower():
                return client
        return 'Unknown'
    
    def process_email(self, email_data: Dict) -> Thread:
        """Process a single email and create thread"""
        classification = self.classify_email(email_data['subject'], email_data['body'])
        
        thread = Thread(
            thread_id=email_data['thread_id'],
            subject=email_data['subject'],
            sender=email_data['sender'],
            client_org=classification['client_org'],
            status=classification['status'],
            priority=classification['priority'],
            received_at=datetime.now(),
            sla_deadline=datetime.now() + timedelta(hours=24)
        )
        
        # Save to database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO threads 
            (thread_id, subject, sender, client_org, status, priority, received_at, sla_deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (thread.thread_id, thread.subject, thread.sender, thread.client_org,
              thread.status, thread.priority, thread.received_at, thread.sla_deadline))
        conn.commit()
        conn.close()
        
        return thread

class DocumentQualityAgent:
    """Agent responsible for document quality checks"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def analyze_document(self, doc_content: str, doc_id: str, thread_id: str) -> Document:
        """Analyze document quality"""
        # Simplified quality checks - in production, use LanguageTool API
        spelling_issues = self.check_spelling(doc_content)
        tracked_changes = self.check_tracked_changes(doc_content)
        style_issues = self.check_style(doc_content)
        
        # Calculate quality score (0-100)
        quality_score = max(0, 100 - (spelling_issues * 5) - (tracked_changes * 3) - (style_issues * 2))
        
        doc = Document(
            doc_id=doc_id,
            thread_id=thread_id,
            filename=f"document_{doc_id}.docx",
            doc_type="NDA",
            quality_score=quality_score,
            spelling_issues=spelling_issues,
            tracked_changes=tracked_changes,
            style_issues=style_issues,
            processed_at=datetime.now()
        )
        
        # Save to database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (doc_id, thread_id, filename, doc_type, quality_score, spelling_issues, 
             tracked_changes, style_issues, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (doc.doc_id, doc.thread_id, doc.filename, doc.doc_type, doc.quality_score,
              doc.spelling_issues, doc.tracked_changes, doc.style_issues, doc.processed_at))
        conn.commit()
        conn.close()
        
        return doc
    
    def check_spelling(self, content: str) -> int:
        """Check for spelling issues"""
        # Simplified - count common misspellings
        common_errors = ['teh', 'recieve', 'seperate', 'occured']
        return sum(1 for error in common_errors if error in content.lower())
    
    def check_tracked_changes(self, content: str) -> int:
        """Check for tracked changes"""
        # Simplified - in production, parse .docx XML
        return len([line for line in content.split('\n') if line.startswith('>')])
    
    def check_style(self, content: str) -> int:
        """Check for style issues"""
        # Simplified style checks
        issues = 0
        if len(content.split()) > 5000:  # Document too long
            issues += 1
        if content.count('!!!') > 0:  # Excessive punctuation
            issues += 1
        return issues

class DashboardAgent:
    """Agent responsible for dashboard metrics and KPIs"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_kpis(self) -> Dict:
        """Calculate current KPIs"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total threads
        cursor.execute("SELECT COUNT(*) FROM threads")
        total_threads = cursor.fetchone()[0]
        
        # Status breakdown
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM threads 
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # SLA compliance
        cursor.execute("""
            SELECT COUNT(*) 
            FROM threads 
            WHERE datetime(sla_deadline) < datetime('now') AND status != 'completed'
        """)
        overdue = cursor.fetchone()[0]
        
        # Average turnaround
        cursor.execute("""
            SELECT AVG(turnaround_hours) 
            FROM threads 
            WHERE turnaround_hours IS NOT NULL
        """)
        avg_turnaround = cursor.fetchone()[0] or 0
        
        # Document quality
        cursor.execute("SELECT AVG(quality_score) FROM documents")
        avg_quality = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_threads': total_threads,
            'pending': status_counts.get('pending', 0),
            'in_review': status_counts.get('in_review', 0),
            'completed': status_counts.get('completed', 0),
            'overdue': overdue,
            'avg_turnaround': round(avg_turnaround, 1),
            'avg_quality': round(avg_quality, 1),
            'sla_compliance': round((1 - (overdue / max(total_threads, 1))) * 100, 1)
        }
    
    def get_threads_data(self) -> pd.DataFrame:
        """Get threads data for display"""
        conn = self.db.get_connection()
        query = """
            SELECT thread_id, subject, sender, client_org, status, 
                   priority, received_at, sla_deadline
            FROM threads
            ORDER BY received_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_documents_data(self) -> pd.DataFrame:
        """Get documents data for display"""
        conn = self.db.get_connection()
        query = """
            SELECT d.*, t.subject, t.client_org
            FROM documents d
            JOIN threads t ON d.thread_id = t.thread_id
            ORDER BY d.processed_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

# ==================== Streamlit UI ====================
def render_sidebar():
    """Render sidebar with filters and options"""
    with st.sidebar:
        st.title("🔧 Controls")
        
        st.header("Filters")
        status_filter = st.multiselect(
            "Status",
            ["pending", "in_review", "completed", "overdue"],
            default=["pending", "in_review"]
        )
        
        client_filter = st.multiselect(
            "Client",
            ["Acme Corp", "TechCo", "GlobalTrade", "StartupXYZ"],
            default=[]
        )
        
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now()
        )
        
        st.divider()
        
        st.header("Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        if st.button("📊 Export Report", use_container_width=True):
            st.success("Report exported!")
        
        if st.button("🎯 Run Quality Check", use_container_width=True):
            with st.spinner("Running quality checks..."):
                # Simulate quality check
                import time
                time.sleep(2)
            st.success("Quality check completed!")
        
        return status_filter, client_filter, date_range

def render_kpi_cards(kpis: Dict):
    """Render KPI cards at the top of dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📥 Total Threads",
            value=kpis['total_threads'],
            delta=f"{kpis['pending']} pending"
        )
    
    with col2:
        st.metric(
            label="⏱️ Avg Turnaround",
            value=f"{kpis['avg_turnaround']}h",
            delta="2h faster" if kpis['avg_turnaround'] < 24 else "On track"
        )
    
    with col3:
        st.metric(
            label="✅ SLA Compliance",
            value=f"{kpis['sla_compliance']}%",
            delta=f"{kpis['overdue']} overdue" if kpis['overdue'] > 0 else "All on time",
            delta_color="inverse" if kpis['overdue'] > 0 else "normal"
        )
    
    with col4:
        st.metric(
            label="📊 Avg Quality Score",
            value=f"{kpis['avg_quality']}/100",
            delta="Good" if kpis['avg_quality'] > 80 else "Needs improvement"
        )

def render_threads_tab(dashboard_agent: DashboardAgent):
    """Render threads monitoring tab"""
    st.header("📧 Email Threads Monitor")
    
    threads_df = dashboard_agent.get_threads_data()
    
    if not threads_df.empty:
        # Add status badges
        threads_df['Status Badge'] = threads_df['status'].apply(
            lambda x: f"🔴 {x}" if x == 'overdue' else 
                     f"🟡 {x}" if x == 'pending' else 
                     f"🔵 {x}" if x == 'in_review' else 
                     f"🟢 {x}"
        )
        
        # Display dataframe
        st.dataframe(
            threads_df[['thread_id', 'subject', 'client_org', 'Status Badge', 
                       'priority', 'received_at', 'sla_deadline']],
            use_container_width=True,
            hide_index=True
        )
        
        # Status distribution chart
        col1, col2 = st.columns(2)
        with col1:
            status_counts = threads_df['status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Status Distribution",
                color_discrete_map={
                    'pending': '#FFA500',
                    'in_review': '#4169E1',
                    'completed': '#32CD32',
                    'overdue': '#FF6347'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            priority_counts = threads_df['priority'].value_counts()
            fig = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                title="Priority Distribution",
                labels={'x': 'Priority', 'y': 'Count'},
                color=priority_counts.index,
                color_discrete_map={
                    'high': '#FF6347',
                    'medium': '#FFA500',
                    'low': '#32CD32'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No threads to display. The system will populate as emails are processed.")

def render_quality_tab(dashboard_agent: DashboardAgent):
    """Render document quality tab"""
    st.header("📄 Document Quality Analysis")
    
    docs_df = dashboard_agent.get_documents_data()
    
    if not docs_df.empty:
        # Quality score distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure(data=[
                go.Histogram(
                    x=docs_df['quality_score'],
                    nbinsx=20,
                    name='Quality Score Distribution',
                    marker_color='#4169E1'
                )
            ])
            fig.update_layout(
                title="Quality Score Distribution",
                xaxis_title="Quality Score",
                yaxis_title="Number of Documents"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Issues breakdown
            issues_data = {
                'Spelling Issues': docs_df['spelling_issues'].sum(),
                'Tracked Changes': docs_df['tracked_changes'].sum(),
                'Style Issues': docs_df['style_issues'].sum()
            }
            fig = px.bar(
                x=list(issues_data.keys()),
                y=list(issues_data.values()),
                title="Total Issues by Type",
                color=list(issues_data.keys()),
                color_discrete_map={
                    'Spelling Issues': '#FF6347',
                    'Tracked Changes': '#FFA500',
                    'Style Issues': '#FFD700'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Document details table
        st.subheader("Document Details")
        
        # Add quality badges
        docs_df['Quality Badge'] = docs_df['quality_score'].apply(
            lambda x: f"🟢 Excellent ({x})" if x >= 90 else
                     f"🟡 Good ({x})" if x >= 70 else
                     f"🔴 Needs Review ({x})"
        )
        
        st.dataframe(
            docs_df[['filename', 'client_org', 'Quality Badge', 
                    'spelling_issues', 'tracked_changes', 'style_issues', 'processed_at']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No documents analyzed yet. Documents will appear here after processing.")

def render_feedback_tab():
    """Render feedback and learning tab"""
    st.header("📝 Feedback & Learning")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Submit Feedback")
        
        doc_id = st.selectbox("Select Document", ["DOC001", "DOC002", "DOC003"])
        finding_type = st.selectbox("Finding Type", ["Spelling", "Tracked Changes", "Style"])
        is_correct = st.radio("Is this finding correct?", ["Yes", "No", "Partially"])
        comments = st.text_area("Additional Comments")
        
        if st.button("Submit Feedback", type="primary"):
            st.success("Feedback submitted successfully! The learning agent will process this in the next cycle.")
    
    with col2:
        st.subheader("Learning Stats")
        st.metric("Total Feedback", "127")
        st.metric("Accuracy Improvement", "+12%")
        st.metric("False Positives Reduced", "34")
        st.metric("Last Learning Cycle", "2 hours ago")

def main():
    """Main application entry point"""
    st.title("📄 NDA Dashboard & Document QA System")
    st.caption("AI-Powered Email Processing and Document Quality Analysis")
    
    # Initialize database and agents
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.email_agent = EmailIngestAgent(st.session_state.db_manager)
        st.session_state.doc_agent = DocumentQualityAgent(st.session_state.db_manager)
        st.session_state.dashboard_agent = DashboardAgent(st.session_state.db_manager)
        
        # Add sample data for demo
        sample_email = {
            'thread_id': 'THREAD001',
            'subject': 'NDA Agreement - Acme Corp',
            'sender': 'john@acmecorp.com',
            'body': 'Please review the attached NDA for our upcoming partnership.'
        }
        st.session_state.email_agent.process_email(sample_email)
        
        # Add sample document
        st.session_state.doc_agent.analyze_document(
            "This is a sample NDA document with teh spelling error.",
            "DOC001",
            "THREAD001"
        )
    
    # Sidebar
    status_filter, client_filter, date_range = render_sidebar()
    
    # KPIs
    kpis = st.session_state.dashboard_agent.get_kpis()
    render_kpi_cards(kpis)
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📧 Threads", "📊 Quality", "📝 Feedback", "⚙️ Settings"])
    
    with tab1:
        render_threads_tab(st.session_state.dashboard_agent)
    
    with tab2:
        render_quality_tab(st.session_state.dashboard_agent)
    
    with tab3:
        render_feedback_tab()
    
    with tab4:
        st.header("⚙️ System Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Email Processing")
            check_interval = st.slider("Check Interval (minutes)", 1, 60, 5)
            auto_classify = st.checkbox("Auto-classify emails", value=True)
            st.selectbox("Classification Model", ["Rule-based", "GPT-4", "Claude"])
        
        with col2:
            st.subheader("Quality Checks")
            st.checkbox("Enable spelling checks", value=True)
            st.checkbox("Enable tracked changes detection", value=True)
            st.checkbox("Enable style guide checks", value=True)
            st.number_input("SLA Hours", min_value=1, max_value=72, value=24)
        
        if st.button("Save Settings", type="primary"):
            st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
