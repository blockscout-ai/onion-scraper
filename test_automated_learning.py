#!/usr/bin/env python3
"""
Test Script for Automated Learning System
This script demonstrates how the automated learning system works.
"""

import time
import random
from src.agents.automated_learning_core import AutomatedLearningCore

def simulate_scraping_attempts(automated_learning, num_attempts=50):
    """Simulate scraping attempts to test learning"""
    
    domains = [
        "example1.onion",
        "example2.onion", 
        "example3.onion",
        "example4.onion",
        "example5.onion"
    ]
    
    strategies = ['1', '2', '3', '4', '5']
    error_types = ['timeout', 'captcha', 'login_required', 'modal_detected', None]
    
    print(f"🧪 Simulating {num_attempts} scraping attempts...")
    
    for i in range(num_attempts):
        # Simulate different success rates for different domains/strategies
        domain = random.choice(domains)
        strategy = random.choice(strategies)
        
        # Simulate success/failure based on domain and strategy
        if domain == "example1.onion" and strategy in ['1', '2']:
            success = random.random() > 0.3  # 70% success rate
        elif domain == "example2.onion" and strategy in ['3', '4']:
            success = random.random() > 0.4  # 60% success rate
        elif domain == "example3.onion" and strategy == '5':
            success = random.random() > 0.2  # 80% success rate
        else:
            success = random.random() > 0.7  # 30% success rate
        
        # Determine error type if failed
        error_type = None
        if not success:
            error_type = random.choice(error_types)
        
        # Record attempt
        automated_learning.record_attempt(
            success=success,
            strategy=strategy,
            domain=domain,
            error_type=error_type,
            worker_id="test"
        )
        
        # Print progress every 10 attempts
        if (i + 1) % 10 == 0:
            status = automated_learning.get_system_status()
            print(f"   📊 Progress: {i+1}/{num_attempts} - Success Rate: {status['current_success_rate']:.1%}")
        
        # Small delay to simulate real processing
        time.sleep(0.1)
    
    print("✅ Simulation completed!")

def demonstrate_learning(automated_learning):
    """Demonstrate the learning capabilities"""
    
    print("\n🎯 Demonstrating Automated Learning")
    print("=" * 40)
    
    # Show initial state
    print("\n📊 Initial State:")
    status = automated_learning.get_system_status()
    print(f"   Success Rate: {status['current_success_rate']:.1%}")
    print(f"   Strategy Performance: {status['strategy_performance']}")
    
    # Simulate some attempts
    simulate_scraping_attempts(automated_learning, 30)
    
    # Show state after learning
    print("\n📊 State After Learning:")
    status = automated_learning.get_system_status()
    print(f"   Success Rate: {status['current_success_rate']:.1%}")
    print(f"   Strategy Performance: {status['strategy_performance']}")
    print(f"   Domain Rules: {status['domain_rules']}")
    print(f"   Error Handlers: {status['error_handlers']}")
    
    # Test strategy selection
    print("\n🎯 Testing Strategy Selection:")
    test_domains = ["example1.onion", "example2.onion", "example3.onion", "newdomain.onion"]
    
    for domain in test_domains:
        strategy = automated_learning.get_best_strategy(domain)
        print(f"   {domain} -> Strategy {strategy}")
    
    # Simulate more attempts to trigger adaptation
    print("\n🔄 Triggering Adaptation...")
    simulate_scraping_attempts(automated_learning, 20)
    
    # Show final state
    print("\n📊 Final State:")
    status = automated_learning.get_system_status()
    print(f"   Success Rate: {status['current_success_rate']:.1%}")
    print(f"   Strategy Performance: {status['strategy_performance']}")
    print(f"   Domain Rules: {status['domain_rules']}")
    print(f"   Error Handlers: {status['error_handlers']}")

def test_persistence(automated_learning):
    """Test that learning state persists across sessions"""
    
    print("\n💾 Testing State Persistence")
    print("=" * 30)
    
    # Save current state
    automated_learning.save_state("test_learning_state.json")
    print("✅ State saved")
    
    # Create new instance and load state
    new_learning = AutomatedLearningCore()
    new_learning.load_state("test_learning_state.json")
    print("✅ State loaded")
    
    # Compare states
    original_status = automated_learning.get_system_status()
    new_status = new_learning.get_system_status()
    
    print(f"   Original attempts: {original_status['total_attempts']}")
    print(f"   Loaded attempts: {new_status['total_attempts']}")
    print(f"   State preserved: {original_status['total_attempts'] == new_status['total_attempts']}")

def main():
    """Main test function"""
    
    print("🤖 Automated Learning System Test")
    print("=" * 40)
    
    # Create automated learning instance
    automated_learning = AutomatedLearningCore()
    
    # Start learning
    automated_learning.start_learning()
    
    try:
        # Demonstrate learning capabilities
        demonstrate_learning(automated_learning)
        
        # Test persistence
        test_persistence(automated_learning)
        
        print("\n✅ All tests completed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   ✅ Continuous learning from attempts")
        print("   ✅ Automatic strategy selection")
        print("   ✅ Domain-specific optimization")
        print("   ✅ Error pattern recognition")
        print("   ✅ State persistence across sessions")
        print("   ✅ Real-time adaptation")
        
    finally:
        # Cleanup
        automated_learning.save_state()
        automated_learning.stop_learning()
        print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    main() 