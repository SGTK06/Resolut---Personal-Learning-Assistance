"""Quick test script for scroll monitor components."""

import sys
print("=" * 50)
print("Testing Scroll Monitor Components")
print("=" * 50)

# Test 1: Config
print("\n1. Testing config.py...")
try:
    from config import (
        SCROLL_DETECTION_THRESHOLD_MINUTES,
        NEGOTIATION_WAIT_MINUTES,
        SOCIAL_MEDIA_APPS,
        MESSAGES
    )
    print(f"   [OK] Detection threshold: {SCROLL_DETECTION_THRESHOLD_MINUTES} min")
    print(f"   [OK] Negotiation wait: {NEGOTIATION_WAIT_MINUTES} min")
    print(f"   [OK] Social apps configured: {len(SOCIAL_MEDIA_APPS)}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)

# Test 2: ActivityMonitor
print("\n2. Testing activity_monitor.py...")
try:
    from activity_monitor import ActivityMonitor
    m = ActivityMonitor()
    assert hasattr(m, 'on_threshold_exceeded'), "Missing on_threshold_exceeded"
    assert hasattr(m, 'get_continuous_social_duration_minutes'), "Missing get_continuous_social_duration_minutes"
    assert hasattr(m, 'reset_duration'), "Missing reset_duration"
    print("   [OK] ActivityMonitor has all required methods")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)

# Test 3: LockdownEnforcer
print("\n3. Testing lockdown_enforcer.py...")
try:
    from lockdown_enforcer import LockdownEnforcer
    e = LockdownEnforcer()
    assert hasattr(e, 'activate'), "Missing activate"
    assert hasattr(e, 'deactivate'), "Missing deactivate"
    print("   [OK] LockdownEnforcer has all required methods")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)

# Test 4: NegotiationOverlay (requires display, so just import test)
print("\n4. Testing negotiation_overlay.py (import only)...")
try:
    # Just test import, don't create widget (requires display)
    import negotiation_overlay
    assert hasattr(negotiation_overlay, 'NegotiationOverlay'), "Missing NegotiationOverlay class"
    print("   [OK] NegotiationOverlay module imports correctly")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)

# Test 5: ScrollMonitorApp (import only)
print("\n5. Testing scroll_monitor_main.py (import only)...")
try:
    import scroll_monitor_main
    assert hasattr(scroll_monitor_main, 'ScrollMonitorApp'), "Missing ScrollMonitorApp class"
    assert hasattr(scroll_monitor_main, 'main'), "Missing main function"
    print("   [OK] ScrollMonitorApp module imports correctly")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("All tests passed!")
print("=" * 50)
