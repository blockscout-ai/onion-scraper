#!/usr/bin/env python3
"""
Multi-Step Transaction Learning System Demo
Demonstrates how the system learns from transaction patterns and applies them to new cases.
"""

import json
from datetime import datetime

def demonstrate_learning_system():
    """Demonstrate the learning system with the card marketplace example"""
    
    print("🧠 MULTI-STEP TRANSACTION LEARNING SYSTEM DEMO")
    print("=" * 60)
    
    print("\n📋 PROBLEM: Missing Multi-Step Transaction Flows")
    print("Current system misses patterns like:")
    print("   'Buy cards now' → 'Learn More' → 'Price $80' → 'Fill form' → 'Get address'")
    
    print("\n🎯 SOLUTION: Learning-Based Pattern Recognition")
    print("The system now:")
    print("   1. 🔍 ANALYZES page content for transaction patterns")
    print("   2. 📚 LEARNS from successful/failed interaction sequences")
    print("   3. 🎯 APPLIES learned patterns to similar cases")
    print("   4. 🔄 IMPROVES recommendations based on results")
    
    print("\n🔬 HOW IT WORKS:")
    
    # Example 1: Pattern Detection
    print("\n1️⃣ PATTERN DETECTION:")
    example_html = '''
    <div class="item">
        <div class="item__title">VISA $4000</div>
        <div class="price">$115</div>
        <form action="Checkout.php" method="post">
            <input type="hidden" name="vse_kat" value="VISA $4000">
            <input type="hidden" name="vse_sum" value="$115">
            <input type="submit" class="btn" value="Buy">
        </form>
    </div>
    '''
    
    print("   📄 Page Content Analysis:")
    print("   ✅ Detected: 'card_marketplace' pattern")
    print("   ✅ Flow Step: 'product_catalog'")
    print("   ✅ Price Options: $115 for VISA $4000")
    print("   ✅ Buy Button: Direct form submission")
    
    # Example 2: Interaction Sequence
    print("\n2️⃣ SMART INTERACTION SEQUENCE:")
    sequence_example = [
        "🔍 find_product → Select highest value card ($4000)",
        "🖱️ click_button → Click 'Buy' button",
        "⏳ wait_for_modal → Wait for checkout form",
        "📝 fill_form → Fill name, email, address fields",
        "📤 submit_form → Submit and wait for payment address",
        "💰 extract_addresses → Find crypto payment address"
    ]
    
    for step in sequence_example:
        print(f"   {step}")
    
    # Example 3: Learning Process
    print("\n3️⃣ LEARNING PROCESS:")
    learning_examples = [
        {
            'pattern': 'card_marketplace_direct_form',
            'success_rate': 85,
            'usage_count': 12,
            'description': 'Direct form submission for card purchases'
        },
        {
            'pattern': 'modal_price_selection',
            'success_rate': 72,
            'usage_count': 8,
            'description': 'Modal-based price selection workflow'
        },
        {
            'pattern': 'multi_step_checkout',
            'success_rate': 91,
            'usage_count': 15,
            'description': 'Multi-step checkout with form filling'
        }
    ]
    
    print("   📊 Learned Patterns:")
    for pattern in learning_examples:
        print(f"   ✅ {pattern['pattern']}: {pattern['success_rate']}% success ({pattern['usage_count']} uses)")
        print(f"      └─ {pattern['description']}")
    
    # Example 4: Application to New Cases
    print("\n4️⃣ APPLICATION TO NEW CASES:")
    new_cases = [
        {
            'site_type': 'Service Marketplace',
            'pattern': 'Similar to card marketplace',
            'confidence': '78%',
            'action': 'Apply learned card_marketplace sequence'
        },
        {
            'site_type': 'Digital Goods Store',
            'pattern': 'Modal-based selection detected',
            'confidence': '82%',
            'action': 'Use modal_price_selection workflow'
        },
        {
            'site_type': 'Subscription Service',
            'pattern': 'Multi-step checkout form',
            'confidence': '89%',
            'action': 'Execute multi_step_checkout sequence'
        }
    ]
    
    print("   🎯 Smart Recommendations:")
    for case in new_cases:
        print(f"   📍 {case['site_type']}")
        print(f"      🔍 Pattern: {case['pattern']}")
        print(f"      🎯 Confidence: {case['confidence']}")
        print(f"      ⚡ Action: {case['action']}")
        print()
    
    print("🚀 BENEFITS:")
    benefits = [
        "🎯 Handles complex multi-step flows automatically",
        "📚 Learns from each interaction to improve future performance",
        "🔄 Adapts to new site patterns based on learned knowledge",
        "⚡ Reduces 'no_addresses' failures through smarter interaction",
        "🧠 Builds institutional knowledge that persists across sessions",
        "📈 Improves success rate through pattern recognition"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print("\n📊 EXPECTED IMPACT:")
    print("   • Reduce 'no_addresses' failures from 76% to <40%")
    print("   • Increase overall success rate from 1.3% to 8-12%")
    print("   • Handle complex card marketplaces automatically")
    print("   • Learn from each successful transaction flow")
    print("   • Apply knowledge to similar sites automatically")
    
    print("\n🔧 TECHNICAL IMPLEMENTATION:")
    technical_features = [
        "Pattern Recognition Engine",
        "Interaction Sequence Executor", 
        "Learning & Adaptation System",
        "Success/Failure Tracking",
        "Confidence-Based Recommendations",
        "Persistent Pattern Storage"
    ]
    
    for i, feature in enumerate(technical_features, 1):
        print(f"   {i}. {feature}")
    
    print("\n" + "=" * 60)
    print("🎉 READY TO LEARN AND ADAPT!")

def show_example_interaction_log():
    """Show an example of what the interaction log looks like"""
    
    print("\n📋 EXAMPLE INTERACTION LOG:")
    print("=" * 40)
    
    example_log = [
        {
            'step': 1,
            'action': 'find_product',
            'success': True,
            'details': {'price': 4000, 'product': 'VISA $4000'},
            'timestamp': '2025-06-27T22:30:15'
        },
        {
            'step': 2,
            'action': 'click_button',
            'success': True,
            'details': {'button_text': 'Buy', 'form_action': 'Checkout.php'},
            'timestamp': '2025-06-27T22:30:17'
        },
        {
            'step': 3,
            'action': 'fill_form',
            'success': True,
            'details': {'fields_filled': 4, 'form_type': 'checkout'},
            'timestamp': '2025-06-27T22:30:20'
        },
        {
            'step': 4,
            'action': 'submit_form',
            'success': True,
            'details': {'indicators': ['payment', 'address', 'bitcoin']},
            'timestamp': '2025-06-27T22:30:23'
        }
    ]
    
    for log_entry in example_log:
        status = "✅" if log_entry['success'] else "❌"
        print(f"   {status} Step {log_entry['step']}: {log_entry['action']}")
        print(f"      └─ {log_entry['details']}")
        print(f"      └─ Time: {log_entry['timestamp']}")
        print()
    
    print("📈 RESULT: Successfully found crypto payment address!")
    print("🧠 LEARNING: Pattern saved for future use with 100% confidence")

def show_learning_statistics():
    """Show example learning statistics"""
    
    print("\n📊 LEARNING SYSTEM STATISTICS:")
    print("=" * 40)
    
    stats = {
        'total_patterns': 23,
        'successful_patterns': 18,
        'success_rate': 78.3,
        'total_interactions': 156,
        'recent_successes': 8,
        'recent_failures': 2
    }
    
    print(f"   📚 Total Learned Patterns: {stats['total_patterns']}")
    print(f"   ✅ Successful Patterns: {stats['successful_patterns']}")
    print(f"   📈 Pattern Success Rate: {stats['success_rate']:.1f}%")
    print(f"   🔄 Total Interactions: {stats['total_interactions']}")
    print(f"   🎯 Recent Successes: {stats['recent_successes']}")
    print(f"   ⚠️ Recent Failures: {stats['recent_failures']}")
    
    print("\n🏆 TOP PERFORMING PATTERNS:")
    top_patterns = [
        {'name': 'multi_step_checkout', 'success_rate': 91, 'uses': 15},
        {'name': 'card_marketplace_direct', 'success_rate': 85, 'uses': 12},
        {'name': 'modal_price_selection', 'success_rate': 72, 'uses': 8}
    ]
    
    for pattern in top_patterns:
        print(f"   🥇 {pattern['name']}: {pattern['success_rate']}% ({pattern['uses']} uses)")

if __name__ == "__main__":
    demonstrate_learning_system()
    show_example_interaction_log()
    show_learning_statistics()
    
    print("\n🚀 TO ACTIVATE THE LEARNING SYSTEM:")
    print("   1. The system is already integrated into scraper_fast.py")
    print("   2. It will automatically detect transaction patterns")
    print("   3. Learn from each interaction (success or failure)")
    print("   4. Apply learned patterns to similar sites")
    print("   5. Continuously improve success rates over time")
    
    print("\n📁 LEARNING DATA STORAGE:")
    print("   • learned_transaction_patterns.json - Persistent pattern storage")
    print("   • Interaction logs with success/failure tracking")
    print("   • Confidence scores for each learned pattern")
    print("   • Usage statistics and performance metrics") 