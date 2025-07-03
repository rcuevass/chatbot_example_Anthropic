#!/usr/bin/env python3
"""
Audit Logging Demo Script

This script demonstrates the audit logging capabilities of the ArXiv Chatbot.
It shows how to use the audit logger programmatically and generate reports.
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from utils.audit_logger import get_audit_logger, cleanup_audit_logger
from utils.audit_analyzer import AuditAnalyzer

def demo_basic_audit_logging():
    """Demonstrate basic audit logging functionality."""
    print("🔐 Demo: Basic Audit Logging")
    print("=" * 50)
    
    # Get audit logger
    audit_logger = get_audit_logger()
    
    # Log some user queries
    print("📝 Logging user queries...")
    audit_logger.log_user_query("Search for quantum computing papers", user_id="demo_user_1")
    audit_logger.log_user_query("Tell me about paper 2412.07992v3", user_id="demo_user_2")
    
    # Log API calls
    print("🌐 Logging API calls...")
    audit_logger.log_api_call(
        model="claude-3-haiku-20240307",
        max_tokens=2048,
        tool_count=2,
        message_count=3,
        duration_ms=1250.5,
        success=True
    )
    
    # Log tool executions
    print("🔧 Logging tool executions...")
    audit_logger.log_tool_execution(
        tool_name="search_papers",
        tool_args={"topic": "quantum computing", "max_results": 5},
        duration_ms=450.2,
        success=True
    )
    
    audit_logger.log_tool_result(
        tool_name="search_papers",
        result_size=2048,
        result_type="text"
    )
    
    # Log some errors
    print("❌ Logging errors...")
    audit_logger.log_error(
        component="api",
        operation="anthropic_call",
        error_message="Rate limit exceeded"
    )
    
    # Log security events
    print("🛡️ Logging security events...")
    audit_logger.log_security_event(
        "Multiple failed login attempts detected",
        severity="warning",
        details={"ip_address": "192.168.1.100", "attempts": 5}
    )
    
    print("✅ Basic audit logging demo completed!\n")

def demo_audit_analysis():
    """Demonstrate audit analysis capabilities."""
    print("📊 Demo: Audit Analysis")
    print("=" * 50)
    
    # Create analyzer
    analyzer = AuditAnalyzer(Path("logs/audit"))
    
    # Get performance metrics for last 7 days
    print("📈 Generating performance metrics...")
    try:
        metrics = analyzer.get_performance_metrics(days=7)
        print(f"   Total events: {metrics['usage']['total_events']}")
        print(f"   User queries: {metrics['usage']['user_queries']}")
        print(f"   API calls: {metrics['usage']['api_calls']}")
        print(f"   Tool executions: {metrics['usage']['tool_executions']}")
        print(f"   Errors: {metrics['usage']['errors']}")
        
        if metrics['usage']['api_calls'] > 0:
            api_success_rate = metrics['performance']['api']['success_rate']
            print(f"   API success rate: {api_success_rate:.2%}")
            
            avg_api_duration = metrics['performance']['api']['avg_duration_ms']
            print(f"   Average API duration: {avg_api_duration:.1f}ms")
    except Exception as e:
        print(f"   No audit data available yet: {e}")
    
    # Get compliance report
    print("\n📋 Generating compliance report...")
    try:
        compliance = analyzer.get_compliance_report(days=30)
        print(f"   Total sessions: {compliance['summary']['total_sessions']}")
        print(f"   Sessions with errors: {compliance['summary']['sessions_with_errors']}")
        print(f"   Error rate: {compliance['summary']['error_rate']:.2%}")
        print(f"   Average session duration: {compliance['summary']['avg_session_duration_seconds']:.1f}s")
    except Exception as e:
        print(f"   No compliance data available yet: {e}")
    
    # Export reports
    print("\n💾 Exporting reports...")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    try:
        analyzer.export_report(
            "performance", 
            reports_dir / "demo_performance.json", 
            days=7
        )
        print("   ✅ Performance report exported to reports/demo_performance.json")
        
        analyzer.export_report(
            "compliance", 
            reports_dir / "demo_compliance.json", 
            days=30
        )
        print("   ✅ Compliance report exported to reports/demo_compliance.json")
    except Exception as e:
        print(f"   ❌ Report export failed: {e}")
    
    print("✅ Audit analysis demo completed!\n")

def demo_session_tracking():
    """Demonstrate session tracking capabilities."""
    print("🔄 Demo: Session Tracking")
    print("=" * 50)
    
    # Get audit logger (this creates a new session)
    audit_logger = get_audit_logger()
    
    print(f"📱 Session ID: {audit_logger.session_id}")
    
    # Simulate a user session
    print("👤 Simulating user session...")
    
    # User starts session
    audit_logger.log_security_event(
        "User session started",
        severity="info",
        details={"session_type": "demo_session"}
    )
    
    # User makes queries
    audit_logger.log_user_query("What are the latest papers on machine learning?")
    time.sleep(0.1)  # Simulate processing time
    
    audit_logger.log_api_call(
        model="claude-3-haiku-20240307",
        max_tokens=2048,
        tool_count=2,
        message_count=2,
        duration_ms=850.3,
        success=True
    )
    
    audit_logger.log_tool_execution(
        tool_name="search_papers",
        tool_args={"topic": "machine learning", "max_results": 3},
        duration_ms=320.1,
        success=True
    )
    
    audit_logger.log_user_query("Tell me more about the first paper")
    time.sleep(0.1)
    
    audit_logger.log_api_call(
        model="claude-3-haiku-20240307",
        max_tokens=2048,
        tool_count=2,
        message_count=4,
        duration_ms=1200.7,
        success=True
    )
    
    # Session ends
    audit_logger.log_security_event(
        "User session ended",
        severity="info",
        details={"session_type": "demo_session"}
    )
    
    # Get session summary
    print("\n📊 Session Summary:")
    summary = audit_logger.get_session_summary()
    print(f"   Session ID: {summary['session_id']}")
    print(f"   Start time: {summary['start_time']}")
    print(f"   Log directory: {summary['log_directory']}")
    
    print("✅ Session tracking demo completed!\n")

def main():
    """Run all audit logging demos."""
    print("🚀 ArXiv Chatbot - Audit Logging Demo")
    print("=" * 60)
    print()
    
    # Check if audit logging is enabled
    if not config.enable_audit_logging:
        print("⚠️  Audit logging is disabled in configuration.")
        print("   Set ENABLE_AUDIT_LOGGING=true in your .env file to enable it.")
        print()
        return
    
    print(f"📋 Audit Configuration:")
    audit_config = config.get_audit_config_summary()
    for key, value in audit_config.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        # Run demos
        demo_basic_audit_logging()
        demo_session_tracking()
        demo_audit_analysis()
        
        print("🎉 All demos completed successfully!")
        print()
        print("📁 Check the following directories for generated files:")
        print("   - logs/audit/     (audit log files)")
        print("   - reports/        (analysis reports)")
        print()
        print("🔍 To analyze the generated audit data:")
        print("   python utils/audit_analyzer.py --report-type performance --days 1")
        print("   python utils/audit_analyzer.py --report-type compliance --days 1")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up audit logger
        cleanup_audit_logger()

if __name__ == "__main__":
    main() 