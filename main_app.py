# agents/email_agent.py
"""Email Processing Agent - Handles email ingestion and classification"""

from datetime import datetime, timedelta
from typing import Dict, List

class EmailAgent:
    def __init__(self):
        self.processed_count = 0
    
    def classify_email(self, subject: str, body: str = "") -> Dict:
        """Classify email based on content"""
        # Simple rule-based classification
        is_nda = any(word in subject.lower() 
                    for word in ['nda', 'agreement', 'confidential'])
        
        priority = 'high' if 'urgent' in subject.lower() else 'medium'
        
        return {
            'is_nda': is_nda,
            'priority': priority,
            'status': 'pending',
            'category': 'contract' if is_nda else 'other'
        }
    
    def process_email(self, email_data: Dict) -> Dict:
        """Process single email and return thread data"""
        classification = self.classify_email(
            email_data.get('subject', ''),
            email_data.get('body', '')
        )
        
        self.processed_count += 1
        
        return {
            'id': f'T{self.processed_count:03d}',
            'subject': email_data.get('subject', 'No Subject'),
            'sender': email_data.get('sender', 'unknown@email.com'),
            'client': self.extract_client(email_data.get('subject', '')),
            'status': classification['status'],
            'priority': classification['priority'],
            'received': datetime.now(),
            'deadline': datetime.now() + timedelta(hours=24)
        }
    
    def extract_client(self, subject: str) -> str:
        """Extract client name from subject"""
        # Simple extraction logic
        clients = ['Acme Corp', 'TechCo', 'GlobalTrade']
        for client in clients:
            if client.lower() in subject.lower():
                return client
        return 'Unknown Client'

# =====================================

# agents/document_agent.py
"""Document Quality Agent - Analyzes document quality"""

from typing import Dict, List

class DocumentAgent:
    def __init__(self):
        self.analyzed_count = 0
    
    def analyze_quality(self, content: str) -> Dict:
        """Analyze document quality"""
        # Simple quality metrics
        word_count = len(content.split())
        
        # Mock quality checks
        spelling_issues = min(3, max(0, word_count // 500))
        style_issues = 1 if word_count > 5000 else 0
        
        # Calculate score
        base_score = 100
        score = base_score - (spelling_issues * 5) - (style_issues * 10)
        score = max(0, min(100, score))
        
        self.analyzed_count += 1
        
        return {
            'id': f'D{self.analyzed_count:03d}',
            'quality_score': score,
            'word_count': word_count,
            'spelling_issues': spelling_issues,
            'style_issues': style_issues,
            'status': 'analyzed'
        }
    
    def check_compliance(self, content: str) -> bool:
        """Check if document meets compliance standards"""
        required_sections = ['confidential', 'agreement', 'parties']
        content_lower = content.lower()
        return all(section in content_lower for section in required_sections)

# =====================================

# agents/dashboard_agent.py
"""Dashboard Agent - Manages KPIs and metrics"""

from typing import Dict, List
from datetime import datetime

class DashboardAgent:
    def __init__(self):
        self.last_update = datetime.now()
    
    def calculate_kpis(self, threads: List[Dict]) -> Dict:
        """Calculate dashboard KPIs"""
        total = len(threads)
        
        if total == 0:
            return {
                'total_threads': 0,
                'pending': 0,
                'in_review': 0,
                'completed': 0,
                'overdue': 0,
                'sla_compliance': 100.0,
                'avg_response_time': 0
            }
        
        # Count by status
        status_counts = {'pending': 0, 'in_review': 0, 'completed': 0}
        for thread in threads:
            status = thread.get('status', 'pending')
            if status in status_counts:
                status_counts[status] += 1
        
        # Count overdue
        now = datetime.now()
        overdue = sum(1 for t in threads 
                     if t.get('deadline') and t['deadline'] < now 
                     and t.get('status') != 'completed')
        
        # SLA compliance
        sla_compliance = ((total - overdue) / total * 100) if total > 0 else 100
        
        return {
            'total_threads': total,
            'pending': status_counts['pending'],
            'in_review': status_counts['in_review'],
            'completed': status_counts['completed'],
            'overdue': overdue,
            'sla_compliance': round(sla_compliance, 1),
            'avg_response_time': 4.5  # Mock value
        }
    
    def get_trend_data(self, threads: List[Dict], days: int = 7) -> Dict:
        """Get trend data for charts"""
        # Mock trend data
        return {
            'daily_volumes': [5, 8, 6, 10, 7, 9, 11],
            'completion_rates': [80, 85, 78, 92, 88, 90, 95],
            'dates': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        }

# =====================================

# utils/helpers.py
"""Helper utilities for the NDA Dashboard"""

from datetime import datetime, timedelta
import hashlib
import json

def generate_id(prefix: str, content: str) -> str:
    """Generate unique ID"""
    hash_obj = hashlib.md5(content.encode())
    return f"{prefix}_{hash_obj.hexdigest()[:8]}"

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M")

def calculate_time_remaining(deadline: datetime) -> str:
    """Calculate time remaining until deadline"""
    remaining = deadline - datetime.now()
    hours = remaining.total_seconds() / 3600
    
    if hours < 0:
        return "Overdue"
    elif hours < 1:
        return f"{int(hours * 60)} minutes"
    elif hours < 24:
        return f"{int(hours)} hours"
    else:
        return f"{int(hours / 24)} days"

def load_config():
    """Load configuration settings"""
    return {
        'sla_hours': 24,
        'enable_alerts': True,
        'quality_threshold': 80,
        'max_threads_display': 100
    }
