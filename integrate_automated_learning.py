#!/usr/bin/env python3
"""
Integration Script for Automated Learning System
This script shows how to integrate automated learning into the existing scraper.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the automated learning core
from agents.automated_learning_core import AutomatedLearningCore

def integrate_with_scraper():
    """
    Integration example showing how to add automated learning to scraper_fast.py
    """
    
    print("🔧 Automated Learning Integration Guide")
    print("=" * 50)
    
    # Create automated learning instance
    automated_learning = AutomatedLearningCore()
    
    # Load existing state if available
    automated_learning.load_state()
    
    # Start automated learning
    automated_learning.start_learning()
    
    print("\n📋 Integration Steps for scraper_fast.py:")
    print("=" * 50)
    
    print("""
1. Add import at the top of scraper_fast.py:
   ```python
   from agents.automated_learning_core import automated_learning
   ```

2. Initialize automated learning in main():
   ```python
   def main():
       # Start automated learning
       automated_learning.start_learning()
       
       # Load existing state
       automated_learning.load_state()
       
       # ... rest of main function
   ```

3. Modify process_url_fast() to record attempts:
   ```python
   def process_url_fast(url, worker_id):
       # Extract domain for learning
       domain = url.split('/')[2] if '//' in url else url
       
       try:
           # Get best strategy from automated learning
           strategy = automated_learning.get_best_strategy(domain)
           
           # Process URL with selected strategy
           result = original_process_url(url, worker_id, strategy)
           
           # Record successful attempt
           automated_learning.record_attempt(
               success=True,
               strategy=strategy,
               domain=domain,
               worker_id=worker_id
           )
           
           return result
           
       except Exception as e:
           # Record failed attempt
           automated_learning.record_attempt(
               success=False,
               strategy=strategy,
               domain=domain,
               error_type=type(e).__name__,
               worker_id=worker_id
           )
           raise
   ```

4. Add cleanup in main():
   ```python
   def main():
       try:
           # ... main processing ...
       finally:
           # Save learning state
           automated_learning.save_state()
           automated_learning.stop_learning()
   ```

5. Add status reporting:
   ```python
   def print_agent_status():
       # ... existing status ...
       
       # Add automated learning status
       learning_status = automated_learning.get_system_status()
       print(f"🤖 Automated Learning: {'Active' if learning_status['learning_active'] else 'Inactive'}")
       print(f"   📊 Success Rate: {learning_status['current_success_rate']:.1%}")
       print(f"   🔄 Consecutive Failures: {learning_status['consecutive_failures']}")
       print(f"   🎯 Domain Rules: {learning_status['domain_rules']}")
   ```
""")
    
    print("\n🎯 Key Benefits:")
    print("- Automatic strategy selection based on domain performance")
    print("- Continuous learning from successes and failures")
    print("- Automatic adaptation when performance drops")
    print("- Domain-specific optimization rules")
    print("- Persistent learning state across runs")
    
    print("\n📊 Current System Status:")
    status = automated_learning.get_system_status()
    print(f"   Learning Active: {status['learning_active']}")
    print(f"   Total Attempts: {status['total_attempts']}")
    print(f"   Domain Rules: {status['domain_rules']}")
    print(f"   Error Handlers: {status['error_handlers']}")
    
    # Stop learning for this demo
    automated_learning.stop_learning()
    
    print("\n✅ Integration guide complete!")
    print("   The automated learning system is ready to be integrated into your scraper.")

if __name__ == "__main__":
    integrate_with_scraper() 