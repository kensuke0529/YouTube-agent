import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Alert:
    """Represents an alert for monitoring"""
    timestamp: datetime
    level: str  # "info", "warning", "error", "critical"
    message: str
    details: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "details": self.details or {}
        }


class MonitoringService:
    """Service for monitoring usage and sending alerts"""
    
    def __init__(self):
        self.alerts_file = os.getenv("ALERTS_FILE", "data/alerts.json")
        self.max_alerts = int(os.getenv("MAX_ALERTS", "1000"))
        
        # Alert thresholds
        self.daily_usage_warning_threshold = float(os.getenv("DAILY_USAGE_WARNING_THRESHOLD", "0.8"))  # 80%
        self.daily_usage_critical_threshold = float(os.getenv("DAILY_USAGE_CRITICAL_THRESHOLD", "0.95"))  # 95%
        self.hourly_usage_warning_threshold = float(os.getenv("HOURLY_USAGE_WARNING_THRESHOLD", "0.8"))  # 80%
        self.hourly_usage_critical_threshold = float(os.getenv("HOURLY_USAGE_CRITICAL_THRESHOLD", "0.95"))  # 95%
        
        # Rate limiting thresholds
        self.rate_limit_warning_threshold = float(os.getenv("RATE_LIMIT_WARNING_THRESHOLD", "0.8"))  # 80%
        self.rate_limit_critical_threshold = float(os.getenv("RATE_LIMIT_CRITICAL_THRESHOLD", "0.95"))  # 95%
        
        # Load existing alerts
        self.alerts: List[Alert] = self._load_alerts()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for monitoring"""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("monitoring")
    
    def _load_alerts(self) -> List[Alert]:
        """Load alerts from storage"""
        try:
            os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                    alerts = []
                    for alert_data in data:
                        alerts.append(Alert(
                            timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                            level=alert_data["level"],
                            message=alert_data["message"],
                            details=alert_data.get("details", {})
                        ))
                    return alerts
        except Exception as e:
            self.logger.error(f"Failed to load alerts: {e}")
        return []
    
    def _save_alerts(self):
        """Save alerts to storage"""
        try:
            os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
            # Keep only recent alerts
            recent_alerts = self.alerts[-self.max_alerts:]
            with open(self.alerts_file, 'w') as f:
                json.dump([alert.to_dict() for alert in recent_alerts], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save alerts: {e}")
    
    def _add_alert(self, level: str, message: str, details: Dict = None):
        """Add a new alert"""
        alert = Alert(
            timestamp=datetime.now(),
            level=level,
            message=message,
            details=details
        )
        
        self.alerts.append(alert)
        self._save_alerts()
        
        # Log the alert
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"ALERT: {message}", extra={"details": details})
    
    def check_token_usage(self, usage_stats: Dict):
        """Check token usage and create alerts if needed"""
        daily_limit = usage_stats.get("daily_limit", 0)
        daily_usage = usage_stats.get("total_tokens", 0)
        hourly_limit = usage_stats.get("hourly_limit", 0)
        hourly_usage = usage_stats.get("hourly_usage", 0)
        
        if daily_limit > 0:
            daily_ratio = daily_usage / daily_limit
            
            if daily_ratio >= self.daily_usage_critical_threshold:
                self._add_alert(
                    "critical",
                    f"Daily token usage critical: {daily_usage}/{daily_limit} ({daily_ratio:.1%})",
                    {
                        "type": "daily_usage",
                        "usage": daily_usage,
                        "limit": daily_limit,
                        "ratio": daily_ratio
                    }
                )
            elif daily_ratio >= self.daily_usage_warning_threshold:
                self._add_alert(
                    "warning",
                    f"Daily token usage high: {daily_usage}/{daily_limit} ({daily_ratio:.1%})",
                    {
                        "type": "daily_usage",
                        "usage": daily_usage,
                        "limit": daily_limit,
                        "ratio": daily_ratio
                    }
                )
        
        if hourly_limit > 0:
            hourly_ratio = hourly_usage / hourly_limit
            
            if hourly_ratio >= self.hourly_usage_critical_threshold:
                self._add_alert(
                    "critical",
                    f"Hourly token usage critical: {hourly_usage}/{hourly_limit} ({hourly_ratio:.1%})",
                    {
                        "type": "hourly_usage",
                        "usage": hourly_usage,
                        "limit": hourly_limit,
                        "ratio": hourly_ratio
                    }
                )
            elif hourly_ratio >= self.hourly_usage_warning_threshold:
                self._add_alert(
                    "warning",
                    f"Hourly token usage high: {hourly_usage}/{hourly_limit} ({hourly_ratio:.1%})",
                    {
                        "type": "hourly_usage",
                        "usage": hourly_usage,
                        "limit": hourly_limit,
                        "ratio": hourly_ratio
                    }
                )
    
    def check_rate_limiting(self, client_id: str, remaining_requests: Dict):
        """Check rate limiting and create alerts if needed"""
        minute_remaining = remaining_requests.get("minute", 0)
        hour_remaining = remaining_requests.get("hour", 0)
        day_remaining = remaining_requests.get("day", 0)
        
        # Get rate limits from environment
        minute_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        hour_limit = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        day_limit = int(os.getenv("RATE_LIMIT_PER_DAY", "10000"))
        
        # Check minute rate limit
        if minute_remaining <= minute_limit * (1 - self.rate_limit_critical_threshold):
            self._add_alert(
                "critical",
                f"Rate limit critical for client {client_id}: {minute_remaining} requests remaining per minute",
                {
                    "type": "rate_limit",
                    "client_id": client_id,
                    "remaining": minute_remaining,
                    "limit": minute_limit,
                    "period": "minute"
                }
            )
        elif minute_remaining <= minute_limit * (1 - self.rate_limit_warning_threshold):
            self._add_alert(
                "warning",
                f"Rate limit high for client {client_id}: {minute_remaining} requests remaining per minute",
                {
                    "type": "rate_limit",
                    "client_id": client_id,
                    "remaining": minute_remaining,
                    "limit": minute_limit,
                    "period": "minute"
                }
            )
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, 
                       response_time: float, client_id: str = None, 
                       tokens_used: int = None):
        """Log API request for monitoring"""
        details = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "client_id": client_id,
            "tokens_used": tokens_used
        }
        
        # Log slow requests
        if response_time > 5.0:  # 5 seconds
            self._add_alert(
                "warning",
                f"Slow API request: {method} {endpoint} took {response_time:.2f}s",
                details
            )
        
        # Log errors
        if status_code >= 400:
            level = "error" if status_code < 500 else "critical"
            self._add_alert(
                level,
                f"API error: {method} {endpoint} returned {status_code}",
                details
            )
        
        # Log high token usage
        if tokens_used and tokens_used > 10000:  # 10k tokens
            self._add_alert(
                "info",
                f"High token usage request: {method} {endpoint} used {tokens_used} tokens",
                details
            )
    
    def get_recent_alerts(self, hours: int = 24, level: str = None) -> List[Dict]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        
        if level:
            filtered_alerts = [
                alert for alert in filtered_alerts
                if alert.level == level
            ]
        
        return [alert.to_dict() for alert in filtered_alerts]
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        """Get summary of recent alerts"""
        recent_alerts = self.get_recent_alerts(hours)
        
        summary = {
            "total": len(recent_alerts),
            "by_level": {},
            "by_type": {},
            "recent": recent_alerts[-10:]  # Last 10 alerts
        }
        
        for alert in recent_alerts:
            level = alert["level"]
            alert_type = alert.get("details", {}).get("type", "unknown")
            
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
            summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1
        
        return summary
    
    def cleanup_old_alerts(self, days: int = 7):
        """Clean up alerts older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        self._save_alerts()


# Global monitoring service instance
monitoring_service = MonitoringService()
