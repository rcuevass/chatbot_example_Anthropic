"""Audit log analyzer for the ArXiv Chatbot - provides insights and compliance reporting."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import argparse

class AuditAnalyzer:
    """Analyzes audit logs for insights and compliance reporting."""
    
    def __init__(self, audit_log_dir: Path):
        """
        Initialize the audit analyzer.
        
        Args:
            audit_log_dir: Directory containing audit log files
        """
        self.audit_log_dir = audit_log_dir
        self.logger = logging.getLogger(__name__)
    
    def load_audit_events(self, start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Load audit events from log files within the specified date range.
        
        Args:
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            
        Returns:
            List of audit events
        """
        events = []
        
        if not self.audit_log_dir.exists():
            self.logger.warning(f"Audit log directory does not exist: {self.audit_log_dir}")
            return events
        
        # Find all audit log files
        log_files = list(self.audit_log_dir.glob("audit_*.log"))
        
        for log_file in log_files:
            # Extract date from filename (audit_YYYYMMDD.log)
            try:
                date_str = log_file.stem.split("_")[1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                # Filter by date range if specified
                if start_date and file_date < start_date.date():
                    continue
                if end_date and file_date > end_date.date():
                    continue
                    
            except (IndexError, ValueError):
                self.logger.warning(f"Could not parse date from filename: {log_file.name}")
                continue
            
            # Read events from file
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Invalid JSON in {log_file.name}:{line_num}: {e}")
                            
            except Exception as e:
                self.logger.error(f"Error reading {log_file}: {e}")
        
        return events
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary dictionary
        """
        events = self.load_audit_events()
        session_events = [e for e in events if e.get("session_id") == session_id]
        
        if not session_events:
            return {"error": f"Session {session_id} not found"}
        
        # Sort events by timestamp
        session_events.sort(key=lambda x: x.get("timestamp", ""))
        
        # Calculate statistics
        event_types = Counter(e.get("event_type") for e in session_events)
        components = Counter(e.get("component") for e in session_events)
        
        # Find session start and end
        start_event = next((e for e in session_events if e.get("event_type") == "session_start"), None)
        end_event = next((e for e in session_events if e.get("event_type") == "session_end"), None)
        
        # Calculate session duration
        session_duration = None
        if start_event and end_event:
            start_time = datetime.fromisoformat(start_event["timestamp"])
            end_time = datetime.fromisoformat(end_event["timestamp"])
            session_duration = (end_time - start_time).total_seconds()
        
        # Find errors
        errors = [e for e in session_events if e.get("event_type") == "error"]
        
        return {
            "session_id": session_id,
            "start_time": start_event["timestamp"] if start_event else None,
            "end_time": end_event["timestamp"] if end_event else None,
            "duration_seconds": session_duration,
            "total_events": len(session_events),
            "event_types": dict(event_types),
            "components": dict(components),
            "error_count": len(errors),
            "errors": [{"operation": e.get("operation"), "error_message": e.get("error_message")} 
                      for e in errors]
        }
    
    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get performance metrics for the specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance metrics dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        events = self.load_audit_events(start_date, end_date)
        
        # Filter relevant events
        api_calls = [e for e in events if e.get("event_type") == "api_call"]
        tool_executions = [e for e in events if e.get("event_type") == "tool_execution"]
        user_queries = [e for e in events if e.get("event_type") == "user_query"]
        errors = [e for e in events if e.get("event_type") == "error"]
        
        # Calculate API performance
        api_durations = [e.get("duration_ms", 0) for e in api_calls if e.get("success")]
        api_success_rate = len([e for e in api_calls if e.get("success")]) / len(api_calls) if api_calls else 0
        
        # Calculate tool performance
        tool_durations = [e.get("duration_ms", 0) for e in tool_executions if e.get("success")]
        tool_success_rate = len([e for e in tool_executions if e.get("success")]) / len(tool_executions) if tool_executions else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "usage": {
                "total_events": len(events),
                "user_queries": len(user_queries),
                "api_calls": len(api_calls),
                "tool_executions": len(tool_executions),
                "errors": len(errors)
            },
            "performance": {
                "api": {
                    "avg_duration_ms": sum(api_durations) / len(api_durations) if api_durations else 0,
                    "min_duration_ms": min(api_durations) if api_durations else 0,
                    "max_duration_ms": max(api_durations) if api_durations else 0,
                    "success_rate": api_success_rate
                },
                "tools": {
                    "avg_duration_ms": sum(tool_durations) / len(tool_durations) if tool_durations else 0,
                    "min_duration_ms": min(tool_durations) if tool_durations else 0,
                    "max_duration_ms": max(tool_durations) if tool_durations else 0,
                    "success_rate": tool_success_rate
                }
            },
            "errors": {
                "total": len(errors),
                "by_component": dict(Counter(e.get("component") for e in errors)),
                "by_operation": dict(Counter(e.get("operation") for e in errors))
            }
        }
    
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate a compliance report for audit purposes.
        
        Args:
            days: Number of days to include in the report
            
        Returns:
            Compliance report dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        events = self.load_audit_events(start_date, end_date)
        
        # Group events by session
        sessions = defaultdict(list)
        for event in events:
            session_id = event.get("session_id")
            if session_id:
                sessions[session_id].append(event)
        
        # Analyze each session
        session_summaries = []
        for session_id, session_events in sessions.items():
            summary = self.get_session_summary(session_id)
            session_summaries.append(summary)
        
        # Calculate compliance metrics
        total_sessions = len(sessions)
        sessions_with_errors = len([s for s in session_summaries if s.get("error_count", 0) > 0])
        avg_session_duration = sum(s.get("duration_seconds", 0) for s in session_summaries) / total_sessions if total_sessions > 0 else 0
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_sessions": total_sessions,
                "total_events": len(events),
                "sessions_with_errors": sessions_with_errors,
                "error_rate": sessions_with_errors / total_sessions if total_sessions > 0 else 0,
                "avg_session_duration_seconds": avg_session_duration
            },
            "event_breakdown": {
                "by_type": dict(Counter(e.get("event_type") for e in events)),
                "by_component": dict(Counter(e.get("component") for e in events))
            },
            "security_events": [
                e for e in events if e.get("event_type") == "security_event"
            ],
            "sessions": session_summaries
        }
    
    def export_report(self, report_type: str, output_file: Path, **kwargs) -> None:
        """
        Export a report to a file.
        
        Args:
            report_type: Type of report ("performance", "compliance", "session")
            output_file: Output file path
            **kwargs: Additional arguments for the report
        """
        if report_type == "performance":
            data = self.get_performance_metrics(**kwargs)
        elif report_type == "compliance":
            data = self.get_compliance_report(**kwargs)
        elif report_type == "session":
            if "session_id" not in kwargs:
                raise ValueError("session_id is required for session reports")
            data = self.get_session_summary(kwargs["session_id"])
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Report exported to: {output_file}")

def main():
    """Command-line interface for audit analysis."""
    parser = argparse.ArgumentParser(description="Analyze ArXiv Chatbot audit logs")
    parser.add_argument("--log-dir", type=Path, default=Path("logs/audit"),
                       help="Audit log directory")
    parser.add_argument("--report-type", choices=["performance", "compliance", "session"],
                       required=True, help="Type of report to generate")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    parser.add_argument("--session-id", help="Session ID for session reports")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = AuditAnalyzer(args.log_dir)
    
    # Generate report
    if args.report_type == "session" and not args.session_id:
        print("Error: session-id is required for session reports")
        return
    
    if args.output:
        analyzer.export_report(
            args.report_type,
            args.output,
            days=args.days,
            session_id=args.session_id
        )
    else:
        # Print to console
        if args.report_type == "performance":
            data = analyzer.get_performance_metrics(args.days)
        elif args.report_type == "compliance":
            data = analyzer.get_compliance_report(args.days)
        else:  # session
            data = analyzer.get_session_summary(args.session_id)
        
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main() 