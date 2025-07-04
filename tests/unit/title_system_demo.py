#!/usr/bin/env python3
"""
Demo: Root Title System for Better Context
==========================================
Shows how the new system provides consistent site context instead of random page titles
"""

# Import the function from scraper_fast (this is just for demo)
import sys
sys.path.append('.')

def demo_root_title_system():
    """Demonstrate the difference between old and new title handling"""
    
    print("🏷️ Root Title System Demo")
    print("=" * 50)
    
    # Simulate old behavior (what we used to get)
    print("\n❌ OLD BEHAVIOR (current page titles):")
    print("   Site: darkmarket123abc.onion")
    print("   Page 1: 'DarkMarket - Home'")
    print("   Page 2: 'Order #123222'")  # ← This is the problem!
    print("   Page 3: 'Payment Confirmation'")
    print("   Page 4: 'Thank You'")
    print("\n   Result: Confusing titles like 'Order #123222' without context")
    
    # Simulate new behavior (root titles)
    print("\n✅ NEW BEHAVIOR (root title system):")
    print("   Site: darkmarket123abc.onion")
    print("   Page 1: 'DarkMarket - Home' → Stored as root title")
    print("   Page 2: 'Order #123222' → Uses 'DarkMarket - Home'")
    print("   Page 3: 'Payment Confirmation' → Uses 'DarkMarket - Home'")
    print("   Page 4: 'Thank You' → Uses 'DarkMarket - Home'")
    print("\n   Result: Consistent 'DarkMarket - Home' context for all pages")
    
    print("\n🎯 BENEFITS:")
    print("   • Better context in logs and CSV files")
    print("   • Easier to identify which site an address came from")
    print("   • More meaningful file names for screenshots")
    print("   • Consistent reporting across all pages of a site")
    
    print("\n📊 EXAMPLE LOG OUTPUT:")
    print("   Before: '📄 [Worker-1] Page title: Order #123222'")
    print("   After:  '📄 [Worker-1] Page title: DarkMarket - Home'")
    
    print("\n💾 EXAMPLE CSV OUTPUT:")
    print("   Before: url,title,chain,address")
    print("           site.onion/order,Order #123222,BTC,1A1zP1eP...")
    print("   After:  site.onion/order,DarkMarket - Home,BTC,1A1zP1eP...")

if __name__ == "__main__":
    demo_root_title_system() 