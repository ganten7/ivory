#!/usr/bin/env python3
"""
Terminal/GUI-based MIDI Monitor with Chord Detection
Displays MIDI notes on a full 88-key keyboard visualization, similar to VMPK
Now using GTK3 for native GNOME integration and single-instance support
Includes chord detection and detachable chord display window
"""

import sys
import time
import argparse
import json
import os
import threading
from collections import defaultdict
from typing import Dict, Set, Optional, Tuple
from pathlib import Path

# Import chord detector
try:
    from chord_detector import ChordDetector
    CHORD_DETECTOR_AVAILABLE = True
except ImportError:
    CHORD_DETECTOR_AVAILABLE = False
    print("Warning: chord_detector module not found. Chord detection disabled.")

# GTK3 imports - import cairo BEFORE gi to ensure proper binding
try:
    import cairo  # Import cairo first to ensure proper binding with gi
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GdkX11', '3.0')
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Gtk, Gdk, GdkX11, GLib, Gio, GdkPixbuf, Pango, PangoCairo
    GTK_AVAILABLE = True
except ImportError as e:
    print(f"Error: GTK3 is required. Install with:")
    print(f"  sudo apt-get install python3-gi gir1.2-gtk-3.0 python3-cairo python3-gi-cairo")
    print(f"Import error: {e}")
    sys.exit(1)

# Note: python3-gi-cairo must be installed for Cairo integration to work
# The error will be caught at runtime when the draw handler is called

# Process name will be set after tkinter initializes

# Check for dependencies only when actually needed (not for --help)
def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import mido
        from mido import Message
    except ImportError:
        print("Error: mido library not found. Install it with:")
        print("  pip install --user --break-system-packages mido python-rtmidi")
        print("\nNote: python-rtmidi requires ALSA development libraries:")
        print("  sudo apt-get install libasound2-dev")
        sys.exit(1)
    
    # Check if rtmidi backend is available
    try:
        import rtmidi
    except ImportError:
        print("Error: python-rtmidi backend not found.")
        print("mido requires python-rtmidi to work on Linux.")
        print("\nTo install:")
        print("  1. Install ALSA development libraries:")
        print("     sudo apt-get install libasound2-dev")
        print("  2. Install python-rtmidi:")
        print("     pip install --user --break-system-packages python-rtmidi")
        sys.exit(1)
    
    return mido, Message

# Import mido only when needed
mido = None
Message = None

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

# MIDI note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Standard 88-key piano: A0 (21) to C8 (108)
KEYBOARD_START_NOTE = 21  # A0
KEYBOARD_END_NOTE = 108   # C8
KEYBOARD_TOTAL_KEYS = 88

def note_name(note_number: int) -> str:
    """Convert MIDI note number to name (e.g., 60 -> 'C4')"""
    # MIDI note 0 = C-1, note 12 = C0, note 24 = C1, note 36 = C2, note 48 = C3, note 60 = C4
    octave = (note_number // 12) - 1
    note = NOTE_NAMES[note_number % 12]
    return f"{note}{octave}"

def is_white_key(note_number: int) -> bool:
    """Check if a MIDI note is a white key"""
    note_in_octave = note_number % 12
    return note_in_octave in [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B

def is_black_key(note_number: int) -> bool:
    """Check if a MIDI note is a black key"""
    return not is_white_key(note_number)

def get_white_key_position(note_number: int) -> int:
    """Get position of white key in 88-key layout (0-51 for white keys)"""
    if not is_white_key(note_number):
        return -1
    
    # Count white keys from A0
    octave = note_number // 12
    note_in_octave = note_number % 12
    
    # White keys per octave: C, D, E, F, G, A, B = 7 keys
    # But first octave (A0-B0) only has A, B = 2 keys
    if octave == 1:  # A0-B0
        if note_in_octave == 9:  # A
            return 0
        elif note_in_octave == 11:  # B
            return 1
        else:
            return -1
    
    # From C1 onwards, standard pattern
    white_keys_before = 2  # A0, B0
    # Count full octaves before this one (C1-B1 is octave 2, C2-B2 is octave 3, etc.)
    if octave >= 2:
        # For octave 2 (C1-B1), we've already counted A0-B0 (2 keys)
        # For octave 3 (C2-B2), add 7 more (C1-B1)
        # For octave 4 (C3-B3), add 14 more (C1-B1 + C2-B2)
        octaves_before = octave - 2  # Number of full octaves (C-B) before this one
        white_keys_before += octaves_before * 7
    
    # Position within octave (C=0, D=1, E=2, F=3, G=4, A=5, B=6)
    white_key_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
    white_keys_before += white_key_map[note_in_octave]
    
    return white_keys_before

def get_black_key_position(note_number: int) -> Tuple[int, int]:
    """Get position of black key: (octave_offset, key_in_octave)"""
    if not is_black_key(note_number):
        return (-1, -1)
    
    octave = note_number // 12
    note_in_octave = note_number % 12
    
    # Black keys: C#, D#, F#, G#, A#
    black_key_map = {1: 0, 3: 1, 6: 2, 8: 3, 10: 4}
    return (octave, black_key_map[note_in_octave])

class ColorConfig:
    """Color configuration for keyboard display"""
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.expanduser("~/.config/midi-monitor-colors.json")
        self.colors = self.load_colors()
    
    def load_colors(self) -> Dict:
        """Load colors from config file or use defaults"""
        default_colors = {
            "white_key_idle": "#FFFFFF",
            "white_key_active_low": "#90EE90",      # Light green
            "white_key_active_med": "#FFD700",      # Gold
            "white_key_active_high": "#FF6347",     # Tomato red
            "black_key_idle": "#000000",
            "black_key_active_low": "#32CD32",      # Lime green
            "black_key_active_med": "#FFA500",      # Orange
            "black_key_active_high": "#DC143C",      # Crimson
            "velocity_threshold_low": 64,
            "velocity_threshold_high": 100,
            "terminal_colors": {
                "low": "green",
                "med": "yellow",
                "high": "red"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_colors = json.load(f)
                    default_colors.update(user_colors)
            except Exception as e:
                print(f"Warning: Could not load color config: {e}")
        
        return default_colors
    
    def save_colors(self):
        """Save current colors to config file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.colors, f, indent=2)
    
    def get_color_for_velocity(self, velocity: int, is_white: bool) -> str:
        """Get color for a key based on velocity"""
        if velocity <= self.colors["velocity_threshold_low"]:
            key = "white_key_active_low" if is_white else "black_key_active_low"
        elif velocity <= self.colors["velocity_threshold_high"]:
            key = "white_key_active_med" if is_white else "black_key_active_med"
        else:
            key = "white_key_active_high" if is_white else "black_key_active_high"
        return self.colors[key]
    
    def get_terminal_color(self, velocity: int) -> str:
        """Get terminal color code for velocity"""
        if velocity <= self.colors["velocity_threshold_low"]:
            color_name = self.colors["terminal_colors"]["low"]
        elif velocity <= self.colors["velocity_threshold_high"]:
            color_name = self.colors["terminal_colors"]["med"]
        else:
            color_name = self.colors["terminal_colors"]["high"]
        
        color_map = {
            "green": Colors.BG_GREEN,
            "yellow": Colors.BG_YELLOW,
            "red": Colors.BG_RED,
            "blue": Colors.BG_BLUE,
            "magenta": Colors.BG_MAGENTA,
            "cyan": Colors.BG_CYAN
        }
        return color_map.get(color_name, Colors.BG_GREEN)

class MIDIMonitor(Gtk.Application):
    def __init__(self, port_name: Optional[str] = None, 
                 color_config: Optional[ColorConfig] = None):
        # Initialize Gtk.Application with unique application_id for single-instance support
        super().__init__(application_id="com.midimonitor.app",
                        flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        self.port_name = port_name
        self.color_config = color_config or ColorConfig()
        self.active_notes: Dict[int, Dict] = {}  # note_number -> {velocity, time}
        self.notes_to_release: set = set()  # Notes that received note_off while sustain was active
        self.note_history: list = []
        self.message_count = 0
        self.start_time = time.time()
        self.sustain_pedal_active = False  # Track sustain pedal (CC 64)
        self.window = None  # Will hold the ApplicationWindow
        
        # Chord detection - enabled by default
        self.chord_detection_enabled = True if CHORD_DETECTOR_AVAILABLE else False
        self.chord_window_detached = False
        self.chord_window = None
        self.current_chord = None
        self.chord_label = None
        self.original_window_height = 150  # Store original piano-only height
        self.chord_label_height = 50  # Extra height for chord label (1/3 of piano height)
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_detector = ChordDetector()
        else:
            self.chord_detector = None
        
        # Color customization - load from config or use defaults
        self.config_file = Path.home() / ".config" / "midi-monitor-gui.json"
        self.load_color_config()

        # Update chord detector with loaded preferences
        if self.chord_detector:
            self.chord_detector.set_note_preference(self.prefer_flats)
        
        # Try to import PIL for icon creation
        try:
            from PIL import Image, ImageDraw
            self.PIL_available = True
            self.Image = Image
            self.ImageDraw = ImageDraw
        except ImportError:
            self.PIL_available = False
        
        # Connect activate signal - this is called when app is launched
        self.connect("activate", self.on_activate)
    
    def _update_window_aspect_ratio(self):
        """Update window aspect ratio lock based on current_aspect_ratio"""
        # Geometry hints don't work reliably on all window managers
        # So we skip this entirely and handle resizing differently
        pass

    def load_color_config(self):
        """Load color configuration from file or use defaults"""
        defaults = {
            "dark_mode": False,
            "white_key_idle_color": "#E8DCC0",  # Darker ivory (slightly darker than before) - new default
            "black_key_idle_color": "#1a1a1a",  # Dark black
            "white_key_active_color": "#6C9BD2",  # Blue (your current selection)
            "black_key_active_color": "#6C9BD2",  # Blue (your current selection)
            "sustain_color": "#D2A36C",  # Golden brown (your current selection)
            "prefer_flats": True  # Default to flats (Bb instead of A#)
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.dark_mode = config.get("dark_mode", defaults["dark_mode"])
                    # Use default lighter ivory if config has the old dark ivory
                    saved_white = config.get("white_key_idle_color", defaults["white_key_idle_color"])
                    if saved_white == "#D4C5A9":  # Old dark ivory
                        self.white_key_idle_color = defaults["white_key_idle_color"]  # Use lighter ivory
                    else:
                        self.white_key_idle_color = saved_white
                    self.black_key_idle_color = config.get("black_key_idle_color", defaults["black_key_idle_color"])
                    self.white_key_active_color = config.get("white_key_active_color", defaults["white_key_active_color"])
                    self.black_key_active_color = config.get("black_key_active_color", defaults["black_key_active_color"])
                    self.sustain_color = config.get("sustain_color", defaults["sustain_color"])
                    self.prefer_flats = config.get("prefer_flats", defaults["prefer_flats"])
            except Exception as e:
                # If loading fails, use defaults
                self.dark_mode = defaults["dark_mode"]
                self.white_key_idle_color = defaults["white_key_idle_color"]
                self.black_key_idle_color = defaults["black_key_idle_color"]
                self.white_key_active_color = defaults["white_key_active_color"]
                self.black_key_active_color = defaults["black_key_active_color"]
                self.sustain_color = defaults["sustain_color"]
                self.prefer_flats = defaults["prefer_flats"]
        else:
            # Use defaults
            self.dark_mode = defaults["dark_mode"]
            self.white_key_idle_color = defaults["white_key_idle_color"]
            self.black_key_idle_color = defaults["black_key_idle_color"]
            self.white_key_active_color = defaults["white_key_active_color"]
            self.black_key_active_color = defaults["black_key_active_color"]
            self.sustain_color = defaults["sustain_color"]
            self.prefer_flats = defaults["prefer_flats"]
    
    def save_color_config(self):
        """Save color configuration to file"""
        config = {
            "dark_mode": self.dark_mode,
            "white_key_idle_color": self.white_key_idle_color,
            "black_key_idle_color": self.black_key_idle_color,
            "white_key_active_color": self.white_key_active_color,
            "black_key_active_color": self.black_key_active_color,
            "sustain_color": self.sustain_color,
            "prefer_flats": self.prefer_flats
        }
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            pass  # Silently fail if we can't save
    
    def custom_color_picker(self, title, initial_color):
        """Custom color picker with hex input and live preview - GTK3 version"""
        if not self.window or not self.window.get_visible():
            print("Warning: Main window not available or not visible")
            return None
        
        try:
            dialog = Gtk.Dialog(title=title, parent=self.window, modal=True)
            dialog.set_default_size(400, 300)
            dialog.set_transient_for(self.window)  # Ensure dialog is transient for main window
            dialog.set_destroy_with_parent(True)
            
            result_color = [initial_color]  # Use list to allow modification in nested functions
            
            # Content area
            content_area = dialog.get_content_area()
            content_area.set_spacing(10)
            content_area.set_margin_top(15)
            content_area.set_margin_bottom(15)
            content_area.set_margin_start(15)
            content_area.set_margin_end(15)
            
            # Standard color chooser button
            color_button = Gtk.Button(label="Open Color Picker")
            color_button.connect("clicked", lambda btn: self._open_gtk_color_chooser(dialog, hex_entry, result_color, update_preview))
            content_area.pack_start(color_button, False, False, 0)
            
            # Hex input frame
            hex_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            hex_label = Gtk.Label(label="Hex Code:")
            hex_entry = Gtk.Entry()
            hex_entry.set_text(initial_color.upper())
            hex_entry.set_width_chars(12)
            hex_box.pack_start(hex_label, False, False, 0)
            hex_box.pack_start(hex_entry, True, True, 0)
            content_area.pack_start(hex_box, False, False, 0)
            
            # Preview drawing area
            preview_frame = Gtk.Frame(label="Preview")
            preview_area = Gtk.DrawingArea()
            preview_area.set_size_request(250, 80)
            preview_area.connect("draw", lambda w, cr: self._draw_preview(cr, result_color[0]))
            preview_frame.add(preview_area)
            content_area.pack_start(preview_frame, False, False, 0)
            
            def validate_hex(hex_str):
                """Validate and normalize hex color"""
                hex_str = hex_str.strip().upper()
                if hex_str.startswith('#'):
                    hex_str = hex_str[1:]
                if len(hex_str) == 3:
                    hex_str = hex_str[0]*2 + hex_str[1]*2 + hex_str[2]*2
                if len(hex_str) == 6 and all(c in '0123456789ABCDEF' for c in hex_str):
                    return '#' + hex_str
                return None
            
            def update_preview(color_hex):
                """Update preview"""
                result_color[0] = color_hex
                preview_area.queue_draw()
            
            def on_hex_change(entry):
                """Handle hex input change"""
                hex_value = entry.get_text()
                valid_color = validate_hex(hex_value)
                if valid_color:
                    result_color[0] = valid_color
                    # Update entry to show normalized format
                    entry.set_text(valid_color.upper())
                    update_preview(valid_color)
            
            hex_entry.connect("changed", on_hex_change)
            hex_entry.connect("activate", lambda e: dialog.response(Gtk.ResponseType.OK))
            
            # Buttons
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("OK", Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)
            
            # Initial preview
            update_preview(initial_color)
        
            # Show dialog and all its contents
            dialog.show_all()
            
            # Ensure main window is visible and realized
            if self.window:
                self.window.present()
            
            # Focus hex entry after dialog is shown
            def focus_entry():
                hex_entry.grab_focus()
                hex_entry.select_region(0, -1)
                return False
            GLib.idle_add(focus_entry)
            
            # Run dialog (modal) - this blocks until user responds
            # dialog.run() automatically shows the dialog if not already shown
            response = dialog.run()
            
            # Get result before destroying
            result = None
            if response == Gtk.ResponseType.OK:
                hex_value = hex_entry.get_text()
                valid_color = validate_hex(hex_value)
                result = valid_color if valid_color else None
            
            # Clean up
            dialog.destroy()
            return result
        except Exception as e:
            print(f"Error showing color picker dialog: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _open_gtk_color_chooser(self, parent_dialog, hex_entry, result_color, update_preview):
        """Open GTK color chooser dialog"""
        dialog = Gtk.ColorChooserDialog(title="Choose Color", parent=parent_dialog)
        # Parse hex color to RGBA
        try:
            hex_color = result_color[0].lstrip('#')
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            color = Gdk.RGBA(red=r, green=g, blue=b, alpha=1.0)
            dialog.set_rgba(color)
        except:
            pass
        
        # Show dialog
        dialog.show_all()
        
        # Run dialog (modal)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            color = dialog.get_rgba()
            # Convert to hex
            hex_color = f"#{int(color.red * 255):02X}{int(color.green * 255):02X}{int(color.blue * 255):02X}"
            hex_entry.set_text(hex_color)
            update_preview(hex_color)
        dialog.destroy()
    
    def _draw_preview(self, cr, color_hex):
        """Draw color preview"""
        try:
            # Parse hex color
            hex_color = color_hex.lstrip('#')
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            
            # Draw rectangle
            cr.set_source_rgb(r, g, b)
            cr.rectangle(5, 5, 240, 70)
            cr.fill()
            
            # Draw border
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(2)
            cr.rectangle(5, 5, 240, 70)
            cr.stroke()
            
            # Draw text using Pango
            text_color = (0, 0, 0) if self._is_light_color(color_hex) else (1, 1, 1)
            cr.set_source_rgb(*text_color)
            layout = PangoCairo.create_layout(cr)
            font_desc = Pango.FontDescription.from_string("Courier Bold 12")
            layout.set_font_description(font_desc)
            layout.set_text(color_hex.upper(), -1)
            cr.move_to(125, 45)
            PangoCairo.show_layout(cr, layout)
        except:
            pass
    
    def _is_light_color(self, hex_color):
        """Check if color is light (for text contrast)"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Calculate luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance > 0.5
        except:
            return True
    
    def on_activate(self, app):
        """Called when application is activated - GTK3 version"""
        # If window already exists, present it (single-instance behavior)
        if self.window:
            self.window.present()
            return
        
        global mido
        mido, _ = check_dependencies()
        
        # Get available MIDI ports
        input_ports = mido.get_input_names()
        if not input_ports:
            error_dialog = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="No MIDI input ports found!"
            )
            error_dialog.run()
            error_dialog.destroy()
            sys.exit(1)
        
        # Select port - prefer USB-MIDI if available
        if self.port_name:
            if self.port_name in input_ports:
                port = self.port_name
            else:
                port = None
                port_lower = self.port_name.lower()
                for p in input_ports:
                    if port_lower in p.lower() or p.lower() in port_lower:
                        port = p
                        break
                if not port:
                    error_dialog = Gtk.MessageDialog(
                        parent=None,
                        flags=Gtk.DialogFlags.MODAL,
                        type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        message_format=f"Error: Port '{self.port_name}' not found!"
                    )
                    error_dialog.run()
                    error_dialog.destroy()
                    sys.exit(1)
        else:
            # Prefer USB-MIDI, then Scarlett, then first available
            port = None
            for p in input_ports:
                if "USB-MIDI" in p:
                    port = p
                    break
            if not port:
                for p in input_ports:
                    if "Scarlett" in p or ("USB" in p and "MIDI" in p):
                        port = p
                        break
            if not port:
                port = input_ports[0]
        
        try:
            self.inport = mido.open_input(port)
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format=f"Error opening MIDI port: {e}"
            )
            error_dialog.run()
            error_dialog.destroy()
            sys.exit(1)
        
        self.actual_port_name = port
        
        # Start MIDI input thread
        self.midi_thread_running = True
        self.midi_thread = threading.Thread(target=self.midi_input_thread, daemon=True)
        self.midi_thread.start()
        
        # Create window
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("")
        # Remove window margins/borders that create white space
        self.window.set_border_width(0)
        # Set window background to gray to match piano and eliminate white space
        css_provider_window = Gtk.CssProvider()
        css_provider_window.load_from_data(b"""
            window {
                background-color: #E8E8E8;
                margin: 0;
                padding: 0;
            }
        """)
        style_context_window = self.window.get_style_context()
        style_context_window.add_provider(css_provider_window, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Set WM_CLASS for GNOME - use set_role (set_wmclass is deprecated)
        try:
            self.window.set_role("MidiMonitor")
        except:
            # Fallback: try deprecated method but suppress warning
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    self.window.set_wmclass("MidiMonitor", "MidiMonitor")
                except:
                    pass
        self.window.set_application(self)
        
        # Set window icon
        self.simple_icon_file = Path.home() / ".local" / "share" / "icons" / "midi-monitor.png"
        
        # Set icon before showing (important for initial display)
        self._setup_icon()
        
        # Also set icon after window is shown (for better compatibility)
        def set_icon_after_show():
            if self.window:
                self._setup_icon()
        GLib.idle_add(set_icon_after_show)
        
        # Set icon when window is realized (X11 properties need window to be realized)
        def set_icon_after_realize(widget):
            self._setup_icon()
            # Also set X11 icon property after realization
            if self.simple_icon_file.exists():
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(self.simple_icon_file))
                    self._set_x11_icon(pixbuf)
                except:
                    pass
        self.window.connect("realize", set_icon_after_realize)
        
        # Set icon when window is mapped (shown)
        def set_icon_after_map(widget, event):
            self._setup_icon()
            # Set X11 icon property again after mapping
            if self.simple_icon_file.exists():
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(self.simple_icon_file))
                    self._set_x11_icon(pixbuf)
                except:
                    pass
            return False
        self.window.connect("map-event", set_icon_after_map)
        
        # Default window size - round width to nearest 10 pixels
        # Start with piano-only height (chord detection disabled by default)
        default_width = round(1300 / 10) * 10  # Round to nearest 10
        default_height = self.original_window_height
        self.window.set_default_size(default_width, default_height)

        # Set aspect ratio to lock it while keeping window resizable
        # This will be updated when chord detection is toggled
        self.current_aspect_ratio = default_width / default_height

        # Store piano aspect ratio for content scaling
        # Piano aspect ratio: 1300 / 150 = 8.667:1
        self.piano_aspect = 1300 / self.original_window_height  # ~8.67:1

        # Set minimum size to prevent cutting off piano
        geom = Gdk.Geometry()
        geom.min_width = 200
        # Min height = piano height + chord height (if enabled)
        if self.chord_detection_enabled:
            geom.min_height = self.original_window_height + self.chord_label_height
        else:
            geom.min_height = self.original_window_height
        self.window.set_geometry_hints(
            None,
            geom,
            Gdk.WindowHints.MIN_SIZE
        )

        # No aspect ratio enforcement on window - let user resize smoothly
        # Piano will maintain aspect ratio inside with black bars as needed

        # Initialize piano viewport (will be updated in on_configure)
        self.piano_x = 0
        self.piano_y = 0
        self.piano_width = default_width
        self.piano_height = default_height

        # Track last set minimum height to avoid updating geometry hints constantly
        self._last_min_height = None

        # Flag to prevent on_configure from updating geometry during manual operations
        self._skip_geometry_update = False

        # Track if window is locked from previous detach (keeps it locked even when chord detection disabled)
        self._window_locked_size = None


        # Background color - use light gray for piano area (keys will be drawn on top)
        self.bg_color = "#E8E8E8"
        
        # Create drawing area for keyboard
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.connect("configure-event", self.on_configure)
        self.drawing_area.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect("motion-notify-event", self.on_motion_notify)
        # Set a very small minimum size to prevent collapse, but allow shrinking
        self.drawing_area.set_size_request(100, 20)
        # Let drawing area expand to fill window
        self.drawing_area.set_vexpand(False)  # Piano should not expand vertically
        self.drawing_area.set_hexpand(True)
        self.drag_start_x = None
        self.drag_start_y = None
        self.window_start_x = 0
        self.window_start_y = 0
        self.drawing_area.connect("button-press-event", self.on_button_press)
        
        # Create chord label as DrawingArea for pixelated Cairo rendering
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_label = Gtk.DrawingArea()
            self.chord_label.set_name("chord-label")
            # Show by default if chord detection is enabled
            self.chord_label.set_visible(self.chord_detection_enabled)
            # Remove margins to eliminate white space
            self.chord_label.set_margin_top(0)
            self.chord_label.set_margin_bottom(0)
            self.chord_label.set_margin_start(0)
            self.chord_label.set_margin_end(0)
            # Set height to 1/3 of piano height
            self.chord_label.set_size_request(-1, self.chord_label_height)
            self.chord_label.set_vexpand(False)
            self.chord_label.set_hexpand(True)
            # Set black background via CSS
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(b"""
                #chord-label {
                    background-color: #000000;
                }
            """)
            style_context = self.chord_label.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            style_context.add_class("chord-label")
            # Ensure DrawingArea is set to draw - required for custom Cairo rendering
            # Must be called before connecting draw handler
            self.chord_label.set_app_paintable(True)
            # Connect draw handler for custom Cairo rendering
            self.chord_label.connect("draw", self.on_chord_label_draw)
            # Enable button events for right-click menu
            self.chord_label.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
            self.chord_label.connect("button-press-event", self.on_chord_label_button_press)
            # Force initial draw
            self.chord_label.queue_draw()
        
        # Create main container with chord label and drawing area
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        # Set container background to match piano to prevent white flashing during resize
        css_provider_box = Gtk.CssProvider()
        css_provider_box.load_from_data(b"""
            .main-box {
                background-color: #E8E8E8;
            }
            drawingarea {
                background-color: #E8E8E8;
            }
        """)
        main_box.get_style_context().add_provider(css_provider_box, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        main_box.get_style_context().add_class("main-box")
        # Ensure drawing area has proper background
        self.drawing_area.get_style_context().add_provider(css_provider_box, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Remove any margins/padding from container
        main_box.set_margin_top(0)
        main_box.set_margin_bottom(0)
        main_box.set_margin_start(0)
        main_box.set_margin_end(0)
        # Allow box to expand/shrink freely
        main_box.set_vexpand(True)
        main_box.set_hexpand(True)
        # Store reference for later use
        self.main_box = main_box
        
        # Add drawing area first (piano) - use pack_end to ensure it stays at bottom
        # Don't expand - piano has fixed aspect ratio, chord label takes extra space
        main_box.pack_end(self.drawing_area, False, False, 0)

        # Add chord label on top (above piano) - use pack_start to put at top
        # Expand to take all extra vertical space (piano has fixed aspect ratio)
        if CHORD_DETECTOR_AVAILABLE and self.chord_label:
            # Chord label expands to fill available space, piano stays at aspect ratio
            main_box.pack_start(self.chord_label, True, True, 0)
        
        # Don't override drawing area background - let it use bg_color from on_draw
        
        self.window.add(main_box)
        
        # Calculate initial key dimensions
        white_keys_count = 52
        self.white_key_width = default_width // white_keys_count
        self.white_key_height = default_height
        self.black_key_width = int(self.white_key_width * 0.7)
        self.black_key_height = int(self.white_key_height * 0.65)
        self.keyboard_start_x = 0
        self.keyboard_start_y = 0
        
        # Connect window signals
        self.window.connect("destroy", self.on_window_destroy)
        
        # Create context menu (will be shown on right-click)
        self._create_context_menu()
        
        # Setup chord detection update timer
        if CHORD_DETECTOR_AVAILABLE and self.chord_detector:
            GLib.timeout_add(100, self.update_chord_detection)  # Update every 100ms
        
        # Show window
        self.window.show_all()
        
        # Ensure window is fully realized before starting updates
        def start_updates():
            if self.window and self.drawing_area:
                # Initial draw
                self.drawing_area.queue_draw()
                # Start update timer
                GLib.timeout_add(50, self.update_gui)  # Update every 50ms
        
        # Wait for window to be fully shown before starting updates
        GLib.idle_add(start_updates)
    
    def _setup_icon(self):
        """Setup window icon"""
        if not self.window:
            return
            
        if not self.PIL_available:
            return
        
        try:
            # Create icon if it doesn't exist
            if not self.simple_icon_file.exists():
                icon_dir = self.simple_icon_file.parent
                icon_dir.mkdir(parents=True, exist_ok=True)
                
                icon_size = 128
                icon_img = self.Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
                draw = self.ImageDraw.Draw(icon_img)
                
                # Draw piano keyboard
                key_width = max(1, icon_size // 7)
                for i in range(7):
                    x = i * key_width
                    draw.rectangle([x, 0, x + key_width - 1, icon_size - 1], 
                                 fill=(245, 245, 220, 255), outline=(139, 125, 107, 255))
                
                black_key_height = int(icon_size * 0.65)
                black_positions = [1, 2, 4, 5, 6]
                for pos in black_positions:
                    x = pos * key_width - max(1, key_width // 3)
                    black_w = max(1, int(key_width * 0.7))
                    draw.rectangle([x, 0, x + black_w, black_key_height],
                                 fill=(26, 26, 26, 255), outline=(0, 0, 0, 255))
                
                icon_img.save(str(self.simple_icon_file), 'PNG')
            
            # Set icon on window using multiple methods for maximum compatibility
            if self.simple_icon_file.exists():
                try:
                    # Load the icon file
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(self.simple_icon_file))
                    
                    # Method 1: Set single icon (most common)
                    self.window.set_icon(pixbuf)
                    
                    # Method 2: Set icon list with multiple sizes (better for some window managers)
                    sizes = [16, 32, 48, 64, 128]
                    icon_list = []
                    for size in sizes:
                        try:
                            pixbuf_scaled = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
                            icon_list.append(pixbuf_scaled)
                        except:
                            pass
                    if icon_list:
                        self.window.set_icon_list(icon_list)
                    
                    # Method 3: Set icon via X11 properties (for GNOME window managers)
                    # This needs to happen after window is realized, so we'll do it separately
                    if self.window.get_realized():
                        try:
                            self._set_x11_icon(pixbuf)
                        except:
                            pass
                except Exception as e:
                    # Fallback: try setting from file path directly
                    try:
                        self.window.set_icon_from_file(str(self.simple_icon_file))
                    except:
                        pass
        except Exception as e:
            pass  # Icon setup failed, continue without icon
    
    def _set_x11_icon(self, pixbuf):
        """Set window icon via X11 properties for better GNOME compatibility"""
        try:
            if not self.window or not self.window.get_realized():
                return
                
            import ctypes
            from ctypes import c_void_p, c_char_p, c_uint32, POINTER
            
            # Get window ID using GdkX11
            gdk_window = self.window.get_window()
            if not gdk_window:
                return
            window_id = GdkX11.X11Window.get_xid(gdk_window)
            
            # Load X11 libraries
            xlib = ctypes.CDLL("libX11.so.6")
            xlib.XOpenDisplay.restype = c_void_p
            
            display = xlib.XOpenDisplay(None)
            if not display:
                return
            
            # Get atom for _NET_WM_ICON
            atom_name = b"_NET_WM_ICON"
            atom = xlib.XInternAtom(display, atom_name, False)
            
            # Convert pixbuf to ARGB format
            width = pixbuf.get_width()
            height = pixbuf.get_height()
            has_alpha = pixbuf.get_has_alpha()
            n_channels = pixbuf.get_n_channels()
            rowstride = pixbuf.get_rowstride()
            pixels = pixbuf.get_pixels()
            
            # Convert to ARGB
            argb_data = []
            for y in range(height):
                for x in range(width):
                    offset = y * rowstride + x * n_channels
                    if has_alpha and n_channels >= 4:
                        r = pixels[offset]
                        g = pixels[offset + 1]
                        b = pixels[offset + 2]
                        a = pixels[offset + 3]
                    elif n_channels >= 3:
                        r = pixels[offset]
                        g = pixels[offset + 1]
                        b = pixels[offset + 2]
                        a = 255
                    else:
                        continue
                    
                    # ARGB format: (A << 24) | (R << 16) | (G << 8) | B
                    argb = (a << 24) | (r << 16) | (g << 8) | b
                    argb_data.append(argb)
            
            # Set property: width, height, then pixel data
            prop_data = [width, height] + argb_data
            PropArrayType = c_uint32 * len(prop_data)
            prop_array = PropArrayType(*prop_data)
            
            # Set the property (XA_CARDINAL = 6)
            xlib.XChangeProperty.argtypes = [c_void_p, ctypes.c_ulong, ctypes.c_ulong, 
                                             ctypes.c_ulong, ctypes.c_int, ctypes.c_int,
                                             ctypes.POINTER(ctypes.c_uint32), ctypes.c_int]
            xlib.XChangeProperty(
                display,
                window_id,
                atom,
                6,   # XA_CARDINAL
                32,  # format (32 bits)
                0,   # mode (Replace)
                prop_array,
                len(prop_data)
            )
            
            xlib.XFlush(display)
            xlib.XCloseDisplay(display)
        except Exception:
            pass
    
    def _create_piano_context_menu(self):
        """Create right-click context menu for piano"""
        self.piano_context_menu = Gtk.Menu()

        # Reordered menu: 7, 2, 3, 4, 5, 1, 6

        # 7. MIDI input selection
        midi_input_item = Gtk.MenuItem(label="Select MIDI Input...")
        midi_input_item.connect("activate", lambda w: self.select_midi_input())
        self.piano_context_menu.append(midi_input_item)

        self.piano_context_menu.append(Gtk.SeparatorMenuItem())

        # 2. Set White Key Color
        white_key_item = Gtk.MenuItem(label="Set White Key Color...")
        white_key_item.connect("activate", lambda w: self.pick_white_key_color())
        self.piano_context_menu.append(white_key_item)

        # 3. Set Black Key Color
        black_key_item = Gtk.MenuItem(label="Set Black Key Color...")
        black_key_item.connect("activate", lambda w: self.pick_black_key_color())
        self.piano_context_menu.append(black_key_item)

        self.piano_context_menu.append(Gtk.SeparatorMenuItem())

        # 4. Set Active Key Color
        active_key_item = Gtk.MenuItem(label="Set Active Key Color...")
        active_key_item.connect("activate", lambda w: self.pick_active_key_color())
        self.piano_context_menu.append(active_key_item)

        # 5. Set Sustain Color
        sustain_item = Gtk.MenuItem(label="Set Sustain Color...")
        sustain_item.connect("activate", lambda w: self.pick_sustain_color())
        self.piano_context_menu.append(sustain_item)

        self.piano_context_menu.append(Gtk.SeparatorMenuItem())

        # 1. Dark mode toggle
        dark_mode_label = "Light Mode" if self.dark_mode else "Dark Mode"
        dark_mode_item = Gtk.MenuItem(label=dark_mode_label)
        dark_mode_item.connect("activate", lambda w: self.toggle_dark_mode())
        self.piano_context_menu.append(dark_mode_item)

        # Chord detection menu options
        if CHORD_DETECTOR_AVAILABLE and self.chord_detector:
            # When detached, show "Attach Chord Window" instead of disable/enable
            if self.chord_window_detached:
                attach_item = Gtk.MenuItem(label="Attach Chord Window")
                attach_item.connect("activate", lambda w: self.toggle_chord_window())
                self.piano_context_menu.append(attach_item)
            else:
                # When attached, show chord detection toggle
                chord_toggle_label = "Disable Chord Detection" if self.chord_detection_enabled else "Enable Chord Detection"
                chord_toggle_item = Gtk.MenuItem(label=chord_toggle_label)
                chord_toggle_item.connect("activate", lambda w: self.toggle_chord_detection())
                self.piano_context_menu.append(chord_toggle_item)

                # Show Detach option when chord detection is enabled and attached
                if self.chord_detection_enabled:
                    detach_item = Gtk.MenuItem(label="Detach Chord Window")
                    detach_item.connect("activate", lambda w: self.toggle_chord_window())
                    self.piano_context_menu.append(detach_item)

        self.piano_context_menu.append(Gtk.SeparatorMenuItem())

        # 6. Reset to defaults
        reset_item = Gtk.MenuItem(label="Reset Settings to Default")
        reset_item.connect("activate", lambda w: self.reset_settings())
        self.piano_context_menu.append(reset_item)

        # Show all menu items
        self.piano_context_menu.show_all()

    def _create_chord_context_menu(self):
        """Create right-click context menu for chord display"""
        self.chord_context_menu = Gtk.Menu()

        # Chord detection options (only if available)
        if CHORD_DETECTOR_AVAILABLE and self.chord_detector:
            # Toggle flats/sharps preference
            flats_sharps_label = "Use Sharps (A#)" if self.prefer_flats else "Use Flats (Bb)"
            flats_sharps_item = Gtk.MenuItem(label=flats_sharps_label)
            flats_sharps_item.connect("activate", lambda w: self.toggle_flats_sharps())
            self.chord_context_menu.append(flats_sharps_item)

            # Toggle chord detection - only show if NOT detached
            if not self.chord_window_detached:
                chord_toggle_item = Gtk.MenuItem(label="Enable Chord Detection" if not self.chord_detection_enabled else "Disable Chord Detection")
                chord_toggle_item.connect("activate", lambda w: self.toggle_chord_detection())
                self.chord_context_menu.append(chord_toggle_item)

            # Detach/Attach chord window - only show if chord detection enabled
            if self.chord_detection_enabled:
                self.chord_context_menu.append(Gtk.SeparatorMenuItem())
                detach_item = Gtk.MenuItem(label="Detach Chord Window" if not self.chord_window_detached else "Attach Chord Window")
                detach_item.connect("activate", lambda w: self.toggle_chord_window())
                self.chord_context_menu.append(detach_item)

        # Show all menu items
        self.chord_context_menu.show_all()

    def _create_context_menu(self):
        """Create all context menus"""
        self._create_piano_context_menu()
        self._create_chord_context_menu()
    
    def on_motion_notify(self, widget, event):
        """Handle mouse motion"""
        return False
    
    def on_button_press(self, widget, event):
        """Handle mouse button press on piano"""
        if event.button == 3:  # Right click
            # Use popup_at_widget for GTK3 (closes automatically when clicking outside)
            # This positions the menu at the widget and handles cleanup properly
            self.piano_context_menu.popup_at_widget(
                widget,
                Gdk.Gravity.SOUTH_WEST,
                Gdk.Gravity.NORTH_WEST,
                event
            )
        return False

    def on_chord_label_button_press(self, widget, event):
        """Handle mouse button press on chord label"""
        if event.button == 3:  # Right click
            self.chord_context_menu.popup_at_widget(
                widget,
                Gdk.Gravity.SOUTH_WEST,
                Gdk.Gravity.NORTH_WEST,
                event
            )
        return False
    
    def on_window_destroy(self, window):
        """Handle window destroy"""
        self.midi_thread_running = False
        if hasattr(self, 'inport'):
            self.inport.close()
        self.window = None
        # Don't call Gtk.main_quit() - Gtk.Application handles this
    
    def on_configure(self, widget, event):
        """Handle drawing area configure (resize)"""
        # Get available space
        available_width = widget.get_allocated_width()
        available_height = widget.get_allocated_height()

        print(f"DEBUG ON_CONFIGURE: Drawing area allocated: {available_width}x{available_height}")

        # ALWAYS use full width to hug left and right edges
        # Calculate piano dimensions to maintain aspect ratio
        piano_width = available_width
        piano_height = piano_width / self.piano_aspect
        piano_x = 0  # Always hug left edge

        print(f"DEBUG PIANO DIMENSIONS: piano_aspect={self.piano_aspect:.2f}, available={available_width}x{available_height}, piano={piano_width:.1f}x{piano_height:.1f}")

        # Update minimum window height dynamically based on current width
        # This prevents cutting off the piano when stretched wide
        window_width, window_height = self.window.get_size()
        print(f"DEBUG ON_CONFIGURE: Window size: {window_width}x{window_height}")

        # Only update geometry if window has a reasonable size
        if window_width < 100:
            print(f"DEBUG ON_CONFIGURE: Window too small, skipping")
            return False

        # Skip geometry updates during manual operations
        # Keep skipping until window width is back to a reasonable size (>= 800px)
        if self._skip_geometry_update:
            if window_width >= 800:
                # Window has stabilized at a good size, re-enable updates
                print(f"DEBUG ON_CONFIGURE: Window stabilized at {window_width}x{window_height}, re-enabling geometry updates")
                self._skip_geometry_update = False
                # Don't unlock width constraint yet - keep it locked at current size
                # User can resize wider, and when they do, we'll detect it and unlock
            else:
                # Still in transition, keep skipping
                print(f"DEBUG ON_CONFIGURE: Manual operation in progress, window={window_width}x{window_height}, SKIPPING")
                return False

        required_piano_height = window_width / self.piano_aspect
        if self.chord_detection_enabled and not self.chord_window_detached:
            min_height = int(required_piano_height + self.chord_label_height)
        else:
            # Piano-only mode: lock vertical resizing
            min_height = int(required_piano_height)

        print(f"DEBUG ON_CONFIGURE: required_piano_height={required_piano_height}, min_height={min_height}, _last_min_height={self._last_min_height}")
        print(f"DEBUG ON_CONFIGURE: chord_detection_enabled={self.chord_detection_enabled}, chord_window_detached={self.chord_window_detached}")

        # Check if window is locked from previous detach
        if self._window_locked_size is not None:
            locked_width, locked_height = self._window_locked_size
            print(f"DEBUG ON_CONFIGURE: Window is locked at {locked_width}x{locked_height}, maintaining lock")
            # Keep window locked at this size
            geom = Gdk.Geometry()
            geom.min_width = locked_width
            geom.max_width = locked_width
            geom.min_height = locked_height
            geom.max_height = locked_height
            self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
            return False

        # Update geometry hints based on mode
        # Only update if minimum height changed significantly (>20px) to prevent choppy diagonal resizing
        if self._last_min_height is None or abs(min_height - self._last_min_height) > 20:
            print(f"DEBUG ON_CONFIGURE: UPDATING GEOMETRY HINTS")
            geom = Gdk.Geometry()
            geom.min_width = 200
            geom.min_height = min_height

            if self.chord_detection_enabled and not self.chord_window_detached:
                # Chord label visible: allow vertical resizing
                print(f"DEBUG ON_CONFIGURE: Setting MIN_SIZE only (allow vertical resize), min_height={min_height}")
                self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE)
            else:
                # Piano-only mode: lock vertical resizing
                geom.max_height = min_height
                print(f"DEBUG ON_CONFIGURE: Setting MIN_SIZE and MAX_SIZE (lock vertical), min/max_height={min_height}")
                self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)

            self._last_min_height = min_height
        else:
            print(f"DEBUG ON_CONFIGURE: Skipping geometry update, diff={abs(min_height - self._last_min_height)}")

        # Position piano based on whether chord detection is enabled
        if self.chord_detection_enabled and not self.chord_window_detached:
            # Chord label visible - hug bottom edge
            if piano_height <= available_height:
                # Piano fits - place at bottom
                piano_y = available_height - piano_height
            else:
                # Piano taller than available space - shouldn't happen with min height
                piano_y = 0
        else:
            # Chord detection disabled - hug top edge (no black bars on top)
            piano_y = 0

        print(f"DEBUG ON_CONFIGURE: Piano positioning - piano_y={piano_y}, piano_height={piano_height}, available_height={available_height}, window_height={window_height}")

        # Update drawing area size request to match required piano height
        # This ensures the drawing area gets the right amount of space in the vbox
        target_height = int(piano_height)
        self.drawing_area.set_size_request(-1, target_height)

        # Store piano viewport
        self.piano_x = piano_x
        self.piano_y = piano_y
        self.piano_width = piano_width
        self.piano_height = piano_height

        # Calculate key dimensions based on piano viewport
        white_keys_count = 52
        self.white_key_width = piano_width / white_keys_count
        self.white_key_height = piano_height
        self.black_key_width = self.white_key_width * 0.7
        self.black_key_height = self.white_key_height * 0.65

        return False
    
    def on_draw(self, widget, cr):
        """Draw full 88-key keyboard using Cairo - GTK3 version"""
        try:
            if not self.window or not self.drawing_area:
                return False

            # Ensure widget is realized
            if not widget.get_realized():
                return False

            # Get drawing area dimensions
            width = widget.get_allocated_width()
            height = widget.get_allocated_height()

            if width <= 1 or height <= 1:
                return False
        except TypeError as e:
            if 'cairo.Context' in str(e):
                print("\n" + "="*60)
                print("ERROR: python3-gi-cairo is not installed!")
                print("="*60)
                print("This package is required for Cairo integration with GTK3.")
                print("\nInstall it with:")
                print("  sudo apt-get install python3-gi-cairo")
                print("\nOr run the installation script:")
                print("  sudo ./install-midi-monitor-deps.sh")
                print("="*60 + "\n")
                sys.exit(1)
            return False
        except Exception:
            return False
        
        # Fill entire background with black (for letterboxing/pillarboxing)
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        # Save context and translate to piano viewport
        cr.save()
        cr.translate(self.piano_x, self.piano_y)

        # Clip to piano viewport to prevent drawing outside
        cr.rectangle(0, 0, self.piano_width, self.piano_height)
        cr.clip()

        # Fill piano background
        bg_r, bg_g, bg_b = self._hex_to_rgb(self.bg_color)
        cr.set_source_rgb(bg_r, bg_g, bg_b)
        cr.paint()

        # Key dimensions are already calculated in on_configure
        # No need to recalculate here
        
        # Draw white keys
        white_keys_list = [n for n in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1) if is_white_key(n)]
        
        for idx, note in enumerate(white_keys_list):
            x = idx * self.white_key_width
            y = 0
            
            # Determine fill color
            if note in self.active_notes:
                if self.sustain_pedal_active:
                    fill_color = self.sustain_color
                else:
                    fill_color = self.white_key_active_color
            else:
                fill_color = self.black_key_idle_color if self.dark_mode else self.white_key_idle_color
            
            # Draw white key
            r, g, b = self._hex_to_rgb(fill_color)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(x, y, self.white_key_width, self.white_key_height)
            cr.fill()
            
            # Draw separator line (except for last key)
            if idx < len(white_keys_list) - 1:
                separator_color = "#999999" if self.dark_mode else "#5C3F1F"
                sep_r, sep_g, sep_b = self._hex_to_rgb(separator_color)
                cr.set_source_rgb(sep_r, sep_g, sep_b)
                cr.set_line_width(1)
                line_x = x + self.white_key_width
                cr.move_to(line_x, 0)
                cr.line_to(line_x, self.white_key_height)
                cr.stroke()
        
        # Draw black keys on top
        for note in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1):
            if is_black_key(note):
                # Calculate position (same logic as before)
                octave = note // 12
                note_in_octave = note % 12
                
                white_keys_before = 0
                if octave == 1:
                    if note_in_octave == 10:  # A#0
                        white_keys_before = 0
                    else:
                        continue
                else:
                    white_keys_before = 2  # A0, B0
                    if octave >= 2:
                        octaves_before = octave - 2
                        white_keys_before += octaves_before * 7
                    
                    if note_in_octave == 1:   # C#
                        white_keys_before += 0
                    elif note_in_octave == 3:  # D#
                        white_keys_before += 1
                    elif note_in_octave == 6:  # F#
                        white_keys_before += 3
                    elif note_in_octave == 8:  # G#
                        white_keys_before += 4
                    elif note_in_octave == 10: # A#
                        white_keys_before += 5
                    else:
                        continue
                
                # Position black key between white keys
                white_keys_list = [n for n in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1) if is_white_key(n)]
                if white_keys_before < len(white_keys_list) and white_keys_before + 1 < len(white_keys_list):
                    white_key1_x = white_keys_before * self.white_key_width
                    white_key2_x = (white_keys_before + 1) * self.white_key_width
                    gap_center_x = (white_key1_x + self.white_key_width + white_key2_x) / 2
                    x = gap_center_x - self.black_key_width / 2
                else:
                    continue
                
                y = 0
                
                # Determine fill color
                if note in self.active_notes:
                    if self.sustain_pedal_active:
                        fill_color = self.sustain_color
                    else:
                        fill_color = self.black_key_active_color
                else:
                    fill_color = self.white_key_idle_color if self.dark_mode else self.black_key_idle_color
                
                # Draw black key
                r, g, b = self._hex_to_rgb(fill_color)
                cr.set_source_rgb(r, g, b)
                cr.rectangle(x, y, self.black_key_width, self.black_key_height)
                cr.fill()
                
                # Draw outline
                outline_color = "#CCCCCC" if self.dark_mode else "#8B7355"
                outline_r, outline_g, outline_b = self._hex_to_rgb(outline_color)
                cr.set_source_rgb(outline_r, outline_g, outline_b)
                cr.set_line_width(1)
                cr.rectangle(x, y, self.black_key_width, self.black_key_height)
                cr.stroke()

        # Restore context (undo translate/clip)
        cr.restore()

        # Chord text is now displayed in the chord_label widget above the piano, not drawn here

        return False
    
    def on_chord_label_draw(self, widget, cr):
        """Draw chord text directly using Cairo"""
        # Always fill black background first
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        # Get widget dimensions
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        print(f"DEBUG CHORD DRAW: Widget allocated size: {width}x{height}")

        if width <= 0 or height <= 0:
            return False

        # Don't display anything if no chord
        if not self.current_chord:
            return False

        # Determine text to display
        display_text = self.current_chord

        # Calculate font size based on height - scale text with available space
        # Use 60% of height for font size, with a minimum of 12px
        font_size = max(12, int(height * 0.6))
        print(f"DEBUG CHORD DRAW: Calculated font size: {font_size}")

        try:
            # Set up Pango layout for text rendering
            layout = PangoCairo.create_layout(cr)
            # Don't set width or alignment - we'll center manually

            # Set font - try Courier Prime first, fallback to monospace
            font_desc = Pango.FontDescription()
            font_desc.set_family("Courier Prime")
            font_desc.set_weight(Pango.Weight.NORMAL)
            font_desc.set_size(int(font_size * Pango.SCALE))
            layout.set_font_description(font_desc)

            # Set text
            layout.set_text(display_text, -1)

            # Check if text fits horizontally, if not reduce font size
            (text_width, text_height) = layout.get_pixel_size()
            if text_width > width * 0.95:  # Use 95% of width to leave margins
                # Scale font size down to fit width
                scale_factor = (width * 0.95) / text_width
                font_size = int(font_size * scale_factor)
                font_desc.set_size(int(font_size * Pango.SCALE))
                layout.set_font_description(font_desc)
                layout.set_text(display_text, -1)

            # Get text extents and center it manually
            (text_width, text_height) = layout.get_pixel_size()
            text_x = (width - text_width) / 2.0
            text_y = (height - text_height) / 2.0

            print(f"DEBUG CHORD DRAW: Text size: {text_width}x{text_height}, positioned at: {text_x}, {text_y}")

            # Draw text directly with ivory color
            cr.set_source_rgb(0.91, 0.86, 0.75)  # #E8DCC0
            cr.move_to(text_x, text_y)
            PangoCairo.show_layout(cr, layout)
        except Exception as e:
            # If font fails, try with system default monospace
            try:
                cr.set_source_rgb(0.91, 0.86, 0.75)  # #E8DCC0
                layout = PangoCairo.create_layout(cr)
                font_desc = Pango.FontDescription.from_string(f"monospace {font_size}")
                layout.set_font_description(font_desc)
                layout.set_text(display_text, -1)

                # Check if text fits horizontally, if not reduce font size
                (text_width, text_height) = layout.get_pixel_size()
                if text_width > width * 0.95:
                    scale_factor = (width * 0.95) / text_width
                    font_size = int(font_size * scale_factor)
                    font_desc = Pango.FontDescription.from_string(f"monospace {font_size}")
                    layout.set_font_description(font_desc)
                    layout.set_text(display_text, -1)

                (text_width, text_height) = layout.get_pixel_size()
                text_x = (width - text_width) / 2.0
                text_y = (height - text_height) / 2.0
                cr.move_to(text_x, text_y)
                PangoCairo.show_layout(cr, layout)
            except Exception as e2:
                print(f"Error drawing chord text: {e}, {e2}", file=sys.stderr)

        return False
    
    def on_chord_window_draw(self, widget, cr):
        """Draw chord text in detached window directly using Cairo"""
        # Always fill black background first
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        # Don't display anything if no chord
        if not self.current_chord:
            return False

        chord_text = self.current_chord

        # Get widget dimensions
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        if width <= 0 or height <= 0:
            return False

        # Calculate font size based on height - scale text with available space
        # Use 60% of height for font size, with a minimum of 12px
        font_size = max(12, int(height * 0.6))

        try:
            # Set up Pango layout for text rendering
            layout = PangoCairo.create_layout(cr)
            # Don't set width or alignment - we'll center manually

            # Set font - try Courier Prime first, fallback to monospace
            font_desc = Pango.FontDescription()
            font_desc.set_family("Courier Prime")
            font_desc.set_weight(Pango.Weight.NORMAL)
            font_desc.set_size(int(font_size * Pango.SCALE))
            layout.set_font_description(font_desc)

            # Set text - use plain text first to avoid markup issues
            layout.set_text(chord_text, -1)

            # Check if text fits horizontally, if not reduce font size
            (text_width, text_height) = layout.get_pixel_size()
            if text_width > width * 0.95:  # Use 95% of width to leave margins
                # Scale font size down to fit width
                scale_factor = (width * 0.95) / text_width
                font_size = int(font_size * scale_factor)
                font_desc.set_size(int(font_size * Pango.SCALE))
                layout.set_font_description(font_desc)
                layout.set_text(chord_text, -1)

            # Get text extents and center it manually
            (text_width, text_height) = layout.get_pixel_size()
            text_x = (width - text_width) / 2.0
            text_y = (height - text_height) / 2.0

            # Draw text directly with ivory color
            cr.set_source_rgb(0.91, 0.86, 0.75)  # #E8DCC0
            cr.move_to(text_x, text_y)
            PangoCairo.show_layout(cr, layout)
        except Exception as e:
            # If font fails, try with system default monospace
            try:
                cr.set_source_rgb(0.91, 0.86, 0.75)  # #E8DCC0
                layout = PangoCairo.create_layout(cr)
                font_desc = Pango.FontDescription.from_string(f"monospace {font_size}")
                layout.set_font_description(font_desc)
                layout.set_text(chord_text, -1)

                # Check if text fits horizontally, if not reduce font size
                (text_width, text_height) = layout.get_pixel_size()
                if text_width > width * 0.95:
                    scale_factor = (width * 0.95) / text_width
                    font_size = int(font_size * scale_factor)
                    font_desc = Pango.FontDescription.from_string(f"monospace {font_size}")
                    layout.set_font_description(font_desc)
                    layout.set_text(chord_text, -1)

                (text_width, text_height) = layout.get_pixel_size()
                text_x = (width - text_width) / 2
                text_y = (height - text_height) / 2
                cr.move_to(text_x, text_y)
                PangoCairo.show_layout(cr, layout)
            except Exception as e2:
                print(f"Error drawing chord window text: {e}, {e2}", file=sys.stderr)

        return False
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple (0-1 range for Cairo)"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        except:
            return (0, 0, 0)
    
    def midi_input_thread(self):
        """Thread to continuously read MIDI messages"""
        try:
            for msg in self.inport:
                if not self.midi_thread_running:
                    break
                
                self.message_count += 1
                current_time = time.time()
                
                # Handle note messages
                if msg.type == 'note_on' and msg.velocity > 0:
                    self.active_notes[msg.note] = {
                        'velocity': msg.velocity,
                        'time': current_time
                    }
                    # Remove from release queue if note is pressed again
                    self.notes_to_release.discard(msg.note)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if self.sustain_pedal_active:
                        # Sustain is active: mark note for release when sustain is released
                        if msg.note in self.active_notes:
                            self.notes_to_release.add(msg.note)
                    else:
                        # Sustain is not active: remove note immediately
                        if msg.note in self.active_notes:
                            del self.active_notes[msg.note]
                        self.notes_to_release.discard(msg.note)
                # Handle sustain pedal (CC 64)
                elif msg.type == 'control_change' and msg.control == 64:
                    was_active = self.sustain_pedal_active
                    self.sustain_pedal_active = (msg.value >= 64)  # Typically 64+ is on
                    
                    # If sustain pedal was released, remove notes that were marked for release
                    if was_active and not self.sustain_pedal_active:
                        # Release all notes that received note_off while sustain was active
                        for note in list(self.notes_to_release):
                            if note in self.active_notes:
                                del self.active_notes[note]
                        self.notes_to_release.clear()
        except Exception as e:
            pass  # Thread will exit when port closes
    
    def show_context_menu(self, widget, event):
        """Show right-click context menu - GTK3 version"""
        # Context menu is shown via on_button_press handler
        # This method is kept for compatibility but not used
        pass
    
    def toggle_dark_mode(self):
        """Toggle dark mode (invert key colors)"""
        self.dark_mode = not self.dark_mode
        
        # Update background color
        if self.dark_mode:
            self.bg_color = "#1a1a1a"  # Dark background
        else:
            self.bg_color = "#E8E8E8"  # Light background
        
        # Redraw keyboard
        if self.drawing_area:
            self.drawing_area.queue_draw()
        self.save_color_config()
        
        # Update menu to reflect new state
        self._create_context_menu()
    
    def pick_white_key_color(self):
        """Open color picker for white keys"""
        color = self.custom_color_picker("Choose White Key Color", self.white_key_idle_color)
        if color:
            self.white_key_idle_color = color
            if self.drawing_area:
                self.drawing_area.queue_draw()
            self.save_color_config()
    
    def pick_black_key_color(self):
        """Open color picker for black keys"""
        color = self.custom_color_picker("Choose Black Key Color", self.black_key_idle_color)
        if color:
            self.black_key_idle_color = color
            if self.drawing_area:
                self.drawing_area.queue_draw()
            self.save_color_config()
    
    def pick_active_key_color(self):
        """Open color picker for active keys (applies to both white and black)"""
        color = self.custom_color_picker("Choose Active Key Color", self.white_key_active_color)
        if color:
            self.white_key_active_color = color
            self.black_key_active_color = color
            if self.drawing_area:
                self.drawing_area.queue_draw()
            self.save_color_config()
    
    def pick_sustain_color(self):
        """Open color picker for sustain pedal color"""
        color = self.custom_color_picker("Choose Sustain Pedal Color", self.sustain_color)
        if color:
            self.sustain_color = color
            if self.drawing_area:
                self.drawing_area.queue_draw()
            self.save_color_config()
    
    def reset_settings(self):
        """Reset all color settings to defaults"""
        self.dark_mode = False
        self.white_key_idle_color = "#E8DCC0"
        self.black_key_idle_color = "#1a1a1a"
        self.white_key_active_color = "#6C9BD2"
        self.black_key_active_color = "#6C9BD2"
        self.sustain_color = "#D2A36C"
        
        # Update background color
        self.bg_color = "#E8E8E8"
        
        # Redraw keyboard
        if self.drawing_area:
            self.drawing_area.queue_draw()
        self.save_color_config()
    
    def toggle_chord_detection(self):
        """Toggle chord detection on/off"""
        if not CHORD_DETECTOR_AVAILABLE or not self.chord_detector:
            return

        self.chord_detection_enabled = not self.chord_detection_enabled

        if self.chord_detection_enabled:
            # Clear window lock when enabling chord detection
            self._window_locked_size = None
            print(f"DEBUG: Unlocking window (enabling chord detection)")

            # Show chord label in main window if not detached
            if not self.chord_window_detached and self.chord_label:
                # Reset chord label to default height
                self.chord_label.set_size_request(-1, self.chord_label_height)

                # Unlock the window to allow it to grow for chord label
                current_window_width, current_window_height = self.window.get_size()
                target_piano_height = int(current_window_width / self.piano_aspect)
                new_height = target_piano_height + self.chord_label_height

                print(f"DEBUG: Resizing window to add chord label, new height={new_height}")
                geom = Gdk.Geometry()
                geom.min_width = 200
                geom.min_height = new_height
                self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE)

                # Resize window to add chord label space
                self.window.resize(current_window_width, new_height)

                # Show the chord label and make it take space
                self.chord_label.set_no_show_all(False)
                self.chord_label.set_visible(True)
            # Create detached window if it was previously detached
            if self.chord_window_detached:
                self.create_chord_window()
            # Reset last min height so on_configure will update geometry constraints
            self._last_min_height = None
        else:
            # Disable chord detection - resize to piano-only size
            print(f"DEBUG: Disabling chord detection, resizing to piano-only")

            # Unlock window
            self._window_locked_size = None

            # Hide chord label completely
            if self.chord_label:
                self.chord_label.set_visible(False)
                self.chord_label.set_no_show_all(True)  # Remove from layout

            # Close detached window
            if self.chord_window:
                self.chord_window.destroy()
                self.chord_window = None

            # Resize window to piano-only size
            current_window_width = self.window.get_size()[0]
            target_piano_height = int(current_window_width / self.piano_aspect)

            # Set skip flag to prevent on_configure from interfering during resize
            self._skip_geometry_update = True
            print(f"DEBUG: Set _skip_geometry_update=True before resize")

            # Lock window at current width and set height to piano-only
            geom = Gdk.Geometry()
            geom.min_width = current_window_width
            geom.max_width = current_window_width
            geom.min_height = target_piano_height
            geom.max_height = target_piano_height
            self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
            self.window.resize(current_window_width, target_piano_height)
            print(f"DEBUG: Resized to piano-only: {current_window_width}x{target_piano_height}")

            # Reset last min height so on_configure will update geometry constraints
            self._last_min_height = None
            self.current_chord = None

        # Update menu
        self._create_context_menu()

        # Force window to process resize events
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Redraw
        if self.drawing_area:
            self.drawing_area.queue_draw()

    def toggle_flats_sharps(self):
        """Toggle between flat and sharp note names in chord detection"""
        if not CHORD_DETECTOR_AVAILABLE or not self.chord_detector:
            return

        # Toggle preference
        self.prefer_flats = not self.prefer_flats

        # Update chord detector
        self.chord_detector.set_note_preference(self.prefer_flats)

        # Save config
        self.save_color_config()

        # Update menu
        self._create_context_menu()

        # Re-detect current chord with new notation
        if self.chord_detection_enabled and self.active_notes:
            self.current_chord = self.chord_detector.detect_chord(self.active_notes)
            self.update_chord_display()

    def toggle_chord_window(self):
        """Toggle between attached and detached chord window"""
        if not self.chord_detection_enabled:
            return

        self.chord_window_detached = not self.chord_window_detached

        if self.chord_window_detached:
            # Detach: Create separate window
            # Clear any previous window lock
            self._window_locked_size = None

            # Prevent on_configure from updating geometry during this operation
            self._skip_geometry_update = True

            # Calculate proper piano height based on current window width and aspect ratio
            current_window_width, current_window_height = self.window.get_size()
            print(f"DEBUG DETACH: Current window size: {current_window_width}x{current_window_height}")
            print(f"DEBUG DETACH: Piano viewport: {self.piano_width}x{self.piano_height}")
            print(f"DEBUG DETACH: Piano aspect ratio: {self.piano_aspect}")
            print(f"DEBUG DETACH: Drawing area allocated: {self.drawing_area.get_allocated_width()}x{self.drawing_area.get_allocated_height()}")

            # Use the piano viewport width/height that's already calculated in on_configure
            # to maintain the exact same piano dimensions
            target_piano_height = int(self.piano_width / self.piano_aspect)
            print(f"DEBUG DETACH: Calculated target piano height: {target_piano_height}")

            # Calculate chord window height - include any extra vertical space user added by resizing
            min_total_height = target_piano_height + self.chord_label_height
            extra_space = max(0, current_window_height - min_total_height)
            chord_window_height = self.chord_label_height + extra_space
            print(f"DEBUG DETACH: Chord window height (including extra space): {chord_window_height}")

            # Create chord window with calculated height
            self.create_chord_window(height=chord_window_height)

            if self.chord_label:
                self.chord_label.set_visible(False)
                # Hide the chord label completely to remove its space
                self.chord_label.set_no_show_all(True)

            # Set geometry constraints FIRST to allow the resize
            # Lock both width and height to current size when detached
            geom = Gdk.Geometry()
            geom.min_width = current_window_width
            geom.max_width = current_window_width
            geom.min_height = target_piano_height
            geom.max_height = target_piano_height
            print(f"DEBUG DETACH: Setting geometry to lock window, width={current_window_width}, height={target_piano_height}")
            self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
            self._last_min_height = target_piano_height

            # Now resize window to maintain the same piano size
            print(f"DEBUG DETACH: Calling resize to: {current_window_width}x{target_piano_height}")
            self.window.resize(current_window_width, target_piano_height)

            # Check what happened after resize
            new_width, new_height = self.window.get_size()
            print(f"DEBUG DETACH: After resize, window size is: {new_width}x{new_height}")
        else:
            # Attach: Show in main window, close separate window
            # Clear any window lock
            self._window_locked_size = None

            # Prevent on_configure from updating geometry during this operation
            self._skip_geometry_update = True

            # Get chord window height before destroying it
            chord_window_height = self.chord_label_height  # Default
            if self.chord_window:
                _, chord_window_height = self.chord_window.get_size()
                print(f"DEBUG ATTACH: Chord window height was: {chord_window_height}")
                self.chord_window.destroy()
                self.chord_window = None

            # Re-enable chord detection when reattaching (AFTER destroying window to avoid close handler interfering)
            if not self.chord_detection_enabled:
                print(f"DEBUG ATTACH: Re-enabling chord detection after window destroy")
                self.chord_detection_enabled = True

            # Calculate proper piano height based on current piano viewport
            current_window_width, current_piano_height = self.window.get_size()
            target_piano_height = int(self.piano_width / self.piano_aspect)

            print(f"DEBUG ATTACH: Before attach - piano viewport: {self.piano_width}x{self.piano_height}")
            print(f"DEBUG ATTACH: Current piano window: {current_window_width}x{current_piano_height}")

            if self.chord_label:
                # Set chord label height to match what the chord window was
                # This ensures no black space at bottom
                self.chord_label.set_size_request(-1, chord_window_height)
                print(f"DEBUG ATTACH: Setting chord label height to: {chord_window_height}")

                # Show the chord label and make it take space
                self.chord_label.set_no_show_all(False)
                self.chord_label.set_visible(True)

            # Set geometry constraints FIRST to allow the resize (no max height - allow vertical resizing)
            # Use the chord window height we captured to maintain total window size
            new_height = target_piano_height + chord_window_height
            geom = Gdk.Geometry()
            geom.min_width = 200
            geom.min_height = new_height
            self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE)
            self._last_min_height = new_height

            # Now resize window to add chord label space
            self.window.resize(current_window_width, new_height)
            print(f"DEBUG ATTACH: Attaching - total height (piano {target_piano_height} + chord {chord_window_height}): {current_window_width}x{new_height}")

        # Force layout update to prevent extra space
        if self.window:
            self.window.queue_resize()

        # Note: _skip_geometry_update flag will be auto-reset by on_configure
        # when window stabilizes at width >= 800px

        # Update menu
        self._create_context_menu()

        # Redraw
        if self.drawing_area:
            self.drawing_area.queue_draw()
    
    def create_chord_window(self, height=None):
        """Create a separate window for chord display

        Args:
            height: Optional height for the chord window. If not provided, uses chord_label height.
        """
        if self.chord_window:
            return

        self.chord_window = Gtk.Window()
        self.chord_window.set_title("Chord Detection")

        # Get main window width
        main_window_width = self.window.get_size()[0]
        chord_win_width = main_window_width

        # Use provided height or get from chord label
        if height is not None:
            chord_win_height = max(height, 50)  # Minimum 50px
            print(f"DEBUG: Creating detached chord window with provided height: {chord_win_width}x{chord_win_height}")
        elif self.chord_label:
            current_chord_height = self.chord_label.get_allocated_height()
            # If chord label hasn't been allocated yet, use the size request
            if current_chord_height <= 1:
                _, current_chord_height = self.chord_label.get_size_request()
            chord_win_height = max(current_chord_height, 50)  # Minimum 50px
            print(f"DEBUG: Creating detached chord window with chord_label height: {chord_win_width}x{chord_win_height}")
        else:
            # Fallback to default size
            chord_win_height = 50

        self.chord_window.set_default_size(chord_win_width, chord_win_height)
        self.chord_window.set_resizable(True)  # Make resizable with locked aspect ratio
        self.chord_window.set_decorated(True)

        # Set aspect ratio to lock it while keeping window resizable
        chord_aspect_ratio = chord_win_width / chord_win_height
        geom = Gdk.Geometry()
        geom.min_aspect = chord_aspect_ratio
        geom.max_aspect = chord_aspect_ratio

        # Set minimum and maximum size constraints
        geom.min_width = 200
        geom.min_height = int(200 / chord_aspect_ratio)
        geom.max_width = 1000
        geom.max_height = int(1000 / chord_aspect_ratio)

        # Combine all hints
        hints = (Gdk.WindowHints.ASPECT |
                Gdk.WindowHints.MIN_SIZE |
                Gdk.WindowHints.MAX_SIZE)

        # Pass the chord window itself, not None
        self.chord_window.set_geometry_hints(self.chord_window, geom, hints)
        
        # Set window background to black and remove padding
        css_provider_window = Gtk.CssProvider()
        css_provider_window.load_from_data(b"""
            window {
                background-color: #000000;
                margin: 0;
                padding: 0;
            }
        """)
        style_context_window = self.chord_window.get_style_context()
        style_context_window.add_provider(css_provider_window, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Create DrawingArea for chord display with pixelated Cairo rendering
        chord_display_area = Gtk.DrawingArea()
        chord_display_area.set_name("chord-display-label")
        # Remove all margins - we'll handle spacing in the draw function
        chord_display_area.set_margin_top(0)
        chord_display_area.set_margin_bottom(0)
        chord_display_area.set_margin_start(0)
        chord_display_area.set_margin_end(0)

        # Set explicit size request to fill the window - will expand with window
        chord_display_area.set_size_request(chord_win_width, chord_win_height)
        chord_display_area.set_hexpand(True)
        chord_display_area.set_vexpand(True)

        # Set black background via CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            #chord-display-label {
                background-color: #000000;
            }
        """)
        style_context = chord_display_area.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Ensure DrawingArea is set to draw - required for custom Cairo rendering
        chord_display_area.set_app_paintable(True)
        # Connect draw handler for custom Cairo rendering (must be after set_app_paintable)
        chord_display_area.connect("draw", self.on_chord_window_draw)
        # Enable button events for right-click menu
        chord_display_area.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        chord_display_area.connect("button-press-event", self.on_chord_label_button_press)
        # Force initial draw
        chord_display_area.queue_draw()

        # Store reference to update it
        self.chord_display_label = chord_display_area
        
        # Add to window - use expand=False to prevent extra space
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(0)
        box.set_margin_bottom(0)
        box.set_margin_start(0)
        box.set_margin_end(0)
        box.pack_start(chord_display_area, False, False, 0)
        self.chord_window.add(box)
        self.chord_window.set_border_width(0)
        
        # Connect destroy event - disable chord detection when detached window is closed
        def on_chord_window_close(widget):
            print("DEBUG: Chord window closed - disabling chord detection")
            self.chord_window = None
            self.chord_window_detached = False
            # Disable chord detection properly (will resize to piano-only)
            if self.chord_detection_enabled:
                print("DEBUG: Chord detection was enabled, toggling to disable")
                self.chord_detection_enabled = False

                # Unlock window
                self._window_locked_size = None

                # Hide chord label completely
                if self.chord_label:
                    self.chord_label.set_visible(False)
                    self.chord_label.set_no_show_all(True)

                # Resize window to piano-only size
                current_window_width = self.window.get_size()[0]
                target_piano_height = int(current_window_width / self.piano_aspect)

                # Set skip flag to prevent on_configure from interfering during resize
                self._skip_geometry_update = True
                print(f"DEBUG: Set _skip_geometry_update=True before resize")

                # Lock window at current width and set height to piano-only
                geom = Gdk.Geometry()
                geom.min_width = current_window_width
                geom.max_width = current_window_width
                geom.min_height = target_piano_height
                geom.max_height = target_piano_height
                self.window.set_geometry_hints(None, geom, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
                self.window.resize(current_window_width, target_piano_height)
                print(f"DEBUG: Resized to piano-only: {current_window_width}x{target_piano_height}")

                # Reset last min height so it will update geometry on next stable configure
                self._last_min_height = None
                self.current_chord = None

                # Update menu
                self._create_context_menu()
                print("DEBUG: Menu updated, chord_detection_enabled =", self.chord_detection_enabled)

        self.chord_window.connect("destroy", on_chord_window_close)
        
        self.chord_window.show_all()
    
    def update_chord_detection(self):
        """Update chord detection - called by timer"""
        if not self.chord_detection_enabled or not self.chord_detector:
            return True  # Continue timer
        
        # Get active note numbers
        active_note_numbers = set(self.active_notes.keys())
        
        if len(active_note_numbers) >= 2:
            # Find lowest note for inversion detection
            lowest_note = min(active_note_numbers) if active_note_numbers else None
            
            # Detect chord
            detected_chord = self.chord_detector.detect_chord(active_note_numbers, lowest_note)
            self.current_chord = detected_chord
        else:
            self.current_chord = None
        
        # Update display (chord_text not needed - drawing functions handle None)

        # Update main window label
        if self.chord_label and not self.chord_window_detached:
            # Trigger redraw for DrawingArea
            if self.chord_label.get_visible():
                self.chord_label.queue_draw()
        
        # Update detached window label
        if self.chord_window_detached and hasattr(self, 'chord_display_label'):
            # Trigger redraw for DrawingArea
            self.chord_display_label.queue_draw()
        
        # Redraw main window to show chord overlay
        if self.drawing_area and not self.chord_window_detached:
            self.drawing_area.queue_draw()
        
        return True  # Continue timer
    
    def select_midi_input(self):
        """Show dialog to select MIDI input port"""
        if not self.window:
            return
        
        global mido
        mido, _ = check_dependencies()
        
        # Get available MIDI ports
        try:
            input_ports = mido.get_input_names()
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format=f"Error getting MIDI ports: {e}"
            )
            error_dialog.run()
            error_dialog.destroy()
            return
        
        if not input_ports:
            error_dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="No MIDI input ports found!"
            )
            error_dialog.run()
            error_dialog.destroy()
            return
        
        # Create dialog
        dialog = Gtk.Dialog(title="Select MIDI Input", parent=self.window, modal=True)
        dialog.set_default_size(400, 300)
        dialog.set_transient_for(self.window)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(15)
        content_area.set_margin_bottom(15)
        content_area.set_margin_start(15)
        content_area.set_margin_end(15)
        
        # Label
        label = Gtk.Label(label="Select MIDI input port:")
        label.set_halign(Gtk.Align.START)
        content_area.pack_start(label, False, False, 0)
        
        # Current port label
        current_label = Gtk.Label()
        current_port = getattr(self, 'actual_port_name', 'None')
        current_label.set_markup(f"<i>Current: {current_port}</i>")
        current_label.set_halign(Gtk.Align.START)
        content_area.pack_start(current_label, False, False, 0)
        
        # Scrolled window for port list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        # List store and tree view
        list_store = Gtk.ListStore(str)
        tree_view = Gtk.TreeView(model=list_store)
        tree_view.set_headers_visible(False)
        tree_view.set_activate_on_single_click(True)
        
        # Port column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Port", renderer, text=0)
        tree_view.append_column(column)
        
        # Populate list
        selected_iter = None
        for port in input_ports:
            iter = list_store.append([port])
            if port == current_port:
                selected_iter = iter
        
        scrolled.add(tree_view)
        content_area.pack_start(scrolled, True, True, 0)
        
        # Select current port if available
        if selected_iter:
            selection = tree_view.get_selection()
            selection.select_iter(selected_iter)
            tree_view.scroll_to_cell(list_store.get_path(selected_iter), None, False, 0, 0)
        
        # Buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("OK", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        # Show dialog
        dialog.show_all()
        
        # Handle double-click
        def on_row_activated(view, path, column):
            dialog.response(Gtk.ResponseType.OK)
        tree_view.connect("row-activated", on_row_activated)
        
        response = dialog.run()
        
        selected_port = None
        if response == Gtk.ResponseType.OK:
            selection = tree_view.get_selection()
            model, iter = selection.get_selected()
            if iter:
                selected_port = model[iter][0]
        
        dialog.destroy()
        
        # Switch to selected port
        if selected_port and selected_port != current_port:
            self.switch_midi_port(selected_port)
    
    def switch_midi_port(self, port_name):
        """Switch to a different MIDI input port"""
        try:
            # Stop current MIDI thread
            self.midi_thread_running = False
            
            # Close current port
            if hasattr(self, 'inport') and self.inport:
                try:
                    self.inport.close()
                except:
                    pass
            
            # Wait a bit for thread to stop
            if hasattr(self, 'midi_thread') and self.midi_thread:
                self.midi_thread.join(timeout=1.0)
            
            # Clear active notes
            self.active_notes.clear()
            self.notes_to_release.clear()
            self.sustain_pedal_active = False
            
            # Open new port
            global mido
            mido, _ = check_dependencies()
            self.inport = mido.open_input(port_name)
            self.actual_port_name = port_name
            
            # Restart MIDI thread
            self.midi_thread_running = True
            self.midi_thread = threading.Thread(target=self.midi_input_thread, daemon=True)
            self.midi_thread.start()
            
            # Redraw to clear any active notes
            if self.drawing_area:
                self.drawing_area.queue_draw()
                
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format=f"Error switching to MIDI port '{port_name}': {e}"
            )
            error_dialog.run()
            error_dialog.destroy()
    
    def update_gui(self):
        """Update GUI display - GTK3 version"""
        # Only queue redraw if window and drawing area exist and are visible
        if self.window and self.drawing_area and self.window.get_visible():
            try:
                self.drawing_area.queue_draw()
            except:
                # If there's an error, stop the timer
                return False
        
        # Return True to continue timer
        return True
    
    def add_message_to_log(self, msg: Message, current_time: float):
        """Add message to GUI log (not used in keyboard-only mode)"""
        # This function is kept for compatibility but not used when showing only keyboard
        pass
    
    def format_message(self, msg: Message) -> str:
        """Format MIDI message for display"""
        if msg.type == 'note_on' and msg.velocity > 0:
            note_info = note_name(msg.note)
            return f"{Colors.GREEN}NOTE ON {Colors.RESET} {note_info:4s} (note={msg.note:3d}) velocity={msg.velocity:3d}"
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            note_info = note_name(msg.note)
            return f"{Colors.RED}NOTE OFF{Colors.RESET} {note_info:4s} (note={msg.note:3d})"
        elif msg.type == 'control_change':
            return f"{Colors.CYAN}CC {msg.control:3d}{Colors.RESET} = {msg.value:3d}"
        elif msg.type == 'program_change':
            return f"{Colors.MAGENTA}PROGRAM{Colors.RESET} {msg.program}"
        elif msg.type == 'pitchwheel':
            return f"{Colors.YELLOW}PITCHWHEEL{Colors.RESET} {msg.pitch}"
        elif msg.type == 'aftertouch':
            return f"{Colors.BLUE}AFTERTOUCH{Colors.RESET} {msg.value}"
        else:
            return f"{Colors.WHITE}{msg.type}{Colors.RESET} {msg.dict()}"
    
    def run(self, argv=None):
        """Run GTK application - single-instance is handled by Gtk.Application"""
        # Gtk.Application handles single-instance automatically
        return super().run(argv if argv else sys.argv)

# Single-instance is now handled automatically by Gtk.Application via application_id

def main():
    parser = argparse.ArgumentParser(
        description="GUI-based MIDI monitor with full 88-key keyboard visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use default MIDI input port
  %(prog)s -p "USB-MIDI MIDI 1"  # Use specific port
  %(prog)s -l                 # List available ports
  %(prog)s --colors ~/.config/my-colors.json  # Use custom color config

Color Configuration:
  Colors are stored in ~/.config/midi-monitor-colors.json
  You can customize:
    - white_key_idle, white_key_active_low/med/high
    - black_key_idle, black_key_active_low/med/high
    - velocity_threshold_low (default: 64)
    - velocity_threshold_high (default: 100)
        """
    )
    
    parser.add_argument('-p', '--port', type=str, help='MIDI input port name')
    parser.add_argument('-l', '--list', action='store_true', help='List available MIDI ports')
    parser.add_argument('--colors', type=str, help='Path to color configuration file')
    
    args = parser.parse_args()
    
    # List ports if requested
    if args.list:
        mido, _ = check_dependencies()
        print("Available MIDI Input Ports:")
        ports = mido.get_input_names()
        if ports:
            for i, port in enumerate(ports):
                print(f"  {i}: {port}")
        else:
            print("  No MIDI input ports found!")
        return
    
    # Load color config
    color_config = ColorConfig(args.colors)
    
    # Create and run monitor (always GUI mode)
    # GTK Application handles single-instance automatically via application_id
    monitor = MIDIMonitor(port_name=args.port, color_config=color_config)
    monitor.run()

if __name__ == '__main__':
    main()














































