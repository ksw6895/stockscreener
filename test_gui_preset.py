#!/usr/bin/env python3
"""Test script for GUI preset functionality"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import GUIApp

def test_preset_application():
    """Test that presets are applied correctly"""
    root = tk.Tk()
    app = GUIApp(root)
    
    # Test each preset
    presets = ["quality", "growth", "value", "balanced"]
    
    for preset_name in presets:
        print(f"\nTesting {preset_name} preset...")
        
        # Apply preset
        app._apply_preset(preset_name)
        
        # Check values
        print(f"  Market Cap Min: {app.config_vars['market_cap_min'].get()}")
        print(f"  Market Cap Max: {app.config_vars['market_cap_max'].get()}")
        print(f"  ROE Avg Min: {app.config_vars['roe_avg_min'].get()}")
        print(f"  ROE Min Each Year: {app.config_vars['roe_min_each_year'].get()}")
        
        # Check weights
        growth_weight = app.config_vars['growth_quality_weight'].get()
        risk_weight = app.config_vars['risk_quality_weight'].get()
        valuation_weight = app.config_vars['valuation_weight'].get()
        sentiment_weight = app.config_vars['sentiment_weight'].get()
        
        total_weight = growth_weight + risk_weight + valuation_weight + sentiment_weight
        
        print(f"  Growth Weight: {growth_weight}")
        print(f"  Risk Weight: {risk_weight}")
        print(f"  Valuation Weight: {valuation_weight}")
        print(f"  Sentiment Weight: {sentiment_weight}")
        print(f"  Total Weight: {total_weight}")
        
        if abs(total_weight - 1.0) > 0.001:
            print(f"  WARNING: Weights don't sum to 1.0!")
    
    # Test cache clear button
    print("\nTesting cache clear functionality...")
    try:
        app._clear_cache()
        print("  Cache clear successful")
    except Exception as e:
        print(f"  Cache clear failed: {e}")
    
    root.destroy()
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_preset_application()