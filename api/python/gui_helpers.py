"""
GUI helper utilities for input validation and tooltips.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ValidatedEntry(ttk.Entry):
    """Entry widget with built-in validation and tooltip support."""

    def __init__(self, parent, textvariable, validate_func: Optional[Callable] = None,
                 tooltip: Optional[str] = None, min_val: Optional[float] = None,
                 max_val: Optional[float] = None, dtype: type = float, **kwargs):
        """
        Initialize a validated entry widget.
        
        Args:
            parent: Parent widget
            textvariable: Variable to bind to
            validate_func: Custom validation function
            tooltip: Tooltip text to display
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            dtype: Data type (float or int)
        """
        super().__init__(parent, textvariable=textvariable, **kwargs)

        self.textvariable = textvariable
        self.min_val = min_val
        self.max_val = max_val
        self.dtype = dtype
        self.custom_validate = validate_func

        # Set up validation
        self.configure(validate="focusout", validatecommand=(self.register(self._validate), '%P'))

        # Set up tooltip
        if tooltip:
            self.tooltip = ToolTip(self, tooltip)

        # Bind events for visual feedback
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyRelease>", self._on_key_release)

    def _validate(self, value: str) -> bool:
        """Validate the entry value."""
        if not value:  # Allow empty values
            return True

        try:
            # Try to convert to the specified type
            if self.dtype == int:
                val = int(value)
            else:
                val = float(value)

            # Check range constraints
            if self.min_val is not None and val < self.min_val:
                self.configure(foreground="red")
                return False

            if self.max_val is not None and val > self.max_val:
                self.configure(foreground="red")
                return False

            # Custom validation
            if self.custom_validate and not self.custom_validate(val):
                self.configure(foreground="red")
                return False

            # Valid value
            self.configure(foreground="black")
            return True

        except (ValueError, TypeError):
            self.configure(foreground="red")
            return False

    def _on_focus_out(self, event):
        """Handle focus out event."""
        self._validate(self.get())

    def _on_key_release(self, event):
        """Provide real-time feedback."""
        self._validate(self.get())


class PercentageEntry(ValidatedEntry):
    """Entry widget specifically for percentage values (0-100)."""

    def __init__(self, parent, textvariable, tooltip: Optional[str] = None, **kwargs):
        default_tooltip = tooltip or "Enter a percentage value between 0 and 100"
        super().__init__(parent, textvariable, min_val=0, max_val=100,
                        dtype=float, tooltip=default_tooltip, **kwargs)


class WeightEntry(ValidatedEntry):
    """Entry widget specifically for weight values (0-1)."""

    def __init__(self, parent, textvariable, tooltip: Optional[str] = None, **kwargs):
        default_tooltip = tooltip or "Enter a weight value between 0 and 1"
        super().__init__(parent, textvariable, min_val=0, max_val=1,
                        dtype=float, tooltip=default_tooltip, **kwargs)


class ToolTip:
    """Create a tooltip for a given widget."""

    def __init__(self, widget, text: str, delay: int = 500):
        """
        Initialize tooltip.
        
        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
            delay: Delay before showing tooltip (ms)
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        self.x = self.y = 0

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        """Schedule tooltip display."""
        self._schedule()

    def _on_leave(self, event=None):
        """Hide tooltip."""
        self._unschedule()
        self._hide()

    def _schedule(self):
        """Schedule tooltip display after delay."""
        self._unschedule()
        self.id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        """Cancel scheduled tooltip display."""
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def _show(self):
        """Display the tooltip."""
        if self.tooltip_window or not self.text:
            return

        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

        tw.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        """Hide the tooltip."""
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()


def add_tooltip(widget, text: str):
    """Convenience function to add a tooltip to a widget."""
    return ToolTip(widget, text)


def create_labeled_entry(parent, label_text: str, variable, row: int, column: int = 0,
                        tooltip: Optional[str] = None, min_val: Optional[float] = None,
                        max_val: Optional[float] = None, dtype: type = float,
                        entry_type: str = "standard") -> ValidatedEntry:
    """
    Create a labeled entry with validation.
    
    Args:
        parent: Parent widget
        label_text: Label text
        variable: Variable to bind to
        row: Grid row
        column: Grid column for label
        tooltip: Tooltip text
        min_val: Minimum value
        max_val: Maximum value
        dtype: Data type
        entry_type: Type of entry ("standard", "percentage", "weight")
    
    Returns:
        The created entry widget
    """
    # Create label
    label = ttk.Label(parent, text=label_text)
    label.grid(row=row, column=column, sticky=tk.W, padx=5, pady=5)

    # Add tooltip to label if provided
    if tooltip:
        add_tooltip(label, tooltip)

    # Create appropriate entry type
    if entry_type == "percentage":
        entry = PercentageEntry(parent, variable, tooltip=tooltip)
    elif entry_type == "weight":
        entry = WeightEntry(parent, variable, tooltip=tooltip)
    else:
        entry = ValidatedEntry(parent, variable, tooltip=tooltip,
                              min_val=min_val, max_val=max_val, dtype=dtype)

    entry.grid(row=row, column=column + 1, padx=5, pady=5)

    return entry


def create_section_frame(parent, title: str, **pack_kwargs) -> ttk.LabelFrame:
    """Create a labeled frame section."""
    frame = ttk.LabelFrame(parent, text=title)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10, **pack_kwargs)
    return frame
