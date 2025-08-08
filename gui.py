import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox, StringVar, BooleanVar, IntVar, DoubleVar, filedialog
from tkinter.scrolledtext import ScrolledText
import threading
import asyncio
import queue
import subprocess
import json
from pathlib import Path

from config import config_manager
from src.gui_helpers import ValidatedEntry, PercentageEntry, WeightEntry, add_tooltip, create_labeled_entry


class GUIApp:
    """
    Graphical user interface for the stock screening application
    """
    
    def __init__(self, root):
        """
        Initialize the GUI
        
        Args:
            root: The root Tk window
        """
        self.root = root
        self.root.title("Enhanced NASDAQ Stock Screener")
        self.root.geometry("1200x800")
        
        # Create variables to store configuration values
        self.config_vars = {}
        
        # Set up queue for log messages from worker threads
        self.log_queue = queue.Queue()
        
        # Set up the notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.filters_tab = ttk.Frame(self.notebook)
        self.growth_tab = ttk.Frame(self.notebook)
        self.risk_tab = ttk.Frame(self.notebook)
        self.valuation_tab = ttk.Frame(self.notebook)
        self.output_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.backtest_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.filters_tab, text="Initial Filters")
        self.notebook.add(self.growth_tab, text="Growth Settings")
        self.notebook.add(self.risk_tab, text="Risk Settings")
        self.notebook.add(self.valuation_tab, text="Valuation Settings")
        self.notebook.add(self.output_tab, text="Output Settings")
        self.notebook.add(self.log_tab, text="Log")
        self.notebook.add(self.backtest_tab, text="Backtesting")
        
        # Initialize the tabs
        self._init_filters_tab()
        self._init_growth_tab()
        self._init_risk_tab()
        self._init_valuation_tab()
        self._init_output_tab()
        self._init_log_tab()
        self._init_backtest_tab()
        
        # Create control frame at the bottom
        self.control_frame = ttk.Frame(root)
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create buttons
        ttk.Button(self.control_frame, text="Start Screening", command=self._start_screening).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.control_frame, text="Clear Cache", command=self._clear_cache).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.control_frame, text="Save Settings", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.control_frame, text="Load Settings", command=self._load_settings).pack(side=tk.RIGHT, padx=5)
        
        # Add custom profile buttons
        ttk.Button(self.control_frame, text="Save Profile", command=self._save_custom_profile).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.control_frame, text="Load Profile", command=self._load_custom_profile).pack(side=tk.RIGHT, padx=5)
        
        # Add preset buttons
        ttk.Label(self.control_frame, text="Presets:").pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Quality", command=lambda: self._apply_preset("quality")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.control_frame, text="Growth", command=lambda: self._apply_preset("growth")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.control_frame, text="Value", command=lambda: self._apply_preset("value")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.control_frame, text="Balanced", command=lambda: self._apply_preset("balanced")).pack(side=tk.LEFT, padx=2)
        
        # Load initial values from config
        self._load_config_values()
        
        # Set up queue for log messages from worker threads
        self.root.after(100, self._check_log_queue)
    
    def _init_filters_tab(self):
        """Initialize the initial filters tab with validation and tooltips"""
        frame = ttk.LabelFrame(self.filters_tab, text="Market Cap and Sector Filters")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Market cap filters with validation
        self.config_vars['market_cap_min'] = DoubleVar()
        create_labeled_entry(frame, "Market Cap Min ($M):", self.config_vars['market_cap_min'],
                           row=0, tooltip="Minimum market capitalization in millions (e.g., 1000 for $1B)",
                           min_val=0, max_val=1000000)
        
        self.config_vars['market_cap_max'] = DoubleVar()
        create_labeled_entry(frame, "Market Cap Max ($M):", self.config_vars['market_cap_max'],
                           row=1, tooltip="Maximum market capitalization in millions (leave 0 for no limit)",
                           min_val=0, max_val=10000000)
        
        # Sector exclusion with tooltip
        self.config_vars['exclude_financial_sector'] = BooleanVar()
        cb = ttk.Checkbutton(frame, text="Exclude Financial Sector", 
                           variable=self.config_vars['exclude_financial_sector'])
        cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        add_tooltip(cb, "Exclude financial sector stocks from analysis (banks, insurance, etc.)")
        
        # ROE criteria with validation
        roe_frame = ttk.LabelFrame(self.filters_tab, text="ROE Criteria")
        roe_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.config_vars['roe_avg_min'] = DoubleVar()
        create_labeled_entry(roe_frame, "Min Average ROE (%):", self.config_vars['roe_avg_min'],
                           row=0, entry_type="percentage",
                           tooltip="Minimum average Return on Equity over specified years (10-30% typical)")
        
        self.config_vars['roe_min_each_year'] = DoubleVar()
        create_labeled_entry(roe_frame, "Min ROE Each Year (%):", self.config_vars['roe_min_each_year'],
                           row=1, entry_type="percentage",
                           tooltip="Minimum ROE required for each individual year (consistency check)")
        
        self.config_vars['roe_years'] = IntVar()
        create_labeled_entry(roe_frame, "Number of Years:", self.config_vars['roe_years'],
                           row=2, dtype=int, min_val=1, max_val=10,
                           tooltip="Number of years to analyze for ROE consistency (typically 3-5 years)")
    
    def _init_growth_tab(self):
        """Initialize the growth settings tab with validation"""
        frame = ttk.LabelFrame(self.growth_tab, text="Growth Rate Targets")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.config_vars['revenue_growth_min_cagr'] = DoubleVar()
        create_labeled_entry(frame, "Min Revenue CAGR (%):", self.config_vars['revenue_growth_min_cagr'],
                           row=0, entry_type="percentage",
                           tooltip="Minimum revenue compound annual growth rate (5-20% typical for quality companies)")
        
        ttk.Label(frame, text="Min EPS CAGR (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['eps_growth_min_cagr'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['eps_growth_min_cagr']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Min FCF CAGR (%):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['fcf_growth_min_cagr'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['fcf_growth_min_cagr']).grid(row=2, column=1, padx=5, pady=5)
        
        # Growth quality weights
        weight_frame = ttk.LabelFrame(self.growth_tab, text="Growth Quality Weights")
        weight_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(weight_frame, text="Magnitude Weight:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['growth_magnitude_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['growth_magnitude_weight']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Consistency Weight:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['growth_consistency_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['growth_consistency_weight']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Sustainability Weight:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['growth_sustainability_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['growth_sustainability_weight']).grid(row=2, column=1, padx=5, pady=5)
    
    def _init_risk_tab(self):
        """Initialize the risk settings tab"""
        frame = ttk.LabelFrame(self.risk_tab, text="Risk Thresholds")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Max Debt-to-Equity:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['debt_to_equity_max'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['debt_to_equity_max']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Min Interest Coverage:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['interest_coverage_min'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['interest_coverage_min']).grid(row=1, column=1, padx=5, pady=5)
        
        # Risk component weights
        weight_frame = ttk.LabelFrame(self.risk_tab, text="Risk Component Weights")
        weight_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(weight_frame, text="Debt Metrics Weight:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['debt_metrics_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['debt_metrics_weight']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Working Capital Weight:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['working_capital_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['working_capital_weight']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Margin Stability Weight:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['margin_stability_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['margin_stability_weight']).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Cash Flow Quality Weight:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['cash_flow_quality_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['cash_flow_quality_weight']).grid(row=3, column=1, padx=5, pady=5)
    
    def _init_valuation_tab(self):
        """Initialize the valuation settings tab"""
        frame = ttk.LabelFrame(self.valuation_tab, text="Valuation Thresholds")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Max P/E Ratio:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['per_max'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['per_max']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Max P/B Ratio:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['pbr_max'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['pbr_max']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Min FCF Yield (%):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['fcf_yield_min'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['fcf_yield_min']).grid(row=2, column=1, padx=5, pady=5)
        
        # Valuation component weights
        weight_frame = ttk.LabelFrame(self.valuation_tab, text="Valuation Component Weights")
        weight_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(weight_frame, text="P/E Ratio Weight:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['per_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['per_weight']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="P/B Ratio Weight:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['pbr_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['pbr_weight']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="FCF Yield Weight:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['fcf_yield_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['fcf_yield_weight']).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Growth-Adjusted Weight:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['growth_adjusted_weight'] = DoubleVar()
        ttk.Entry(weight_frame, textvariable=self.config_vars['growth_adjusted_weight']).grid(row=3, column=1, padx=5, pady=5)
    
    def _init_output_tab(self):
        """Initialize the output settings tab"""
        frame = ttk.LabelFrame(self.output_tab, text="Output Settings")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Output Filename Prefix:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['filename_prefix'] = StringVar()
        ttk.Entry(frame, textvariable=self.config_vars['filename_prefix']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Minimum Quality Score (0-1):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['min_quality_score'] = DoubleVar()
        ttk.Entry(frame, textvariable=self.config_vars['min_quality_score']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Maximum Stocks to Report:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['max_stocks'] = IntVar()
        ttk.Entry(frame, textvariable=self.config_vars['max_stocks']).grid(row=2, column=1, padx=5, pady=5)
        
        # Format options
        ttk.Label(frame, text="Output Formats:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.config_vars['output_text'] = BooleanVar()
        ttk.Checkbutton(frame, text="Text Report", 
                       variable=self.config_vars['output_text']).grid(
                       row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.config_vars['output_excel'] = BooleanVar()
        ttk.Checkbutton(frame, text="Excel Report", 
                       variable=self.config_vars['output_excel']).grid(
                       row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Global scoring weights
        weight_frame = ttk.LabelFrame(self.output_tab, text="Global Scoring Weights")
        weight_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(weight_frame, text="Growth Quality Weight:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['growth_quality_weight'] = DoubleVar()
        self.config_vars['growth_quality_weight'].trace_add('write', lambda *args: self._update_weight_sum())
        ttk.Entry(weight_frame, textvariable=self.config_vars['growth_quality_weight']).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Risk Quality Weight:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['risk_quality_weight'] = DoubleVar()
        self.config_vars['risk_quality_weight'].trace_add('write', lambda *args: self._update_weight_sum())
        ttk.Entry(weight_frame, textvariable=self.config_vars['risk_quality_weight']).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Valuation Weight:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['valuation_weight'] = DoubleVar()
        self.config_vars['valuation_weight'].trace_add('write', lambda *args: self._update_weight_sum())
        ttk.Entry(weight_frame, textvariable=self.config_vars['valuation_weight']).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(weight_frame, text="Sentiment Weight:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sentiment_weight'] = DoubleVar()
        self.config_vars['sentiment_weight'].trace_add('write', lambda *args: self._update_weight_sum())
        ttk.Entry(weight_frame, textvariable=self.config_vars['sentiment_weight']).grid(row=3, column=1, padx=5, pady=5)
        
        # Weight sum display and normalize button
        ttk.Label(weight_frame, text="Current Sum:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.weight_sum_label = ttk.Label(weight_frame, text="0.00", font=('TkDefaultFont', 10, 'bold'))
        self.weight_sum_label.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(weight_frame, text="Normalize Weights", command=self._normalize_weights).grid(
            row=5, column=0, columnspan=2, padx=5, pady=10)
    
    def _init_log_tab(self):
        """Initialize the log tab"""
        # Create a scrolled text widget for logs
        self.log_text = ScrolledText(self.log_tab, height=30)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Create custom log handler that puts log messages into the queue
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
                
            def emit(self, record):
                self.log_queue.put(self.format(record))
        
        # Configure the root logger to use our queue handler
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
    
    def _check_log_queue(self):
        """Check for new log messages and add them to the log text widget"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + '\n')
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
                self.log_queue.task_done()
        except queue.Empty:
            pass
        
        # Schedule to check again
        self.root.after(100, self._check_log_queue)
    
    def _load_config_values(self):
        """Load values from config into the GUI"""
        # Initial filters
        initial_filters = config_manager.get_initial_filters()
        self.config_vars['market_cap_min'].set(initial_filters.get('market_cap_min', 100000000) / 1_000_000)
        self.config_vars['market_cap_max'].set(initial_filters.get('market_cap_max', 5000000000) / 1_000_000)
        self.config_vars['exclude_financial_sector'].set(initial_filters.get('exclude_financial_sector', False))
        
        # ROE criteria
        roe = initial_filters.get('roe', {})
        self.config_vars['roe_avg_min'].set(roe.get('min_avg', 0.15) * 100)
        self.config_vars['roe_min_each_year'].set(roe.get('min_each_year', 0.10) * 100)
        self.config_vars['roe_years'].set(roe.get('years', 3))
        
        # Growth quality
        growth_quality = config_manager.get_growth_quality_settings()
        
        # Growth targets
        revenue_growth = growth_quality.get('revenue_growth', {})
        eps_growth = growth_quality.get('eps_growth', {})
        fcf_growth = growth_quality.get('fcf_growth', {})
        
        self.config_vars['revenue_growth_min_cagr'].set(revenue_growth.get('min_cagr', 0.20) * 100)
        self.config_vars['eps_growth_min_cagr'].set(eps_growth.get('min_cagr', 0.15) * 100)
        self.config_vars['fcf_growth_min_cagr'].set(fcf_growth.get('min_cagr', 0.10) * 100)
        
        # Growth weights
        self.config_vars['growth_magnitude_weight'].set(revenue_growth.get('magnitude_weight', 0.35))
        self.config_vars['growth_consistency_weight'].set(revenue_growth.get('consistency_weight', 0.35))
        self.config_vars['growth_sustainability_weight'].set(revenue_growth.get('sustainability_weight', 0.30))
        
        # Risk quality
        risk_quality = config_manager.config.get('risk_quality', {})
        
        self.config_vars['debt_to_equity_max'].set(risk_quality.get('debt_to_equity_max', 2.0))
        self.config_vars['interest_coverage_min'].set(risk_quality.get('interest_coverage_min', 3.0))
        
        # Risk weights
        risk_weights = risk_quality.get('weights', {})
        self.config_vars['debt_metrics_weight'].set(risk_weights.get('debt_metrics', 0.30))
        self.config_vars['working_capital_weight'].set(risk_weights.get('working_capital', 0.25))
        self.config_vars['margin_stability_weight'].set(risk_weights.get('margin_stability', 0.25))
        self.config_vars['cash_flow_quality_weight'].set(risk_weights.get('cash_flow_quality', 0.20))
        
        # Valuation
        valuation = config_manager.config.get('valuation', {})
        
        self.config_vars['per_max'].set(valuation.get('per_max', 30.0))
        self.config_vars['pbr_max'].set(valuation.get('pbr_max', 5.0))
        self.config_vars['fcf_yield_min'].set(valuation.get('fcf_yield_min', 3.0))
        
        # Valuation weights
        valuation_weights = valuation.get('weights', {})
        self.config_vars['per_weight'].set(valuation_weights.get('per', 0.30))
        self.config_vars['pbr_weight'].set(valuation_weights.get('pbr', 0.20))
        self.config_vars['fcf_yield_weight'].set(valuation_weights.get('fcf_yield', 0.30))
        self.config_vars['growth_adjusted_weight'].set(valuation_weights.get('growth_adjusted', 0.20))
        
        # Output settings
        output_settings = config_manager.get_output_settings()
        
        self.config_vars['filename_prefix'].set(output_settings.get('filename_prefix', 'nasdaq_growth_stocks'))
        self.config_vars['min_quality_score'].set(output_settings.get('min_quality_score', 0.70))
        self.config_vars['max_stocks'].set(output_settings.get('max_stocks', 50))
        
        self.config_vars['output_text'].set(output_settings.get('format', 'text') == 'text')
        self.config_vars['output_excel'].set(output_settings.get('format', 'text') == 'excel')
        
        # Global scoring weights
        scoring_weights = config_manager.get_scoring_weights()
        
        self.config_vars['growth_quality_weight'].set(scoring_weights.get('growth_quality', 0.40))
        self.config_vars['risk_quality_weight'].set(scoring_weights.get('risk_quality', 0.25))
        self.config_vars['valuation_weight'].set(scoring_weights.get('valuation', 0.20))
        self.config_vars['sentiment_weight'].set(scoring_weights.get('sentiment', 0.15))
    
    def _save_settings(self):
        """Save settings from the GUI to the config"""
        try:
            # Prepare updated config
            new_config = {
                'initial_filters': {
                    'market_cap_min': int(self.config_vars['market_cap_min'].get() * 1_000_000),
                    'market_cap_max': int(self.config_vars['market_cap_max'].get() * 1_000_000),
                    'exclude_financial_sector': self.config_vars['exclude_financial_sector'].get(),
                    'roe': {
                        'min_avg': self.config_vars['roe_avg_min'].get() / 100,
                        'min_each_year': self.config_vars['roe_min_each_year'].get() / 100,
                        'years': self.config_vars['roe_years'].get()
                    }
                },
                'growth_quality': {
                    'revenue_growth': {
                        'min_cagr': self.config_vars['revenue_growth_min_cagr'].get() / 100,
                        'magnitude_weight': self.config_vars['growth_magnitude_weight'].get(),
                        'consistency_weight': self.config_vars['growth_consistency_weight'].get(),
                        'sustainability_weight': self.config_vars['growth_sustainability_weight'].get()
                    },
                    'eps_growth': {
                        'min_cagr': self.config_vars['eps_growth_min_cagr'].get() / 100
                    },
                    'fcf_growth': {
                        'min_cagr': self.config_vars['fcf_growth_min_cagr'].get() / 100
                    }
                },
                'risk_quality': {
                    'debt_to_equity_max': self.config_vars['debt_to_equity_max'].get(),
                    'interest_coverage_min': self.config_vars['interest_coverage_min'].get(),
                    'weights': {
                        'debt_metrics': self.config_vars['debt_metrics_weight'].get(),
                        'working_capital': self.config_vars['working_capital_weight'].get(),
                        'margin_stability': self.config_vars['margin_stability_weight'].get(),
                        'cash_flow_quality': self.config_vars['cash_flow_quality_weight'].get()
                    }
                },
                'valuation': {
                    'per_max': self.config_vars['per_max'].get(),
                    'pbr_max': self.config_vars['pbr_max'].get(),
                    'fcf_yield_min': self.config_vars['fcf_yield_min'].get() / 100,
                    'weights': {
                        'per': self.config_vars['per_weight'].get(),
                        'pbr': self.config_vars['pbr_weight'].get(),
                        'fcf_yield': self.config_vars['fcf_yield_weight'].get(),
                        'growth_adjusted': self.config_vars['growth_adjusted_weight'].get()
                    }
                },
                'output': {
                    'filename_prefix': self.config_vars['filename_prefix'].get(),
                    'min_quality_score': self.config_vars['min_quality_score'].get(),
                    'max_stocks': self.config_vars['max_stocks'].get(),
                    'format': 'text' if self.config_vars['output_text'].get() else 'excel'
                },
                'scoring': {
                    'weights': {
                        'growth_quality': self.config_vars['growth_quality_weight'].get(),
                        'risk_quality': self.config_vars['risk_quality_weight'].get(),
                        'valuation': self.config_vars['valuation_weight'].get(),
                        'sentiment': self.config_vars['sentiment_weight'].get()
                    }
                },
                'target_rates': {
                    'revenue': self.config_vars['revenue_growth_min_cagr'].get() / 100,
                    'eps': self.config_vars['eps_growth_min_cagr'].get() / 100,
                    'fcf': self.config_vars['fcf_growth_min_cagr'].get() / 100
                }
            }
            
            # Update config
            config_manager.update_config(new_config)
            
            # Save to file
            config_manager.save_config()
            
            messagebox.showinfo("Success", "Settings saved successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def _load_settings(self):
        """Reload settings from the config file"""
        try:
            # Reload config
            config_manager.config = config_manager.load_config(config_manager.config_file)
            
            # Update GUI
            self._load_config_values()
            
            messagebox.showinfo("Success", "Settings loaded successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
    
    def _update_weight_sum(self):
        """Update the weight sum display"""
        try:
            growth_weight = self.config_vars['growth_quality_weight'].get() or 0
            risk_weight = self.config_vars['risk_quality_weight'].get() or 0
            valuation_weight = self.config_vars['valuation_weight'].get() or 0
            sentiment_weight = self.config_vars['sentiment_weight'].get() or 0
            
            total = growth_weight + risk_weight + valuation_weight + sentiment_weight
            
            # Update label with color coding
            self.weight_sum_label.config(text=f"{total:.2f}")
            if abs(total - 1.0) < 0.001:
                self.weight_sum_label.config(foreground="green")
            else:
                self.weight_sum_label.config(foreground="red")
        except:
            pass  # Ignore errors during initialization
    
    def _normalize_weights(self):
        """Normalize weights to sum to 1.0"""
        try:
            growth_weight = self.config_vars['growth_quality_weight'].get() or 0
            risk_weight = self.config_vars['risk_quality_weight'].get() or 0
            valuation_weight = self.config_vars['valuation_weight'].get() or 0
            sentiment_weight = self.config_vars['sentiment_weight'].get() or 0
            
            total = growth_weight + risk_weight + valuation_weight + sentiment_weight
            
            if total > 0:
                self.config_vars['growth_quality_weight'].set(round(growth_weight / total, 3))
                self.config_vars['risk_quality_weight'].set(round(risk_weight / total, 3))
                self.config_vars['valuation_weight'].set(round(valuation_weight / total, 3))
                self.config_vars['sentiment_weight'].set(round(sentiment_weight / total, 3))
                
                messagebox.showinfo("Weights Normalized", "Weights have been normalized to sum to 1.0")
            else:
                messagebox.showwarning("Invalid Weights", "Cannot normalize weights when sum is zero")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to normalize weights: {str(e)}")
    
    def _apply_preset(self, preset_name):
        """Apply a preset configuration"""
        presets = {
            "quality": {
                "market_cap_min": 1000.0,
                "market_cap_max": 50000.0,
                "roe_avg_min": 15.0,
                "roe_min_each_year": 10.0,
                "revenue_growth_min_cagr": 10.0,
                "eps_growth_min_cagr": 10.0,
                "fcf_growth_min_cagr": 8.0,
                "growth_quality_weight": 0.4,  # Fixed key name
                "risk_quality_weight": 0.3,    # Fixed key name
                "valuation_weight": 0.2,
                "sentiment_weight": 0.1
            },
            "growth": {
                "market_cap_min": 500.0,
                "market_cap_max": 20000.0,
                "roe_avg_min": 10.0,
                "roe_min_each_year": 5.0,
                "revenue_growth_min_cagr": 20.0,
                "eps_growth_min_cagr": 15.0,
                "fcf_growth_min_cagr": 12.0,
                "growth_quality_weight": 0.6,  # Fixed key name
                "risk_quality_weight": 0.2,    # Fixed key name
                "valuation_weight": 0.1,
                "sentiment_weight": 0.1
            },
            "value": {
                "market_cap_min": 2000.0,
                "market_cap_max": 100000.0,
                "roe_avg_min": 10.0,
                "roe_min_each_year": 8.0,
                "revenue_growth_min_cagr": 5.0,
                "eps_growth_min_cagr": 5.0,
                "fcf_growth_min_cagr": 5.0,
                "growth_quality_weight": 0.2,  # Fixed key name
                "risk_quality_weight": 0.3,    # Fixed key name
                "valuation_weight": 0.4,
                "sentiment_weight": 0.1
            },
            "balanced": {
                "market_cap_min": 1000.0,
                "market_cap_max": 50000.0,
                "roe_avg_min": 12.0,
                "roe_min_each_year": 8.0,
                "revenue_growth_min_cagr": 10.0,
                "eps_growth_min_cagr": 10.0,
                "fcf_growth_min_cagr": 8.0,
                "growth_quality_weight": 0.25,  # Fixed key name
                "risk_quality_weight": 0.25,    # Fixed key name
                "valuation_weight": 0.25,
                "sentiment_weight": 0.25
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            
            # Apply all preset values
            for key, value in preset.items():
                if key in self.config_vars:
                    self.config_vars[key].set(value)
                else:
                    # Log warning for debugging
                    logging.debug(f"Key '{key}' not found in config_vars")
            
            # Update weight sum display if it exists
            if hasattr(self, '_update_weight_sum'):
                self._update_weight_sum()
            
            messagebox.showinfo("Preset Applied", f"{preset_name.capitalize()} preset applied with normalized weights.")
        else:
            messagebox.showerror("Error", f"Unknown preset: {preset_name}")
    
    def _clear_cache(self):
        """Clear the cache"""
        try:
            from src.cache import cache_manager
            cache_manager.clear()
            
            # Log the action
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "Cache cleared successfully.\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            
            messagebox.showinfo("Cache Cleared", "Cache has been cleared successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear cache: {str(e)}")
            logging.error(f"Failed to clear cache: {str(e)}")
    
    def _start_screening(self):
        """Start the screening process"""
        try:
            # First save current settings
            self._save_settings()
            
            # Show a message that screening is starting
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "Starting stock screening process...\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            
            # Switch to log tab
            self.notebook.select(self.log_tab)
            
            # Disable buttons during processing
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.DISABLED)
            
            # Start screening in a separate thread
            threading.Thread(target=self._run_screening, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start screening: {str(e)}")
            
            # Re-enable buttons
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.NORMAL)
    
    def _run_screening(self):
        """Run the screening process in a separate thread"""
        try:
            # Import here to avoid circular imports
            from stock_screener import run_screener
            
            # Run the screener
            run_screener()
            
            # Re-enable buttons
            self.root.after(0, self._enable_buttons)
            
        except Exception as e:
            logging.error(f"Error in screening process: {str(e)}")
            
            # Re-enable buttons
            self.root.after(0, self._enable_buttons)
    
    def _enable_buttons(self):
        """Re-enable buttons after processing is complete"""
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.NORMAL)

    def _init_backtest_tab(self):
        """Initialize the backtesting tab"""
        # Info label
        info_label = ttk.Label(self.backtest_tab, 
                             text="Backtest uses your current screening settings (filters, weights, etc.)",
                             font=('TkDefaultFont', 9, 'italic'))
        info_label.pack(padx=10, pady=5)
        
        # Create main frame
        frame = ttk.LabelFrame(self.backtest_tab, text="Backtesting Configuration")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lookback period selection
        ttk.Label(frame, text="Lookback Period:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.backtest_period = StringVar(value="6m")
        period_combo = ttk.Combobox(frame, textvariable=self.backtest_period, 
                                  values=["3m", "6m", "1y"], state="readonly")
        period_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Initial investment amount
        ttk.Label(frame, text="Initial Investment ($):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.initial_investment = DoubleVar(value=100000.0)
        ttk.Entry(frame, textvariable=self.initial_investment).grid(row=1, column=1, padx=5, pady=5)
        
        # Results display
        results_frame = ttk.LabelFrame(self.backtest_tab, text="Backtest Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text area to display summary results
        self.backtest_results_text = ScrolledText(results_frame, height=10)
        self.backtest_results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.backtest_results_text.config(state=tk.DISABLED)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.backtest_tab)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Run backtest button
        self.run_backtest_button = ttk.Button(buttons_frame, text="Run Backtest", command=self._run_backtest)
        self.run_backtest_button.pack(side=tk.RIGHT, padx=5)
        
        # View graphs button (initially disabled)
        self.view_graphs_button = ttk.Button(buttons_frame, text="View Graphs", command=self._view_backtest_graphs, state=tk.DISABLED)
        self.view_graphs_button.pack(side=tk.RIGHT, padx=5)
        
        # Store backtest results
        self.backtest_result_paths = {}

    def _run_backtest(self):
        """Run a backtest with the current settings"""
        try:
            # First save current settings to ensure backtest uses them
            self._save_settings()
            
            # Disable buttons during processing
            self.run_backtest_button.config(state=tk.DISABLED)
            self.view_graphs_button.config(state=tk.DISABLED)
            
            # Clear previous results
            self.backtest_results_text.config(state=tk.NORMAL)
            self.backtest_results_text.delete(1.0, tk.END)
            self.backtest_results_text.insert(tk.END, "Running backtest with current screening settings...\n")
            self.backtest_results_text.insert(tk.END, f"  Growth weight: {self.config_vars['growth_quality_weight'].get():.2f}\n")
            self.backtest_results_text.insert(tk.END, f"  Risk weight: {self.config_vars['risk_quality_weight'].get():.2f}\n")
            self.backtest_results_text.insert(tk.END, f"  Valuation weight: {self.config_vars['valuation_weight'].get():.2f}\n")
            self.backtest_results_text.insert(tk.END, f"  Sentiment weight: {self.config_vars['sentiment_weight'].get():.2f}\n\n")
            self.backtest_results_text.config(state=tk.DISABLED)
            
            # Get parameters
            period = self.backtest_period.get()
            investment = self.initial_investment.get()
            
            # Start backtest in a separate thread
            threading.Thread(
                target=self._execute_backtest,
                args=(period, investment),
                daemon=True
            ).start()
            
        except Exception as e:
            self.backtest_results_text.config(state=tk.NORMAL)
            self.backtest_results_text.insert(tk.END, f"Error: {str(e)}\n")
            self.backtest_results_text.config(state=tk.DISABLED)
            
            # Re-enable run button
            self.run_backtest_button.config(state=tk.NORMAL)

    def _execute_backtest(self, period, investment):
        """Execute the backtest in a separate thread"""
        try:
            # Import here to avoid circular imports
            from backtest import run_complete_backtest
            
            # Run the backtest
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_complete_backtest(period, investment))
            
            # Store the result paths
            self.backtest_result_paths = result
            
            # Display the summary
            if "error" in result:
                self._update_backtest_results(f"Error: {result['error']}")
            else:
                # Try to read and display the summary report
                try:
                    with open(result['summary_report'], 'r') as f:
                        summary_text = f.read()
                    self._update_backtest_results(summary_text)
                except Exception as e:
                    self._update_backtest_results(f"Backtest completed, but could not read summary: {str(e)}")
                
                # Enable the view graphs button
                self.root.after(0, lambda: self.view_graphs_button.config(state=tk.NORMAL))
            
        except Exception as e:
            self._update_backtest_results(f"Error executing backtest: {str(e)}")
        finally:
            # Re-enable the run button
            self.root.after(0, lambda: self.run_backtest_button.config(state=tk.NORMAL))
            
    def _update_backtest_results(self, text):
        """Update the backtest results text widget"""
        def _update():
            self.backtest_results_text.config(state=tk.NORMAL)
            self.backtest_results_text.delete(1.0, tk.END)
            self.backtest_results_text.insert(tk.END, text)
            self.backtest_results_text.config(state=tk.DISABLED)
        
        # Schedule the update to run on the main thread
        self.root.after(0, _update)

    def _view_backtest_graphs(self):
        """Open backtest graphs in the default image viewer"""
        try:
            if not self.backtest_result_paths:
                messagebox.showinfo("No Graphs", "No backtest graphs available.")
                return
                
            # Open graphs with default system application
            if 'individual_graph' in self.backtest_result_paths:
                os.startfile(self.backtest_result_paths['individual_graph']) if sys.platform == 'win32' else \
                subprocess.call(['open', self.backtest_result_paths['individual_graph']]) if sys.platform == 'darwin' else \
                subprocess.call(['xdg-open', self.backtest_result_paths['individual_graph']])
                
            if 'portfolio_graph' in self.backtest_result_paths:
                os.startfile(self.backtest_result_paths['portfolio_graph']) if sys.platform == 'win32' else \
                subprocess.call(['open', self.backtest_result_paths['portfolio_graph']]) if sys.platform == 'darwin' else \
                subprocess.call(['xdg-open', self.backtest_result_paths['portfolio_graph']])
                
            if 'wealth_graph' in self.backtest_result_paths:
                os.startfile(self.backtest_result_paths['wealth_graph']) if sys.platform == 'win32' else \
                subprocess.call(['open', self.backtest_result_paths['wealth_graph']]) if sys.platform == 'darwin' else \
                subprocess.call(['xdg-open', self.backtest_result_paths['wealth_graph']])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open graphs: {str(e)}")
    
    def _save_custom_profile(self):
        """Save current settings as a custom profile"""
        try:
            # Ask user for profile location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Custom Profile"
            )
            
            if not file_path:
                return
            
            # Prepare profile data
            profile_data = {
                "name": Path(file_path).stem,
                "description": "Custom profile saved from GUI",
                "weights": {
                    "growth": self.config_vars['growth_quality_weight'].get(),
                    "risk": self.config_vars['risk_quality_weight'].get(),
                    "valuation": self.config_vars['valuation_weight'].get(),
                    "sentiment": self.config_vars['sentiment_weight'].get()
                },
                "screening": {
                    "min_roe": self.config_vars['roe_avg_min'].get() / 100,
                    "min_roa": self.config_vars.get('roa_min', DoubleVar(value=5)).get() / 100 if 'roa_min' in self.config_vars else 0.05,
                    "min_gross_margin": self.config_vars.get('gross_margin_min', DoubleVar(value=20)).get() / 100 if 'gross_margin_min' in self.config_vars else 0.2,
                    "min_operating_margin": self.config_vars.get('operating_margin_min', DoubleVar(value=10)).get() / 100 if 'operating_margin_min' in self.config_vars else 0.1,
                    "market_cap": {
                        "min_market_cap": self.config_vars['market_cap_min'].get() if self.config_vars['market_cap_min'].get() > 0 else None,
                        "max_market_cap": self.config_vars['market_cap_max'].get() if self.config_vars['market_cap_max'].get() > 0 else None
                    },
                    "growth": {
                        "min_revenue_growth": self.config_vars['revenue_growth_min_cagr'].get() / 100,
                        "min_earnings_growth": self.config_vars['eps_growth_min_cagr'].get() / 100,
                        "min_eps_growth": self.config_vars['eps_growth_min_cagr'].get() / 100
                    },
                    "risk": {
                        "max_debt_to_equity": self.config_vars['debt_to_equity_max'].get(),
                        "min_current_ratio": self.config_vars.get('current_ratio_min', DoubleVar(value=1.0)).get() if 'current_ratio_min' in self.config_vars else 1.0,
                        "min_interest_coverage": self.config_vars['interest_coverage_min'].get()
                    },
                    "valuation": {
                        "max_pe_ratio": self.config_vars['per_max'].get(),
                        "max_pb_ratio": self.config_vars['pbr_max'].get(),
                        "max_peg_ratio": self.config_vars.get('peg_max', DoubleVar(value=2.0)).get() if 'peg_max' in self.config_vars else 2.0
                    }
                },
                "output": {
                    "formats": ["excel", "text"] if self.config_vars.get('output_excel', BooleanVar(value=True)).get() else ["text"],
                    "excel_filename": f"{self.config_vars['filename_prefix'].get()}_analysis.xlsx",
                    "text_filename": f"{self.config_vars['filename_prefix'].get()}_analysis.txt",
                    "include_charts": True
                }
            }
            
            # Save profile to file
            with open(file_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Profile saved successfully to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {str(e)}")
    
    def _load_custom_profile(self):
        """Load settings from a custom profile"""
        try:
            # Ask user for profile location
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Custom Profile"
            )
            
            if not file_path:
                return
            
            # Load profile data
            with open(file_path, 'r') as f:
                profile_data = json.load(f)
            
            # Apply weights if present
            if 'weights' in profile_data:
                weights = profile_data['weights']
                if 'growth' in weights:
                    self.config_vars['growth_quality_weight'].set(weights['growth'])
                if 'risk' in weights:
                    self.config_vars['risk_quality_weight'].set(weights['risk'])
                if 'valuation' in weights:
                    self.config_vars['valuation_weight'].set(weights['valuation'])
                if 'sentiment' in weights:
                    self.config_vars['sentiment_weight'].set(weights['sentiment'])
                
                # Update weight sum display
                self._update_weight_sum()
            
            # Apply screening criteria if present
            if 'screening' in profile_data:
                screening = profile_data['screening']
                
                # Basic filters
                if 'min_roe' in screening:
                    self.config_vars['roe_avg_min'].set(screening['min_roe'] * 100)
                
                # Market cap
                if 'market_cap' in screening:
                    if 'min_market_cap' in screening['market_cap'] and screening['market_cap']['min_market_cap']:
                        self.config_vars['market_cap_min'].set(screening['market_cap']['min_market_cap'])
                    if 'max_market_cap' in screening['market_cap'] and screening['market_cap']['max_market_cap']:
                        self.config_vars['market_cap_max'].set(screening['market_cap']['max_market_cap'])
                
                # Growth
                if 'growth' in screening:
                    if 'min_revenue_growth' in screening['growth']:
                        self.config_vars['revenue_growth_min_cagr'].set(screening['growth']['min_revenue_growth'] * 100)
                    if 'min_earnings_growth' in screening['growth']:
                        self.config_vars['eps_growth_min_cagr'].set(screening['growth']['min_earnings_growth'] * 100)
                
                # Risk
                if 'risk' in screening:
                    if 'max_debt_to_equity' in screening['risk']:
                        self.config_vars['debt_to_equity_max'].set(screening['risk']['max_debt_to_equity'])
                    if 'min_interest_coverage' in screening['risk']:
                        self.config_vars['interest_coverage_min'].set(screening['risk']['min_interest_coverage'])
                
                # Valuation
                if 'valuation' in screening:
                    if 'max_pe_ratio' in screening['valuation']:
                        self.config_vars['per_max'].set(screening['valuation']['max_pe_ratio'])
                    if 'max_pb_ratio' in screening['valuation']:
                        self.config_vars['pbr_max'].set(screening['valuation']['max_pb_ratio'])
            
            messagebox.showinfo("Success", f"Profile loaded successfully from {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {str(e)}")


def run_gui():
    """Run the GUI application"""
    root = tk.Tk()
    app = GUIApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()