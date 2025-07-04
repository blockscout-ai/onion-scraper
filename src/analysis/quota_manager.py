#!/usr/bin/env python3
"""
OpenAI API Quota Manager
Helps manage and monitor OpenAI API usage to avoid quota errors
"""

import json
import time
from datetime import datetime, timedelta

class APIQuotaManager:
    def __init__(self, quota_file="api_quota.json"):
        self.quota_file = quota_file
        self.load_quota_data()
    
    def load_quota_data(self):
        """Load quota data from file"""
        try:
            with open(self.quota_file, 'r') as f:
                data = json.load(f)
            self.daily_calls = data.get('daily_calls', 0)
            self.last_reset = datetime.fromisoformat(data.get('last_reset', datetime.now().isoformat()))
            self.quota_limit = data.get('quota_limit', 50)
        except (FileNotFoundError, json.JSONDecodeError):
            self.daily_calls = 0
            self.last_reset = datetime.now()
            self.quota_limit = 50
    
    def save_quota_data(self):
        """Save quota data to file"""
        data = {
            'daily_calls': self.daily_calls,
            'last_reset': self.last_reset.isoformat(),
            'quota_limit': self.quota_limit
        }
        with open(self.quota_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_and_reset_daily(self):
        """Check if we need to reset daily counter"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.daily_calls = 0
            self.last_reset = now
            self.save_quota_data()
            print(f"📅 Daily quota reset: {self.daily_calls}/{self.quota_limit}")
    
    def can_make_call(self):
        """Check if we can make an API call"""
        self.check_and_reset_daily()
        return self.daily_calls < self.quota_limit
    
    def record_call(self):
        """Record an API call"""
        self.daily_calls += 1
        self.save_quota_data()
    
    def get_status(self):
        """Get current quota status"""
        self.check_and_reset_daily()
        return {
            'daily_calls': self.daily_calls,
            'quota_limit': self.quota_limit,
            'remaining': self.quota_limit - self.daily_calls,
            'percentage_used': (self.daily_calls / self.quota_limit) * 100,
            'last_reset': self.last_reset.isoformat()
        }
    
    def set_quota_limit(self, limit):
        """Set daily quota limit"""
        self.quota_limit = limit
        self.save_quota_data()
        print(f"📊 Quota limit set to {limit}")

def main():
    """CLI interface for quota manager"""
    import sys
    
    manager = APIQuotaManager()
    
    if len(sys.argv) < 2:
        # Show status
        status = manager.get_status()
        print("📊 OpenAI API Quota Status")
        print(f"   Daily calls: {status['daily_calls']}/{status['quota_limit']}")
        print(f"   Remaining: {status['remaining']}")
        print(f"   Usage: {status['percentage_used']:.1f}%")
        print(f"   Last reset: {status['last_reset']}")
        
        if status['remaining'] <= 0:
            print("🚨 QUOTA EXCEEDED - No API calls available today")
        elif status['remaining'] <= 5:
            print("⚠️ WARNING - Low quota remaining")
        else:
            print("✅ Quota OK")
    
    elif sys.argv[1] == "set-limit":
        if len(sys.argv) != 3:
            print("Usage: python quota_manager.py set-limit <number>")
            sys.exit(1)
        try:
            limit = int(sys.argv[2])
            manager.set_quota_limit(limit)
        except ValueError:
            print("Error: Limit must be a number")
            sys.exit(1)
    
    elif sys.argv[1] == "reset":
        manager.daily_calls = 0
        manager.last_reset = datetime.now()
        manager.save_quota_data()
        print("🔄 Quota counter reset")
    
    elif sys.argv[1] == "disable-ai":
        print("🚨 To disable AI features in scraper:")
        print("   Edit scraper_fast.py and set: EMERGENCY_MODE = True")
        print("   This will disable all AI features to prevent quota errors")
    
    elif sys.argv[1] == "help":
        print("OpenAI API Quota Manager")
        print("Commands:")
        print("  python quota_manager.py              - Show status")
        print("  python quota_manager.py set-limit N  - Set daily limit to N")
        print("  python quota_manager.py reset        - Reset daily counter")
        print("  python quota_manager.py disable-ai   - Show how to disable AI")
        print("  python quota_manager.py help         - Show this help")
    
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Use 'python quota_manager.py help' for available commands")

if __name__ == "__main__":
    main() 