#!/usr/bin/env python3
"""
PyQt5 version of Ivory - MIDI Keyboard Monitor with Chord Detection
Windows-compatible version using PyQt5 instead of GTK3
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

# PyQt5 imports
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                  QMenu, QMessageBox, QDialog, QLabel, QListWidget,
                                  QDialogButtonBox, QColorDialog, QLineEdit, QPushButton,
                                  QHBoxLayout, QFrame)
    from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QSharedMemory, QSystemSemaphore
    from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush, QIcon
    PYQT5_AVAILABLE = True
except ImportError as e:
    print(f"Error: PyQt5 is required. Install with:")
    print(f"  pip install PyQt5")
    print(f"Import error: {e}")
    sys.exit(1)

# Check for dependencies only when actually needed
def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import mido
        from mido import Message
    except ImportError:
        print("Error: mido library not found. Install it with:")
        print("  pip install mido python-rtmidi")
        sys.exit(1)
    
    return mido, Message

# Import mido only when needed
mido = None
Message = None

# MIDI note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Standard 88-key piano: A0 (21) to C8 (108)
KEYBOARD_START_NOTE = 21  # A0
KEYBOARD_END_NOTE = 108   # C8
KEYBOARD_TOTAL_KEYS = 88

def note_name(note_number: int) -> str:
    """Convert MIDI note number to name (e.g., 60 -> 'C4')"""
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
    
    octave = note_number // 12
    note_in_octave = note_number % 12
    
    if octave == 1:  # A0-B0
        if note_in_octave == 9:  # A
            return 0
        elif note_in_octave == 11:  # B
            return 1
        else:
            return -1
    
    white_keys_before = 2  # A0, B0
    if octave >= 2:
        octaves_before = octave - 2
        white_keys_before += octaves_before * 7
    
    white_key_map = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
    white_keys_before += white_key_map[note_in_octave]
    
    return white_keys_before

def get_black_key_position(note_number: int) -> Tuple[int, int]:
    """Get position of black key: (octave_offset, key_in_octave)"""
    if not is_black_key(note_number):
        return (-1, -1)
    
    octave = note_number // 12
    note_in_octave = note_number % 12
    
    black_key_map = {1: 0, 3: 1, 6: 2, 8: 3, 10: 4}
    return (octave, black_key_map[note_in_octave])


class PianoWidget(QWidget):
    """Widget for drawing the piano keyboard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes: Dict[int, Dict] = {}
        self.sustain_pedal_active = False
        
        # Color settings
        self.dark_mode = False
        self.white_key_idle_color = QColor(232, 220, 192)  # #E8DCC0
        self.black_key_idle_color = QColor(26, 26, 26)  # #1a1a1a
        self.white_key_active_color = QColor(108, 155, 210)  # #6C9BD2
        self.black_key_active_color = QColor(108, 155, 210)  # #6C9BD2
        self.sustain_color = QColor(210, 163, 108)  # #D2A36C
        self.bg_color = QColor(232, 232, 232)  # #E8E8E8
        
        # Piano dimensions
        self.piano_aspect = 1300 / 150  # ~8.67:1
        self.white_key_width = 0
        self.white_key_height = 0
        self.black_key_width = 0
        self.black_key_height = 0
        
        # Set minimum size
        self.setMinimumSize(200, 50)
        
        # Enable mouse tracking for context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def set_active_notes(self, notes: Dict[int, Dict]):
        """Update active notes"""
        self.active_notes = notes
        self.update()
    
    def set_sustain_pedal(self, active: bool):
        """Update sustain pedal state"""
        self.sustain_pedal_active = active
        self.update()
    
    def set_colors(self, dark_mode=None, white_idle=None, black_idle=None,
                   white_active=None, black_active=None, sustain=None, bg=None):
        """Update color settings"""
        if dark_mode is not None:
            self.dark_mode = dark_mode
        if white_idle is not None:
            self.white_key_idle_color = white_idle
        if black_idle is not None:
            self.black_key_idle_color = black_idle
        if white_active is not None:
            self.white_key_active_color = white_active
        if black_active is not None:
            self.black_key_active_color = black_active
        if sustain is not None:
            self.sustain_color = sustain
        if bg is not None:
            self.bg_color = bg
        self.update()
    
    def show_context_menu(self, pos: QPoint):
        """Show context menu"""
        # This will be handled by the main window
        pass
    
    def paintEvent(self, event):
        """Draw the piano keyboard"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fill background
        painter.fillRect(0, 0, width, height, self.bg_color)
        
        # Calculate piano dimensions to maintain aspect ratio
        piano_width = width
        piano_height = piano_width / self.piano_aspect
        
        # Center vertically if needed
        piano_y = (height - piano_height) / 2 if height > piano_height else 0
        
        # Calculate key dimensions
        white_keys_count = 52
        self.white_key_width = piano_width / white_keys_count
        self.white_key_height = piano_height
        self.black_key_width = self.white_key_width * 0.7
        self.black_key_height = self.white_key_height * 0.65
        
        # Translate to piano position
        painter.translate(0, piano_y)
        
        # Draw white keys
        white_keys_list = [n for n in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1) 
                          if is_white_key(n)]
        
        for idx, note in enumerate(white_keys_list):
            x = idx * self.white_key_width
            
            # Determine fill color
            if note in self.active_notes:
                if self.sustain_pedal_active:
                    fill_color = self.sustain_color
                else:
                    fill_color = self.white_key_active_color
            else:
                fill_color = self.black_key_idle_color if self.dark_mode else self.white_key_idle_color
            
            # Draw white key
            painter.fillRect(int(x), 0, int(self.white_key_width), int(self.white_key_height), fill_color)
            
            # Draw separator line (except for last key)
            if idx < len(white_keys_list) - 1:
                separator_color = QColor(153, 153, 153) if self.dark_mode else QColor(92, 63, 31)
                painter.setPen(QPen(separator_color, 1))
                line_x = int(x + self.white_key_width)
                painter.drawLine(line_x, 0, line_x, int(self.white_key_height))
        
        # Draw black keys on top
        for note in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1):
            if is_black_key(note):
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
                if white_keys_before < len(white_keys_list) and white_keys_before + 1 < len(white_keys_list):
                    white_key1_x = white_keys_before * self.white_key_width
                    white_key2_x = (white_keys_before + 1) * self.white_key_width
                    gap_center_x = (white_key1_x + self.white_key_width + white_key2_x) / 2
                    x = gap_center_x - self.black_key_width / 2
                else:
                    continue
                
                # Determine fill color
                if note in self.active_notes:
                    if self.sustain_pedal_active:
                        fill_color = self.sustain_color
                    else:
                        fill_color = self.black_key_active_color
                else:
                    fill_color = self.white_key_idle_color if self.dark_mode else self.black_key_idle_color
                
                # Draw black key
                painter.fillRect(int(x), 0, int(self.black_key_width), int(self.black_key_height), fill_color)
                
                # Draw outline
                outline_color = QColor(204, 204, 204) if self.dark_mode else QColor(139, 115, 85)
                painter.setPen(QPen(outline_color, 1))
                painter.drawRect(int(x), 0, int(self.black_key_width), int(self.black_key_height))


class ChordLabelWidget(QWidget):
    """Widget for displaying chord names"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_chord = None
        self.setMinimumHeight(50)
        self.setMaximumHeight(200)
        
        # Enable mouse tracking for context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def set_chord(self, chord: Optional[str]):
        """Update chord text"""
        self.current_chord = chord
        self.update()
    
    def show_context_menu(self, pos: QPoint):
        """Show context menu"""
        # This will be handled by the main window
        pass
    
    def paintEvent(self, event):
        """Draw chord text"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill black background
        painter.fillRect(0, 0, self.width(), self.height(), QColor(0, 0, 0))
        
        if not self.current_chord:
            return
        
        # Calculate font size based on height
        font_size = max(12, int(self.height() * 0.6))
        
        # Set font - try Courier Prime first, fallback to monospace
        font = QFont("Courier Prime", font_size, QFont.Bold)
        if not font.exactMatch():
            font = QFont("Courier", font_size, QFont.Bold)
        if not font.exactMatch():
            font = QFont("monospace", font_size, QFont.Bold)
        
        painter.setFont(font)
        painter.setPen(QColor(232, 220, 192))  # #E8DCC0
        
        # Measure text
        metrics = QFontMetrics(font)
        # Use boundingRect for width (width() is deprecated)
        text_rect = metrics.boundingRect(self.current_chord)
        text_width = text_rect.width()
        text_height = text_rect.height()
        
        # Scale font if too wide
        if text_width > self.width() * 0.95:
            scale_factor = (self.width() * 0.95) / text_width
            font_size = int(font_size * scale_factor)
            font.setPointSize(font_size)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_rect = metrics.boundingRect(self.current_chord)
            text_width = text_rect.width()
            text_height = text_rect.height()
        
        # Center text
        text_x = (self.width() - text_width) / 2
        text_y = (self.height() + text_height) / 2 - metrics.descent()
        
        painter.drawText(int(text_x), int(text_y), self.current_chord)


class MIDIMonitor(QMainWindow):
    """Main application window"""
    
    def __init__(self, port_name: Optional[str] = None):
        super().__init__()
        
        self.port_name = port_name
        self.active_notes: Dict[int, Dict] = {}
        self.notes_to_release: set = set()
        self.sustain_pedal_active = False
        self.midi_thread_running = False
        self.inport = None
        self.actual_port_name = None
        
        # Chord detection
        self.chord_detection_enabled = True if CHORD_DETECTOR_AVAILABLE else False
        self.chord_window_detached = False
        self.chord_window = None
        self.current_chord = None
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_detector = ChordDetector()
        else:
            self.chord_detector = None
        
        # Settings
        self.config_file = Path.home() / ".config" / "ivory" / "settings.json"
        self.load_settings()
        
        # Update chord detector preferences
        if self.chord_detector:
            self.chord_detector.set_note_preference(self.prefer_flats)
        
        # Initialize UI
        self.init_ui()
        
        # Connect MIDI
        self.connect_midi()
        
        # Start update timers
        if CHORD_DETECTOR_AVAILABLE and self.chord_detector:
            self.chord_timer = QTimer()
            self.chord_timer.timeout.connect(self.update_chord_detection)
            self.chord_timer.start(100)  # Update every 100ms
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gui)
        self.update_timer.start(50)  # Update every 50ms
    
    def load_settings(self):
        """Load settings from file"""
        defaults = {
            "dark_mode": False,
            "white_key_idle_color": "#E8DCC0",
            "black_key_idle_color": "#1a1a1a",
            "white_key_active_color": "#6C9BD2",
            "black_key_active_color": "#6C9BD2",
            "sustain_color": "#D2A36C",
            "prefer_flats": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.dark_mode = config.get("dark_mode", defaults["dark_mode"])
                    self.white_key_idle_color = QColor(config.get("white_key_idle_color", defaults["white_key_idle_color"]))
                    self.black_key_idle_color = QColor(config.get("black_key_idle_color", defaults["black_key_idle_color"]))
                    self.white_key_active_color = QColor(config.get("white_key_active_color", defaults["white_key_active_color"]))
                    self.black_key_active_color = QColor(config.get("black_key_active_color", defaults["black_key_active_color"]))
                    self.sustain_color = QColor(config.get("sustain_color", defaults["sustain_color"]))
                    self.prefer_flats = config.get("prefer_flats", defaults["prefer_flats"])
            except Exception:
                # Use defaults on error
                self.dark_mode = defaults["dark_mode"]
                self.white_key_idle_color = QColor(defaults["white_key_idle_color"])
                self.black_key_idle_color = QColor(defaults["black_key_idle_color"])
                self.white_key_active_color = QColor(defaults["white_key_active_color"])
                self.black_key_active_color = QColor(defaults["black_key_active_color"])
                self.sustain_color = QColor(defaults["sustain_color"])
                self.prefer_flats = defaults["prefer_flats"]
        else:
            # Use defaults
            self.dark_mode = defaults["dark_mode"]
            self.white_key_idle_color = QColor(defaults["white_key_idle_color"])
            self.black_key_idle_color = QColor(defaults["black_key_idle_color"])
            self.white_key_active_color = QColor(defaults["white_key_active_color"])
            self.black_key_active_color = QColor(defaults["black_key_active_color"])
            self.sustain_color = QColor(defaults["sustain_color"])
            self.prefer_flats = defaults["prefer_flats"]
    
    def save_settings(self):
        """Save settings to file"""
        config = {
            "dark_mode": self.dark_mode,
            "white_key_idle_color": self.white_key_idle_color.name(),
            "black_key_idle_color": self.black_key_idle_color.name(),
            "white_key_active_color": self.white_key_active_color.name(),
            "black_key_active_color": self.black_key_active_color.name(),
            "sustain_color": self.sustain_color.name(),
            "prefer_flats": self.prefer_flats
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Ivory - MIDI Keyboard Monitor")
        self.setMinimumSize(200, 150)
        
        # Try to set window icon if available
        icon_path = Path(__file__).parent / "icons" / "ivory.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central_widget.setLayout(layout)
        
        # Create chord label (if available)
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_label = ChordLabelWidget()
            self.chord_label.set_chord(None)
            self.chord_label.setVisible(self.chord_detection_enabled)
            layout.addWidget(self.chord_label)
        
        # Create piano widget
        self.piano_widget = PianoWidget()
        layout.addWidget(self.piano_widget)
        
        # Update piano colors
        self.update_piano_colors()
        
        # Set default size
        self.resize(1300, 200)
    
    def update_piano_colors(self):
        """Update piano widget colors"""
        bg_color = QColor(26, 26, 26) if self.dark_mode else QColor(232, 232, 232)
        self.piano_widget.set_colors(
            dark_mode=self.dark_mode,
            white_idle=self.white_key_idle_color,
            black_idle=self.black_key_idle_color,
            white_active=self.white_key_active_color,
            black_active=self.black_key_active_color,
            sustain=self.sustain_color,
            bg=bg_color
        )
    
    def connect_midi(self):
        """Connect to MIDI input"""
        mido, _ = check_dependencies()
        
        # Get available ports
        input_ports = mido.get_input_names()
        
        if not input_ports:
            QMessageBox.critical(self, "No MIDI Input", 
                                "No MIDI input ports found!\n\nPlease connect a MIDI device.")
            sys.exit(1)
        
        # Select port
        port = self.port_name
        if not port:
            # Auto-select: prefer USB-MIDI, then Scarlett, then first available
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
            self.actual_port_name = port
        except Exception as e:
            QMessageBox.critical(self, "MIDI Error", 
                                f"Error opening MIDI port:\n{e}")
            sys.exit(1)
        
        # Start MIDI input thread
        self.midi_thread_running = True
        self.midi_thread = threading.Thread(target=self.midi_input_thread, daemon=True)
        self.midi_thread.start()
    
    def midi_input_thread(self):
        """Thread to continuously read MIDI messages"""
        try:
            for msg in self.inport:
                if not self.midi_thread_running:
                    break
                
                current_time = time.time()
                
                # Handle note messages
                if msg.type == 'note_on' and msg.velocity > 0:
                    self.active_notes[msg.note] = {
                        'velocity': msg.velocity,
                        'time': current_time
                    }
                    self.notes_to_release.discard(msg.note)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if self.sustain_pedal_active:
                        if msg.note in self.active_notes:
                            self.notes_to_release.add(msg.note)
                    else:
                        if msg.note in self.active_notes:
                            del self.active_notes[msg.note]
                        self.notes_to_release.discard(msg.note)
                # Handle sustain pedal (CC 64)
                elif msg.type == 'control_change' and msg.control == 64:
                    was_active = self.sustain_pedal_active
                    self.sustain_pedal_active = (msg.value >= 64)
                    
                    if was_active and not self.sustain_pedal_active:
                        for note in list(self.notes_to_release):
                            if note in self.active_notes:
                                del self.active_notes[note]
                        self.notes_to_release.clear()
        except Exception:
            pass  # Thread will exit when port closes
    
    def update_gui(self):
        """Update GUI elements"""
        # Update piano widget
        self.piano_widget.set_active_notes(self.active_notes)
        self.piano_widget.set_sustain_pedal(self.sustain_pedal_active)
    
    def update_chord_detection(self):
        """Update chord detection"""
        if not self.chord_detection_enabled or not self.chord_detector:
            return
        
        if not self.active_notes:
            self.current_chord = None
            if CHORD_DETECTOR_AVAILABLE:
                self.chord_label.set_chord(None)
            if self.chord_window:
                self.chord_window.chord_label.set_chord(None)
            return
        
        # Get active note numbers
        active_note_numbers = set(self.active_notes.keys())
        
        # Detect chord
        chord = self.chord_detector.detect_chord(active_note_numbers)
        self.current_chord = chord
        
        # Update displays
        if CHORD_DETECTOR_AVAILABLE and not self.chord_window_detached:
            self.chord_label.set_chord(chord)
        if self.chord_window:
            self.chord_window.chord_label.set_chord(chord)
    
    def contextMenuEvent(self, event):
        """Handle context menu"""
        menu = QMenu(self)
        
        # MIDI input selection
        menu.addAction("Select MIDI Input...", self.select_midi_input)
        menu.addSeparator()
        
        # Color settings
        menu.addAction("Set White Key Color...", self.pick_white_key_color)
        menu.addAction("Set Black Key Color...", self.pick_black_key_color)
        menu.addSeparator()
        menu.addAction("Set Active Key Color...", self.pick_active_key_color)
        menu.addAction("Set Sustain Color...", self.pick_sustain_color)
        menu.addSeparator()
        
        # Dark mode
        dark_mode_action = menu.addAction(
            "Light Mode" if self.dark_mode else "Dark Mode",
            self.toggle_dark_mode
        )
        
        # Chord detection options
        if CHORD_DETECTOR_AVAILABLE and self.chord_detector:
            menu.addSeparator()
            # Flats/sharps toggle
            menu.addAction(
                "Use Sharps (A#)" if self.prefer_flats else "Use Flats (Bb)",
                self.toggle_flats_sharps
            )
            menu.addSeparator()
            if self.chord_window_detached:
                menu.addAction("Attach Chord Window", self.toggle_chord_window)
            else:
                menu.addAction(
                    "Disable Chord Detection" if self.chord_detection_enabled else "Enable Chord Detection",
                    self.toggle_chord_detection
                )
                if self.chord_detection_enabled:
                    menu.addAction("Detach Chord Window", self.toggle_chord_window)
        
        menu.addSeparator()
        menu.addAction("Reset Settings to Default", self.reset_settings)
        
        menu.exec_(event.globalPos())
    
    def select_midi_input(self):
        """Show MIDI input selection dialog"""
        mido, _ = check_dependencies()
        input_ports = mido.get_input_names()
        
        if not input_ports:
            QMessageBox.information(self, "No MIDI Input", 
                                   "No MIDI input ports found!")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select MIDI Input")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        layout.addWidget(QLabel("Select MIDI input port:"))
        
        if self.actual_port_name:
            current_label = QLabel(f"Current: {self.actual_port_name}")
            layout.addWidget(current_label)
        
        list_widget = QListWidget()
        for port in input_ports:
            list_widget.addItem(port)
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_items = list_widget.selectedItems()
            if selected_items:
                port = selected_items[0].text()
                try:
                    # Close old port
                    if self.inport:
                        self.midi_thread_running = False
                        self.inport.close()
                    
                    # Open new port
                    self.inport = mido.open_input(port)
                    self.actual_port_name = port
                    self.midi_thread_running = True
                    self.midi_thread = threading.Thread(target=self.midi_input_thread, daemon=True)
                    self.midi_thread.start()
                except Exception as e:
                    QMessageBox.critical(self, "MIDI Error", 
                                        f"Error opening MIDI port:\n{e}")
    
    def pick_white_key_color(self):
        """Open color picker for white keys"""
        color = QColorDialog.getColor(self.white_key_idle_color, self, "Choose White Key Color")
        if color.isValid():
            self.white_key_idle_color = color
            self.update_piano_colors()
            self.save_settings()
    
    def pick_black_key_color(self):
        """Open color picker for black keys"""
        color = QColorDialog.getColor(self.black_key_idle_color, self, "Choose Black Key Color")
        if color.isValid():
            self.black_key_idle_color = color
            self.update_piano_colors()
            self.save_settings()
    
    def pick_active_key_color(self):
        """Open color picker for active keys"""
        color = QColorDialog.getColor(self.white_key_active_color, self, "Choose Active Key Color")
        if color.isValid():
            self.white_key_active_color = color
            self.black_key_active_color = color
            self.update_piano_colors()
            self.save_settings()
    
    def pick_sustain_color(self):
        """Open color picker for sustain pedal color"""
        color = QColorDialog.getColor(self.sustain_color, self, "Choose Sustain Pedal Color")
        if color.isValid():
            self.sustain_color = color
            self.update_piano_colors()
            self.save_settings()
    
    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.dark_mode = not self.dark_mode
        self.update_piano_colors()
        self.save_settings()
    
    def toggle_chord_detection(self):
        """Toggle chord detection"""
        if not CHORD_DETECTOR_AVAILABLE or not self.chord_detector:
            return
        
        self.chord_detection_enabled = not self.chord_detection_enabled
        
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_label.setVisible(self.chord_detection_enabled)
            if not self.chord_detection_enabled:
                self.chord_label.set_chord(None)
    
    def toggle_flats_sharps(self):
        """Toggle between flats and sharps"""
        if not self.chord_detector:
            return
        
        self.prefer_flats = not self.prefer_flats
        self.chord_detector.set_note_preference(self.prefer_flats)
        self.save_settings()
        # Trigger chord update to refresh display
        self.update_chord_detection()
    
    def toggle_chord_window(self):
        """Toggle detached chord window"""
        if self.chord_window_detached:
            # Attach
            if self.chord_window:
                self.chord_window.close()
                self.chord_window = None
            self.chord_window_detached = False
            if CHORD_DETECTOR_AVAILABLE:
                self.chord_label.setVisible(self.chord_detection_enabled)
        else:
            # Detach
            if CHORD_DETECTOR_AVAILABLE:
                self.chord_label.setVisible(False)
            self.chord_window_detached = True
            self.create_chord_window()
    
    def create_chord_window(self):
        """Create detached chord window"""
        if not CHORD_DETECTOR_AVAILABLE:
            return
        
        self.chord_window = QMainWindow(self)
        self.chord_window.setWindowTitle("Ivory - Chord Display")
        self.chord_window.setMinimumSize(300, 100)
        
        chord_widget = ChordLabelWidget()
        chord_widget.set_chord(self.current_chord)
        self.chord_window.setCentralWidget(chord_widget)
        self.chord_window.chord_label = chord_widget
        
        # Store reference for updates
        self.chord_window.resize(400, 150)
        self.chord_window.show()
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        self.dark_mode = False
        self.white_key_idle_color = QColor(232, 220, 192)  # #E8DCC0
        self.black_key_idle_color = QColor(26, 26, 26)  # #1a1a1a
        self.white_key_active_color = QColor(108, 155, 210)  # #6C9BD2
        self.black_key_active_color = QColor(108, 155, 210)  # #6C9BD2
        self.sustain_color = QColor(210, 163, 108)  # #D2A36C
        self.prefer_flats = True
        
        self.update_piano_colors()
        self.save_settings()
    
    def closeEvent(self, event):
        """Handle window close"""
        self.midi_thread_running = False
        if self.inport:
            self.inport.close()
        if self.chord_window:
            self.chord_window.close()
        event.accept()


class SingleApplication(QApplication):
    """QApplication with single-instance support"""
    
    def __init__(self, appid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._appid = appid
        self._shared_memory = QSharedMemory(appid)
        
        # Try to create shared memory - if it exists, another instance is running
        if self._shared_memory.attach():
            # Another instance exists
            self._is_running = True
        else:
            # First instance - create shared memory
            if self._shared_memory.create(1):
                self._is_running = False
            else:
                # Failed to create - assume another instance exists
                self._is_running = True
    
    def is_running(self):
        """Check if another instance is already running"""
        return self._is_running
    
    def cleanup(self):
        """Clean up shared memory"""
        if self._shared_memory.isAttached():
            self._shared_memory.detach()


def main():
    parser = argparse.ArgumentParser(
        description="PyQt5 MIDI keyboard monitor with chord detection",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-p', '--port', type=str, help='MIDI input port name')
    parser.add_argument('-l', '--list', action='store_true', help='List available MIDI ports')
    
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
    
    # Create application with single-instance support
    app = SingleApplication("ivory-midi-monitor", sys.argv)
    app.setApplicationName("Ivory")
    app.setOrganizationName("Ivory")
    
    # Check if another instance is running
    if app.is_running():
        QMessageBox.warning(None, "Ivory Already Running", 
                           "Ivory is already running.\n\n"
                           "Only one instance can run at a time.")
        sys.exit(0)
    
    # Try to set application icon if available
    icon_path = Path(__file__).parent / "icons" / "ivory.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    monitor = MIDIMonitor(port_name=args.port)
    monitor.show()
    
    # Run event loop
    exit_code = app.exec_()
    
    # Cleanup
    app.cleanup()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()


