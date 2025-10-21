#!/usr/bin/env python3
"""
Test script to validate portrait mode touch mapping mathematics.

This script validates that the inverse mapping correctly maps window coordinates
back to portrait coordinates for -90° rotation.
"""

import math

def window_to_portrait(xw, yw, ox, oy, s, Pw):
    """
    Analytically map window coordinates to portrait coordinates for -90° rotation.
    
    Forward mapping: xw = ox + s*v, yw = oy + s*(Pw - u)
    Inverse mapping: u = Pw - (yw - oy)/s, v = (xw - ox)/s
    
    Args:
        xw, yw: Window coordinates
        ox, oy: Letterbox offset
        s: Scale factor
        Pw: Portrait width (1080)
    
    Returns:
        (u, v): Portrait coordinates
    """
    u = Pw - (yw - oy) / s
    v = (xw - ox) / s
    return u, v

def portrait_to_window(u, v, ox, oy, s, Pw):
    """
    Forward mapping: portrait → window coordinates for -90° rotation.
    
    Args:
        u, v: Portrait coordinates
        ox, oy: Letterbox offset
        s: Scale factor
        Pw: Portrait width (1080)
    
    Returns:
        (xw, yw): Window coordinates
    """
    xw = ox + s * v
    yw = oy + s * (Pw - u)
    return xw, yw

def test_round_trip():
    """Test that forward and inverse mappings are inverses of each other"""
    # Test parameters (example from a 1920x1080 window with portrait 1080x1920)
    Pw = 1080
    Ph = 1920
    
    # Window size
    window_w = 1920
    window_h = 1080
    
    # After -90° rotation, rotated size is (Ph, Pw) = (1920, 1080)
    rot_w = Ph  # 1920
    rot_h = Pw  # 1080
    
    # Scale factor
    s = min(window_w / rot_w, window_h / rot_h)
    
    # Letterbox offset
    blit_w = rot_w * s
    blit_h = rot_h * s
    ox = (window_w - blit_w) / 2
    oy = (window_h - blit_h) / 2
    
    print(f"Test parameters:")
    print(f"  Window size: {window_w}x{window_h}")
    print(f"  Portrait size: {Pw}x{Ph}")
    print(f"  Rotated size: {rot_w}x{rot_h}")
    print(f"  Scale factor: {s:.4f}")
    print(f"  Letterbox offset: ({ox:.1f}, {oy:.1f})")
    print(f"  Blit size: {blit_w:.1f}x{blit_h:.1f}")
    print()
    
    # Test portrait corners
    test_cases = [
        (0, 0, "bottom-left"),
        (Pw, 0, "bottom-right"),
        (Pw, Ph, "top-right"),
        (0, Ph, "top-left"),
        (Pw/2, Ph/2, "center"),
    ]
    
    print("Round-trip test (portrait → window → portrait):")
    max_error = 0
    for u, v, label in test_cases:
        # Forward mapping
        xw, yw = portrait_to_window(u, v, ox, oy, s, Pw)
        
        # Inverse mapping
        u2, v2 = window_to_portrait(xw, yw, ox, oy, s, Pw)
        
        # Check error
        error = math.sqrt((u - u2)**2 + (v - v2)**2)
        max_error = max(max_error, error)
        
        status = "✓" if error < 0.001 else "✗"
        print(f"  {status} {label:12s} portrait=({u:7.1f},{v:7.1f}) → "
              f"window=({xw:7.1f},{yw:7.1f}) → "
              f"portrait=({u2:7.1f},{v2:7.1f}) error={error:.6f}")
    
    print(f"\nMaximum round-trip error: {max_error:.6f}")
    print()
    
    # Test window corners
    window_corners = [
        (0, 0, "bottom-left"),
        (window_w, 0, "bottom-right"),
        (window_w, window_h, "top-right"),
        (0, window_h, "top-left"),
    ]
    
    print("Window corners mapped to portrait space:")
    for xw, yw, label in window_corners:
        u, v = window_to_portrait(xw, yw, ox, oy, s, Pw)
        in_bounds = (0 <= u <= Pw and 0 <= v <= Ph)
        status = "✓" if in_bounds else "✗"
        print(f"  {status} {label:12s} window=({xw:7.1f},{yw:7.1f}) → "
              f"portrait=({u:7.1f},{v:7.1f}) in_bounds={in_bounds}")
    
    print()
    
    # Test specific coordinates from the problem statement
    print("Test coordinates from problem statement (should show corrected values):")
    # These were showing negative x in the bug report
    test_coords = [
        (1131, 741),
        (1133, 550),
        (1132, 643),
        (300, 1054),
    ]
    
    for xw, yw in test_coords:
        u, v = window_to_portrait(xw, yw, ox, oy, s, Pw)
        in_bounds = (0 <= u <= Pw and 0 <= v <= Ph)
        status = "✓" if in_bounds else "✗"
        print(f"  {status} window=({xw},{yw}) → portrait=({u:.1f},{v:.1f}) in_bounds={in_bounds}")
    
    print()
    
    return max_error < 0.001

if __name__ == "__main__":
    success = test_round_trip()
    if success:
        print("✓ All tests passed!")
        exit(0)
    else:
        print("✗ Some tests failed!")
        exit(1)
