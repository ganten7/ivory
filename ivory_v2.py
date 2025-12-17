#!/usr/bin/env python3
"""
Ivory - MIDI Keyboard Monitor with Chord Detection
Cross-platform application built with PyQt5
"""

__version__ = "1.1"

import sys
import time
import argparse
import json
import os
import threading
from collections import defaultdict
from typing import Dict, Set, Optional, Tuple
from pathlib import Path

# PyInstaller support: get resource path
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Import chord detector (enhanced version with improvements)
try:
    from chord_detector_v2 import ChordDetector
    CHORD_DETECTOR_AVAILABLE = True
except ImportError:
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
                                  QHBoxLayout, QFrame, QSizePolicy, QTextBrowser)
    from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QSharedMemory, QSystemSemaphore, QEvent
    from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush, QIcon, QMouseEvent, QContextMenuEvent
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
    except ImportError as e:
        error_msg = f"Error: mido library not found.\n\n{e}\n\nInstall it with:\n  pip install mido python-rtmidi"
        print(error_msg, file=sys.stderr)
        # Try to show error dialog if PyQt5 is available
        try:
            if PYQT5_AVAILABLE:
                from PyQt5.QtWidgets import QApplication, QMessageBox
                if not QApplication.instance():
                    error_app = QApplication(sys.argv)
                QMessageBox.critical(None, "Ivory Error", error_msg)
        except:
            pass
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

def get_config_dir() -> Path:
    """Get platform-specific config directory"""
    if sys.platform == "win32":
        # Windows: %APPDATA%\ivory
        appdata = os.getenv('APPDATA')
        if appdata:
            return Path(appdata) / "ivory"
        return Path.home() / "AppData" / "Roaming" / "ivory"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/ivory
        return Path.home() / "Library" / "Application Support" / "ivory"
    else:
        # Linux and others: ~/.config/ivory
        return Path.home() / ".config" / "ivory"

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

    # Signal emitted when a note is clicked (note_number, is_active)
    note_clicked = pyqtSignal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes: Dict[int, Dict] = {}
        self.sustain_pedal_active = False

        # Manual click mode - for testing without MIDI keyboard
        self.manual_notes: Set[int] = set()  # Notes toggled by mouse clicks
        self.click_enabled = False  # Enable click-to-toggle (disabled by default)

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
        
        # Set size policy - height depends on width for aspect ratio
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        # Ensure widget fills its allocated space
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(200, 50)
        
        # Enable context menu - forward to parent
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
    
    def _on_context_menu(self, pos: QPoint):
        """Forward context menu to parent window"""
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        if parent and hasattr(parent, 'show_context_menu'):
            parent.show_context_menu(self.mapToGlobal(pos))
    
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
    
    def sizeHint(self):
        """Return preferred size based on current width"""
        width = self.width() if self.width() > 0 else 1300
        height = int(width / self.piano_aspect)
        return QSize(width, max(height, 50))
    
    def hasHeightForWidth(self):
        """Indicate that height depends on width (for aspect ratio)"""
        return True
    
    def heightForWidth(self, width):
        """Calculate height based on width to maintain aspect ratio"""
        if width > 0:
            return max(50, int(width / self.piano_aspect))
        return 50
    
    def resizeEvent(self, event):
        """Update height when width changes to maintain aspect ratio"""
        super().resizeEvent(event)
        new_width = event.size().width()
        current_height = self.height()
        if new_width > 0:
            new_height = max(50, int(new_width / self.piano_aspect))
            height_diff = abs(current_height - new_height)
            # Only update if significantly different (more than 2px)
            if height_diff > 2:
                self.setFixedHeight(new_height)
                # Request layout update
                if self.parent():
                    self.parent().updateGeometry()
        self.update()
    
    def paintEvent(self, event):
        """Draw the piano keyboard"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill ENTIRE widget area, not just event.rect()
        widget_rect = self.rect()
        width = widget_rect.width()
        height = widget_rect.height()
        
        # Fill entire widget background (no white space) - use widget.rect() not event.rect()
        painter.fillRect(widget_rect, self.bg_color)
        
        # Use full width and height - piano fills entire widget
        piano_width = width
        piano_height = height
        
        # Calculate key dimensions based on actual widget size
        white_keys_count = 52
        self.white_key_width = piano_width / white_keys_count
        self.white_key_height = piano_height
        self.black_key_width = self.white_key_width * 0.7
        self.black_key_height = self.white_key_height * 0.65
        
        # No translation needed - draw directly at (0, 0)
        
        # Draw white keys
        white_keys_list = [n for n in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1) 
                          if is_white_key(n)]
        
        for idx, note in enumerate(white_keys_list):
            x = idx * self.white_key_width

            # Determine fill color (check both MIDI notes and manual click notes)
            is_active = note in self.active_notes or note in self.manual_notes
            if is_active:
                if note in self.active_notes and self.sustain_pedal_active:
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
                
                # Determine fill color (check both MIDI notes and manual click notes)
                is_active = note in self.active_notes or note in self.manual_notes
                if is_active:
                    if note in self.active_notes and self.sustain_pedal_active:
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

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks to toggle notes"""
        if not self.click_enabled:
            return

        # Only respond to left clicks
        if event.button() != Qt.LeftButton:
            return

        # Get click position
        x = event.x()
        y = event.y()

        # Find which note was clicked
        note = self._get_note_at_position(x, y)

        if note is not None:
            # Toggle the note in manual_notes only
            if note in self.manual_notes:
                self.manual_notes.remove(note)
            else:
                self.manual_notes.add(note)

            # Emit signal and update display
            self.note_clicked.emit(note, note in self.manual_notes)
            self.update()

    def _get_note_at_position(self, x: float, y: float) -> Optional[int]:
        """Determine which note is at the given position"""
        # Check black keys first (they're on top)
        for note in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1):
            if is_black_key(note):
                octave = note // 12
                note_in_octave = note % 12

                # Calculate black key position (same logic as paintEvent)
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
                white_keys_list = [n for n in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1)
                                  if is_white_key(n)]
                if white_keys_before < len(white_keys_list) and white_keys_before + 1 < len(white_keys_list):
                    white_key1_x = white_keys_before * self.white_key_width
                    white_key2_x = (white_keys_before + 1) * self.white_key_width
                    gap_center_x = (white_key1_x + self.white_key_width + white_key2_x) / 2
                    black_x = gap_center_x - self.black_key_width / 2
                else:
                    continue

                # Check if click is within black key bounds
                if (black_x <= x <= black_x + self.black_key_width and
                    0 <= y <= self.black_key_height):
                    return note

        # Check white keys
        white_keys_list = [n for n in range(KEYBOARD_START_NOTE, KEYBOARD_END_NOTE + 1)
                          if is_white_key(n)]

        for idx, note in enumerate(white_keys_list):
            key_x = idx * self.white_key_width

            # Check if click is within white key bounds
            if (key_x <= x <= key_x + self.white_key_width and
                0 <= y <= self.white_key_height):
                return note

        return None


class ChordLabelWidget(QWidget):
    """Widget for displaying chord names"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_chord = None
        # Default height for chord label (can be changed on reattachment)
        self.chord_label_height = 50
        # Allow flexible height - user can resize
        self.setMinimumHeight(50)
        self.setMaximumHeight(500)  # Reasonable max
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Width and height expand
        
        # Remove all margins/padding
        self.setContentsMargins(0, 0, 0, 0)
        
        # Enable context menu - forward to parent
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
    
    def set_chord(self, chord: Optional[str]):
        """Update chord text"""
        try:
            self.current_chord = chord
            self.update()
        except Exception as e:
            print(f"ERROR in set_chord: {e}")
            import traceback
            traceback.print_exc()
            self.current_chord = None
    
    def _on_context_menu(self, pos: QPoint):
        """Forward context menu to parent window"""
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        if parent and hasattr(parent, 'show_context_menu'):
            parent.show_context_menu(self.mapToGlobal(pos))
    
    def paintEvent(self, event):
        """Draw chord text"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Fill ENTIRE widget area with black background (no white space)
            # Use widget.rect() not event.rect() to fill the entire widget
            widget_rect = self.rect()
            painter.fillRect(widget_rect, QColor(0, 0, 0))

            width = self.width()
            height = self.height()

            if not self.current_chord:
                return

            # Convert text representations to symbols for display
            # Order matters: hdim7 must be replaced before dim7, and dim7 before dim
            # hdim7 → ø7, dim7 → °7, dim → ° (for triads)
            display_chord = self.current_chord.replace('hdim7', 'ø7').replace('dim7', '°7').replace('dim', '°')

            # Calculate font size based on height
            font_size = max(12, int(self.height() * 0.6))
        except Exception as e:
            print(f"Error in paintEvent initialization: {e}")
            return

        # Set font - use Courier New (non-bold), fallback to Courier, then monospace
        font = QFont("Courier New", font_size, QFont.Normal)
        if not font.exactMatch():
            font = QFont("Courier", font_size, QFont.Normal)
        if not font.exactMatch():
            font = QFont("monospace", font_size, QFont.Normal)
        
        painter.setFont(font)
        painter.setPen(QColor(232, 220, 192))  # #E8DCC0
        
        # Measure text
        metrics = QFontMetrics(font)
        # Use boundingRect for width (width() is deprecated)
        text_rect = metrics.boundingRect(display_chord)
        text_width = text_rect.width()
        text_height = text_rect.height()

        # Scale font if too wide (but maintain minimum size)
        if text_width > self.width() * 0.95:
            scale_factor = (self.width() * 0.95) / text_width
            font_size = max(6, int(font_size * scale_factor))  # Minimum 6pt font
            font.setPointSize(font_size)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_rect = metrics.boundingRect(display_chord)
            text_width = text_rect.width()
            text_height = text_rect.height()
        
        # Center text
        text_x = (self.width() - text_width) / 2
        text_y = (self.height() + text_height) / 2 - metrics.descent()

        # Special handling for ° and ø symbols - draw them as shapes instead of text
        try:
            if '°' in display_chord or 'ø' in display_chord:
                # Get average character width for spacing
                avg_char_width = metrics.averageCharWidth()
                current_x = int(text_x)

                # Process character by character
                for i, char in enumerate(display_chord):
                    if char == '°':
                        # Add space before symbol (increased for better spacing)
                        padding_before = 8
                        current_x += padding_before

                        # Draw ° as a small circle
                        circle_size = max(4, int(font_size * 0.35))
                        circle_y = int(text_y - metrics.ascent() * 0.7)
                        painter.setPen(QPen(QColor(232, 220, 192), 1.5))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(current_x, circle_y, circle_size, circle_size)

                        # Move past symbol with minimal padding after
                        current_x += circle_size + 3
                    elif char == 'ø':
                        # Add space before symbol (increased for better spacing)
                        padding_before = 8
                        current_x += padding_before

                        # Draw ø as a circle with a diagonal line
                        circle_size = max(6, int(font_size * 0.45))
                        circle_y = int(text_y - metrics.ascent() * 0.4)
                        painter.setPen(QPen(QColor(232, 220, 192), 1.5))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(current_x, circle_y, circle_size, circle_size)
                        # Draw diagonal slash through circle
                        painter.drawLine(current_x, circle_y + circle_size,
                                       current_x + circle_size, circle_y)

                        # Move past symbol with minimal padding after
                        current_x += circle_size + 3
                    else:
                        # Draw regular character
                        painter.drawText(current_x, int(text_y), char)
                        current_x += metrics.boundingRect(char).width()
            else:
                # No special symbols, draw normally
                painter.drawText(int(text_x), int(text_y), display_chord)
        except Exception as e:
            # If drawing fails, fall back to simple text rendering without symbols
            print(f"Error rendering chord with symbols: {e}")
            try:
                # Fall back to drawing the original text (which has dim7/hdim7, no symbols)
                painter.drawText(int(text_x), int(text_y), self.current_chord)
            except:
                pass  # Silently fail


class MIDIMonitor(QMainWindow):
    """Main application window"""
    
    def __init__(self, port_name: Optional[str] = None):
        super().__init__()
        
        self.port_name = port_name
        self.active_notes: Dict[int, Dict] = {}
        self.notes_to_release: set = set()
        self.sustain_pedal_active = False
        self.midi_thread_running = False
        self.chord_window_detached = False  # Initialize chord window state
        self._base_width = 1300  # Base width for percentage sizing
        self._window_size_percent = 100  # Current window size percentage
        self._borderless_mode = False  # Borderless window mode
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
        
        # Settings - use platform-specific config directory
        self.config_file = get_config_dir() / "settings.json"
        self.load_settings()

        # Update chord detector preferences
        if self.chord_detector:
            self.chord_detector.set_note_preference(self.prefer_flats)

        # Initialize UI
        self.init_ui()

        # Apply click_enabled setting after piano_widget is created
        if hasattr(self, 'piano_widget') and hasattr(self, '_click_enabled'):
            self.piano_widget.click_enabled = self._click_enabled
        
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

        # Check for MIDI devices and show warning if needed (after window is shown)
        QTimer.singleShot(500, self.check_midi_devices_on_startup)
    
    def load_settings(self):
        """Load settings from file"""
        defaults = {
            "dark_mode": False,
            "white_key_idle_color": "#E8DCC0",
            "black_key_idle_color": "#1a1a1a",
            "white_key_active_color": "#6C9BD2",
            "black_key_active_color": "#6C9BD2",
            "sustain_color": "#D2A36C",
            "prefer_flats": True,
            "chord_detection_enabled": True,
            "window_size_percent": 100,
            "borderless_mode": False,
            "chord_window_detached": False,
            "detached_chord_height": 50,
            "click_enabled": False,
            "show_no_midi_warning": True
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
                    self.chord_detection_enabled = config.get("chord_detection_enabled", defaults["chord_detection_enabled"])
                    self._window_size_percent = config.get("window_size_percent", defaults["window_size_percent"])
                    self._borderless_mode = config.get("borderless_mode", defaults["borderless_mode"])
                    self.chord_window_detached = config.get("chord_window_detached", defaults["chord_window_detached"])
                    self._detached_chord_height = config.get("detached_chord_height", defaults["detached_chord_height"])
                    self._click_enabled = config.get("click_enabled", defaults["click_enabled"])
                    self.show_no_midi_warning = config.get("show_no_midi_warning", defaults["show_no_midi_warning"])
            except Exception:
                # Use defaults on error
                self.dark_mode = defaults["dark_mode"]
                self.white_key_idle_color = QColor(defaults["white_key_idle_color"])
                self.black_key_idle_color = QColor(defaults["black_key_idle_color"])
                self.white_key_active_color = QColor(defaults["white_key_active_color"])
                self.black_key_active_color = QColor(defaults["black_key_active_color"])
                self.sustain_color = QColor(defaults["sustain_color"])
                self.prefer_flats = defaults["prefer_flats"]
                self.chord_detection_enabled = defaults["chord_detection_enabled"]
                self._window_size_percent = defaults["window_size_percent"]
                self._borderless_mode = defaults["borderless_mode"]
                self.chord_window_detached = defaults["chord_window_detached"]
                self._detached_chord_height = defaults["detached_chord_height"]
                self._click_enabled = defaults["click_enabled"]
                self.show_no_midi_warning = defaults["show_no_midi_warning"]
        else:
            # Use defaults
            self.dark_mode = defaults["dark_mode"]
            self.white_key_idle_color = QColor(defaults["white_key_idle_color"])
            self.black_key_idle_color = QColor(defaults["black_key_idle_color"])
            self.white_key_active_color = QColor(defaults["white_key_active_color"])
            self.black_key_active_color = QColor(defaults["black_key_active_color"])
            self.sustain_color = QColor(defaults["sustain_color"])
            self.prefer_flats = defaults["prefer_flats"]
            self.chord_detection_enabled = defaults["chord_detection_enabled"]
            self._window_size_percent = defaults["window_size_percent"]
            self._borderless_mode = defaults["borderless_mode"]
            self.chord_window_detached = defaults["chord_window_detached"]
            self._detached_chord_height = defaults["detached_chord_height"]
            self._click_enabled = defaults["click_enabled"]
            self.show_no_midi_warning = defaults["show_no_midi_warning"]
    
    def save_settings(self):
        """Save settings to file"""
        config = {
            "dark_mode": self.dark_mode,
            "white_key_idle_color": self.white_key_idle_color.name(),
            "black_key_idle_color": self.black_key_idle_color.name(),
            "white_key_active_color": self.white_key_active_color.name(),
            "black_key_active_color": self.black_key_active_color.name(),
            "sustain_color": self.sustain_color.name(),
            "prefer_flats": self.prefer_flats,
            "chord_detection_enabled": self.chord_detection_enabled,
            "window_size_percent": getattr(self, '_window_size_percent', 100),
            "borderless_mode": getattr(self, '_borderless_mode', False),
            "chord_window_detached": getattr(self, 'chord_window_detached', False),
            "detached_chord_height": getattr(self, '_detached_chord_height', 50),
            "click_enabled": getattr(self.piano_widget, 'click_enabled', False) if hasattr(self, 'piano_widget') else False,
            "show_no_midi_warning": self.show_no_midi_warning
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window title
        self.setWindowTitle("Ivory")
        # Don't modify window flags - keep default window behavior
        self.setMinimumSize(200, 150)
        
        # Try to set window icon if available
        # Handle both development and PyInstaller bundle paths
        try:
            if getattr(sys, 'frozen', False):
                icon_path = resource_path("icons/ivory.png")
            else:
                icon_path = Path(__file__).parent / "icons" / "ivory.png"
        except:
            icon_path = None
        
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create central widget - use a layout to ensure proper window rendering
        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)
        # Install event filter for borderless dragging
        central_widget.installEventFilter(self)
        
        # Create a layout for the central widget - use layout properly
        # This ensures Qt renders the window frame properly
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central_widget.setLayout(layout)
        # CRITICAL: Also set margins on central widget itself
        central_widget.setContentsMargins(0, 0, 0, 0)
        
        # Create chord label (if available) - add to layout
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_label = ChordLabelWidget(central_widget)
            self.chord_label.set_chord(None)
            self.chord_label.setVisible(self.chord_detection_enabled)
            # Set flexible height constraints
            self.chord_label.setMinimumHeight(50)
            self.chord_label.setMaximumHeight(500)
            self.chord_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Install event filter for borderless dragging
            self.chord_label.installEventFilter(self)
            # Initialize detached height
            self._detached_chord_height = 50  # Default
            # Add to layout with stretch factor
            layout.addWidget(self.chord_label, 1)  # stretch=1 means it can expand
        else:
            pass
        
        # Create piano widget - add to layout
        self.piano_widget = PianoWidget(central_widget)
        self.piano_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Connect note click signal for manual testing
        self.piano_widget.note_clicked.connect(self._on_note_clicked)
        # Install event filter for borderless dragging
        self.piano_widget.installEventFilter(self)
        # Add to layout with stretch factor 0 (fixed size based on aspect ratio)
        layout.addWidget(self.piano_widget, 0)
        # Set initial height based on default width
        initial_width = 1300
        initial_piano_height = int(initial_width / self.piano_widget.piano_aspect)
        
        # Update piano colors
        self.update_piano_colors()
        
        # Set default size - use saved size percentage or default
        default_width = 1300
        self._base_width = default_width
        
        # Apply saved window size percentage
        scale = self._window_size_percent / 100.0
        initial_width = int(default_width * scale)
        chord_height = int(50 * scale) if (CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled and not self.chord_window_detached) else 0
        piano_height = int(initial_width / self.piano_widget.piano_aspect)
        initial_height = chord_height + piano_height
        
        # Set geometry constraints
        min_width = 200
        min_piano_height = int(min_width / self.piano_widget.piano_aspect)
        min_height = chord_height + min_piano_height
        
        max_width = 5000
        
        # Make window non-resizable - fixed size only
        self.setFixedSize(initial_width, initial_height)
        
        # Restore chord window detached state if saved
        if self.chord_window_detached and CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled:
            # Will be created after window is shown
            QTimer.singleShot(100, self.create_chord_window)
    
    def set_window_size_percent(self, percent: int):
        """Set window size as percentage of base size"""
        self._window_size_percent = percent
        scale = percent / 100.0
        new_width = int(self._base_width * scale)
        
        # Calculate heights based on new width - SCALE chord height proportionally
        piano_height = int(new_width / self.piano_widget.piano_aspect)
        # Base chord height is 50px at 100% - scale it with the percentage
        base_chord_height = 50
        chord_height = int(base_chord_height * scale) if (CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled and not self.chord_window_detached) else 0
        new_height = chord_height + piano_height
        
        # Update fixed size (window is always non-resizable)
        self.setFixedSize(new_width, new_height)
        
        # CRITICAL: Position widgets immediately with new sizes
        # Don't wait for resizeEvent - update directly
        if hasattr(self, 'piano_widget') and self.piano_widget:
            # Update piano widget size
            self.piano_widget.setFixedSize(new_width, piano_height)
            self.piano_widget.setGeometry(0, chord_height, new_width, piano_height)
        
        if (CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled and 
            not self.chord_window_detached and hasattr(self, 'chord_label') and self.chord_label):
            # Update chord label size - SCALE IT
            self.chord_label.setFixedSize(new_width, chord_height)
            self.chord_label.setGeometry(0, 0, new_width, chord_height)
            self.chord_label.setVisible(True)
            # Update min/max heights to scale proportionally too
            self.chord_label.setMinimumHeight(int(50 * scale))
            self.chord_label.setMaximumHeight(int(500 * scale))
        
        # Update central widget
        central_widget = self.centralWidget()
        if central_widget:
            central_widget.setFixedSize(new_width, new_height)
        
        # Force update to redraw
        self.update()
        if hasattr(self, 'piano_widget'):
            self.piano_widget.update()
        if hasattr(self, 'chord_label') and self.chord_label:
            self.chord_label.update()
        
        # Save settings
        self.save_settings()
    
    def showEvent(self, event):
        """Handle window show event - position widgets after window is visible"""
        super().showEvent(event)
        # Ensure window title is set
        self.setWindowTitle("Ivory")
        # Position widgets after window is shown
        QTimer.singleShot(10, self._position_widgets)
    
    def _update_piano_height(self):
        """Update piano widget height and constraints based on window width"""
        window_width = self.width()
        if window_width > 0:
            # Calculate required piano height
            required_piano_height = int(window_width / self.piano_widget.piano_aspect)
            
            # Update piano widget height (this doesn't trigger parent resizeEvent)
            if abs(self.piano_widget.height() - required_piano_height) > 1:
                self.piano_widget.setFixedHeight(required_piano_height)
            
            # Update min/max sizes
            min_width = 200
            min_piano_height = int(min_width / self.piano_widget.piano_aspect)
            min_chord_height = 50 if (CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled and not self.chord_window_detached) else 0
            min_height = min_chord_height + min_piano_height
            
            max_width = 5000
            self.setMinimumSize(min_width, min_height)
            self.setMaximumWidth(max_width)
    
    def _safe_update_chord_window_width(self):
        """Safely update detached chord window width (called via timer to prevent feedback)"""
        if self.chord_window and self.chord_window_detached and self.chord_window.isVisible():
            current_height = self.chord_window.height()
            current_chord_width = self.chord_window.width()
            new_width = self.width()
            width_diff = abs(new_width - current_chord_width)
            
            # Only update if width actually changed significantly
            if width_diff > 5:
                self.chord_window.resize(new_width, current_height)
    
    def resizeEvent(self, event):
        """Handle window resize - update widget sizes to fill space exactly, no white space"""
        super().resizeEvent(event)
        
        # Only position widgets if we have them initialized
        # Window is non-resizable, so this only happens when size menu changes size
        if hasattr(self, 'piano_widget') and hasattr(self, 'centralWidget'):
            self._position_widgets()
    
    def _position_widgets(self):
        """Position widgets correctly - called from resizeEvent and initial setup"""
        # Safety check - make sure widgets exist
        if not hasattr(self, 'piano_widget') or not self.piano_widget:
            return
        
        # Don't position if window isn't visible yet
        if not self.isVisible():
            return
        
        new_width = self.width()
        new_height = self.height()
        
        # Skip if dimensions are invalid
        if new_width <= 0 or new_height <= 0:
            return
        
        # Get central widget and ensure it has no margins
        central_widget = self.centralWidget()
        if central_widget:
            central_widget.setContentsMargins(0, 0, 0, 0)
            # Ensure central widget fills window exactly
            if central_widget.width() != new_width or central_widget.height() != new_height:
                central_widget.resize(new_width, new_height)
        
        # Update piano widget height based on current width (aspect ratio)
        required_piano_height = int(new_width / self.piano_widget.piano_aspect)
        
        # Position widgets using layout - but override heights to fill space EXACTLY
        chord_detached = hasattr(self, 'chord_window_detached') and self.chord_window_detached
        chord_available = CHORD_DETECTOR_AVAILABLE and hasattr(self, 'chord_detection_enabled') and self.chord_detection_enabled
        chord_label_exists = hasattr(self, 'chord_label') and self.chord_label
        
        if chord_available and not chord_detached and chord_label_exists:
            # Chord label is attached - maintain aspect ratio for piano
            # Calculate chord height based on scale (proportional to window size)
            scale = new_width / self._base_width
            target_chord_height = int(50 * scale)  # Base 50px scaled
            
            # Ensure window height matches exactly: chord_height + piano_height
            required_total_height = target_chord_height + required_piano_height
            actual_window_height = self.height()
            if abs(required_total_height - actual_window_height) > 1:
                self.setFixedSize(new_width, required_total_height)
                actual_window_height = required_total_height
            
            # CRITICAL: Position widgets absolutely - chord at top, piano below it
            # Piano starts at y=target_chord_height, NOT pushed down
            self.chord_label.setGeometry(0, 0, new_width, target_chord_height)
            self.chord_label.setFixedSize(new_width, target_chord_height)
            self.chord_label.setVisible(True)
            
            self.piano_widget.setGeometry(0, target_chord_height, new_width, required_piano_height)
            self.piano_widget.setFixedSize(new_width, required_piano_height)
            
            # Ensure widgets have no margins
            self.piano_widget.setContentsMargins(0, 0, 0, 0)
            self.chord_label.setContentsMargins(0, 0, 0, 0)
            
            # Ensure central widget fills window exactly
            central_widget = self.centralWidget()
            if central_widget:
                central_widget.setGeometry(0, 0, new_width, required_total_height)
                central_widget.setFixedSize(new_width, required_total_height)
        else:
            # No chord label OR chord window is detached - maintain piano aspect ratio
            # Hide chord label if it exists
            if chord_label_exists:
                self.chord_label.setVisible(False)
            
            # CRITICAL: Always ensure window height matches piano height exactly
            # Read current window height after any resize operations
            actual_window_height = self.height()
            if abs(required_piano_height - actual_window_height) > 1:
                self.setFixedSize(new_width, required_piano_height)
                # Update actual height for positioning
                actual_window_height = required_piano_height
            
            # CRITICAL: Position piano at (0, 0) to fill entire window - NEVER push it down
            self.piano_widget.setGeometry(0, 0, new_width, required_piano_height)
            self.piano_widget.setFixedSize(new_width, required_piano_height)
            self.piano_widget.setContentsMargins(0, 0, 0, 0)
            
            # Ensure central widget fills window exactly
            central_widget = self.centralWidget()
            if central_widget:
                central_widget.setGeometry(0, 0, new_width, required_piano_height)
                central_widget.setFixedSize(new_width, required_piano_height)
        
        # Update detached chord window width if needed (debounced)
        if self.chord_window_detached and self.chord_window:
            if not hasattr(self, '_chord_width_update_timer'):
                self._chord_width_update_timer = QTimer()
                self._chord_width_update_timer.setSingleShot(True)
                self._chord_width_update_timer.timeout.connect(self._safe_update_chord_window_width)
            self._chord_width_update_timer.stop()
            self._chord_width_update_timer.start(100)
    
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
            # No MIDI devices found - don't exit, just don't connect
            # User will be notified via check_midi_devices_on_startup
            return
        
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

    def check_midi_devices_on_startup(self):
        """Check for MIDI devices on startup and show informational dialog if none found"""
        # Only show warning if user hasn't disabled it
        if not self.show_no_midi_warning:
            return

        mido, _ = check_dependencies()
        input_ports = mido.get_input_names()

        if not input_ports:
            # No MIDI devices found - show friendly notification
            dialog = QDialog(self)
            dialog.setWindowTitle("No MIDI Devices Found")
            dialog.setMinimumWidth(450)

            layout = QVBoxLayout()
            dialog.setLayout(layout)

            # Message
            message = QLabel(
                "No midi devices found. You can still use the piano to find chords "
                "by enabling Key Toggle in the right-click menu."
            )
            message.setWordWrap(True)
            layout.addWidget(message)

            layout.addSpacing(10)

            # "Don't show again" checkbox
            dont_show_checkbox = QCheckBox("Don't show again")
            layout.addWidget(dont_show_checkbox)

            # Ok button
            button_layout = QHBoxLayout()
            ok_button = QPushButton("Ok")
            ok_button.setDefault(True)

            def on_ok():
                if dont_show_checkbox.isChecked():
                    self.show_no_midi_warning = False
                    self.save_settings()
                dialog.accept()

            ok_button.clicked.connect(on_ok)
            button_layout.addStretch()
            button_layout.addWidget(ok_button)
            button_layout.addStretch()
            layout.addLayout(button_layout)

            dialog.exec_()

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

    def _on_note_clicked(self, note: int, is_active: bool):
        """Handle manual note toggle from mouse clicks"""
        # Manual notes are already managed in PianoWidget
        # Just trigger chord detection update
        self.update_chord_detection()

    def update_gui(self):
        """Update GUI elements"""
        # Update piano widget
        self.piano_widget.set_active_notes(self.active_notes)
        self.piano_widget.set_sustain_pedal(self.sustain_pedal_active)
    
    def update_chord_detection(self):
        """Update chord detection"""
        if not self.chord_detection_enabled or not self.chord_detector:
            return

        try:
            # Combine MIDI notes and manual click notes
            active_note_numbers = set(self.active_notes.keys())  # MIDI notes
            active_note_numbers.update(self.piano_widget.manual_notes)  # Manual click notes

            if not active_note_numbers:
                self.current_chord = None
                if CHORD_DETECTOR_AVAILABLE:
                    self.chord_label.set_chord(None)
                if self.chord_window:
                    self.chord_window.chord_label.set_chord(None)
                return

            # Detect chord with error handling
            chord = self.chord_detector.detect_chord(active_note_numbers)
            self.current_chord = chord

            # Update displays
            if CHORD_DETECTOR_AVAILABLE and not self.chord_window_detached:
                self.chord_label.set_chord(chord)
            if self.chord_window:
                self.chord_window.chord_label.set_chord(chord)
        except Exception as e:
            # Log error but don't crash
            print(f"Error in chord detection: {e}")
            import traceback
            traceback.print_exc()
            # Clear chord display on error
            self.current_chord = None
            if CHORD_DETECTOR_AVAILABLE:
                self.chord_label.set_chord(None)
            if self.chord_window:
                self.chord_window.chord_label.set_chord(None)
    
    def contextMenuEvent(self, event):
        """Handle context menu"""
        self.show_context_menu(event.globalPos())
    
    def show_context_menu(self, global_pos: QPoint):
        """Show context menu at specified global position"""
        menu = QMenu(self)
        
        # Apply theme based on dark mode: ivory on black (dark mode) or black on ivory (light mode)
        if self.dark_mode:
            # Dark mode: ivory text on black background
            bg_color = "#000000"
            text_color = "#E8DCC0"
            separator_color = "#E8DCC0"
            selected_bg = "#1a1a1a"
        else:
            # Light mode: black text on ivory background
            bg_color = "#E8DCC0"
            text_color = "#000000"
            separator_color = "#000000"
            selected_bg = "#d4c8b0"
        
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {bg_color};
                font-family: "Courier New", Courier, monospace;
                font-weight: bold;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 4px 20px 4px 20px;
                font-family: "Courier New", Courier, monospace;
                font-weight: bold;
            }}
            QMenu::item:selected {{
                background-color: {selected_bg};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {separator_color};
                margin: 1px 0px 1px 0px;
            }}
        """)
        
        # Size menu - always available at top
        size_menu = menu.addMenu("Size")
        size_menu.addAction("50%", lambda: self.set_window_size_percent(50))
        size_menu.addAction("75%", lambda: self.set_window_size_percent(75))
        size_menu.addAction("100%", lambda: self.set_window_size_percent(100))
        size_menu.addAction("125%", lambda: self.set_window_size_percent(125))
        size_menu.addAction("150%", lambda: self.set_window_size_percent(150))
        size_menu.addAction("175%", lambda: self.set_window_size_percent(175))
        size_menu.addAction("200%", lambda: self.set_window_size_percent(200))
        menu.addSeparator()
        
        # Borderless mode toggle
        borderless_action = menu.addAction(
            "Bordered" if self._borderless_mode else "Borderless",
            self.toggle_borderless_mode
        )
        menu.addSeparator()
        
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
            # Key click toggle (only in windowed mode, not borderless)
            if not self._borderless_mode:
                menu.addAction(
                    "Disable Key Toggle" if self.piano_widget.click_enabled else "Enable Key Toggle",
                    self.toggle_key_clicks
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
        menu.addAction("About", self.show_about)
        menu.addAction("Reset Settings to Default", self.reset_settings)
        
        # Show menu at specified position
        menu.exec_(global_pos)
    
    def select_midi_input(self):
        """Show MIDI input selection dialog"""
        mido, _ = check_dependencies()
        input_ports = mido.get_input_names()

        if not input_ports:
            QMessageBox.information(self, "No MIDI Input",
                                   "No MIDI input ports found!\n\n"
                                   "Make sure your MIDI device is connected.\n\n"
                                   "You can still use chord detection by enabling Key Toggle in the right-click menu.")
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
        self.save_settings()  # Save state change
        
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_label.setVisible(self.chord_detection_enabled and not self.chord_window_detached)
            if not self.chord_detection_enabled:
                self.chord_label.set_chord(None)
        
        # Resize window to maintain aspect ratio
        if not self.chord_window_detached:
            current_width = self.width()
            required_piano_height = int(current_width / self.piano_widget.piano_aspect)
            chord_height = int(50 * (current_width / self._base_width)) if (self.chord_detection_enabled and CHORD_DETECTOR_AVAILABLE) else 0
            required_total_height = chord_height + required_piano_height
            
            # Update window size immediately
            self.setFixedSize(current_width, required_total_height)
            # Use QTimer to ensure window has resized before positioning
            QTimer.singleShot(10, lambda: self._position_widgets())
        else:
            # Just update constraints if detached - ensure no white space
            current_width = self.width()
            required_piano_height = int(current_width / self.piano_widget.piano_aspect)
            self.setFixedSize(current_width, required_piano_height)
            # Use QTimer to ensure window has resized before positioning
            QTimer.singleShot(10, lambda: self._position_widgets())
    
    def toggle_flats_sharps(self):
        """Toggle between flats and sharps"""
        if not self.chord_detector:
            return

        self.prefer_flats = not self.prefer_flats
        self.chord_detector.set_note_preference(self.prefer_flats)
        self.save_settings()
        # Trigger chord update to refresh display
        self.update_chord_detection()

    def toggle_key_clicks(self):
        """Toggle clickable keys on/off"""
        self.piano_widget.click_enabled = not self.piano_widget.click_enabled
        # Clear all manually toggled keys when disabling
        if not self.piano_widget.click_enabled:
            self.piano_widget.manual_notes.clear()
            self.piano_widget.update()
        self.save_settings()
    
    def toggle_chord_window(self):
        """Toggle detached chord window"""
        if self.chord_window_detached:
            # Currently detached - ATTACH it
            if self.chord_window:
                # Save detached window height before closing (for next detachment)
                self._detached_chord_height = self.chord_window.height()
                self.chord_window.close()
                self.chord_window = None
            self.chord_window_detached = False
            self.save_settings()  # Save state change
            
            if CHORD_DETECTOR_AVAILABLE:
                # Calculate chord height based on current piano size (proportional)
                current_width = self.width()
                scale = current_width / self._base_width
                chord_height = int(50 * scale)  # Base 50px scaled to current size
                
                # Set chord label size based on piano, not detached window size
                self.chord_label.setFixedSize(current_width, chord_height)
                self.chord_label.setGeometry(0, 0, current_width, chord_height)
                self.chord_label.setMinimumHeight(int(50 * scale))
                self.chord_label.setMaximumHeight(int(500 * scale))
                self.chord_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self.chord_label.setVisible(self.chord_detection_enabled)
            
            # Resize window to fit piano + chord label (maintain aspect ratio)
            current_width = self.width()
            required_piano_height = int(current_width / self.piano_widget.piano_aspect)
            chord_height = int(50 * (current_width / self._base_width)) if (CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled) else 0
            required_total_height = chord_height + required_piano_height
            
            # Update fixed size immediately
            self.setFixedSize(current_width, required_total_height)
            # Position widgets immediately to prevent white space
            self._position_widgets()
        else:
            # Currently attached - DETACH it
            # Save current chord label height before hiding
            if CHORD_DETECTOR_AVAILABLE and self.chord_label:
                self._detached_chord_height = self.chord_label.height()
            
            # Hide chord label in main window
            if CHORD_DETECTOR_AVAILABLE:
                self.chord_label.setVisible(False)
            
            self.chord_window_detached = True
            self.save_settings()  # Save state change
            
            # CREATE the detached window
            self.create_chord_window()
            
            # CRITICAL: Resize window to fit CURRENT piano height maintaining aspect ratio
            # This ensures the window maintains aspect ratio when detached
            current_width = self.width()
            current_piano_height = int(current_width / self.piano_widget.piano_aspect)  # Calculate from width
            
            # Resize window to fit piano with aspect ratio maintained
            # Update fixed size immediately
            self.setFixedSize(current_width, current_piano_height)
            # Position widgets immediately to ensure no white space
            self._position_widgets()
    
    def create_chord_window(self):
        """Create detached chord window"""
        if not CHORD_DETECTOR_AVAILABLE:
            return
        
        
        # Don't create if already exists
        if self.chord_window:
            return
        
        # Create independent window (not a child of main window)
        self.chord_window = QMainWindow()
        # Set title
        self.chord_window.setWindowTitle("Ivory")
        self.chord_window.setMinimumSize(300, 100)
        self.chord_window.setContentsMargins(0, 0, 0, 0)
        
        # Apply borderless mode if enabled, otherwise ensure normal window frame is visible
        if self._borderless_mode:
            self.chord_window.setWindowFlags(Qt.FramelessWindowHint)
        else:
            # Ensure normal window frame is visible (default QMainWindow flags)
            self.chord_window.setWindowFlags(Qt.Window)
        
        # Create layout with no margins
        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central_widget.setLayout(layout)
        self.chord_window.setCentralWidget(central_widget)
        
        # Install event filter on central widget for borderless dragging
        central_widget.installEventFilter(self.chord_window)
        
        chord_widget = ChordLabelWidget()
        chord_widget.set_chord(self.current_chord)
        # Non-aspect ratio locked - allow height resizing
        chord_widget.setMinimumHeight(50)
        chord_widget.setMaximumHeight(16777215)  # Unlimited height
        chord_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Disable context menu on widget itself - let window handle it
        chord_widget.setContextMenuPolicy(Qt.NoContextMenu)
        # Install event filter for borderless dragging and context menu
        chord_widget.installEventFilter(self.chord_window)
        layout.addWidget(chord_widget)
        self.chord_window.chord_label = chord_widget
        
        # Add mouse event handlers for dragging borderless window
        def chord_mousePressEvent(event):
            if self._borderless_mode and event.button() == Qt.LeftButton:
                self.chord_window._drag_position = event.globalPos() - self.chord_window.frameGeometry().topLeft()
                event.accept()
            else:
                QMainWindow.mousePressEvent(self.chord_window, event)
        
        def chord_mouseMoveEvent(event):
            if self._borderless_mode and event.buttons() == Qt.LeftButton and hasattr(self.chord_window, '_drag_position'):
                self.chord_window.move(event.globalPos() - self.chord_window._drag_position)
                event.accept()
            else:
                QMainWindow.mouseMoveEvent(self.chord_window, event)
        
        def chord_mouseReleaseEvent(event):
            if self._borderless_mode and event.button() == Qt.LeftButton and hasattr(self.chord_window, '_drag_position'):
                delattr(self.chord_window, '_drag_position')
            QMainWindow.mouseReleaseEvent(self.chord_window, event)
        
        def chord_eventFilter(obj, event):
            """Event filter for chord window child widgets to enable dragging and context menu"""
            # Handle context menu events - forward to window
            if isinstance(event, QMouseEvent) and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                # Create a QContextMenuEvent and forward to window's contextMenuEvent
                context_event = QContextMenuEvent(QContextMenuEvent.Mouse, event.pos(), event.globalPos())
                self.chord_window.contextMenuEvent(context_event)
                return True  # Consume the event
            
            # Handle dragging when borderless mode is enabled
            if self._borderless_mode and isinstance(event, QMouseEvent):
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    # Set drag position and let event continue
                    self.chord_window._drag_position = event.globalPos() - self.chord_window.frameGeometry().topLeft()
                    return False  # Let event continue
                elif event.type() == QEvent.MouseMove and event.buttons() == Qt.LeftButton and hasattr(self.chord_window, '_drag_position'):
                    # CRITICAL: Handle mouse move in event filter to enable dragging from child widgets
                    self.chord_window.move(event.globalPos() - self.chord_window._drag_position)
                    return True  # Consume event to prevent widget-specific handling
                elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                    if hasattr(self.chord_window, '_drag_position'):
                        delattr(self.chord_window, '_drag_position')
            return False
        
        def chord_contextMenuEvent(event):
            """Handle context menu for chord window"""
            # Forward to main window's context menu
            # Use globalPos() if available, otherwise convert from local position
            if hasattr(event, 'globalPos'):
                global_pos = event.globalPos()
            else:
                global_pos = self.chord_window.mapToGlobal(event.pos())
            self.show_context_menu(global_pos)
        
        # Override mouse event handlers
        self.chord_window.mousePressEvent = chord_mousePressEvent
        self.chord_window.mouseMoveEvent = chord_mouseMoveEvent
        self.chord_window.mouseReleaseEvent = chord_mouseReleaseEvent
        self.chord_window.eventFilter = chord_eventFilter
        self.chord_window.contextMenuEvent = chord_contextMenuEvent
        # Enable context menu using DefaultContextMenu to use contextMenuEvent handler
        self.chord_window.setContextMenuPolicy(Qt.DefaultContextMenu)
        
        # Store reference for updates
        # Use piano width but allow height to be resized
        piano_width = self.width()
        default_height = 150
        if hasattr(self, '_detached_chord_height') and self._detached_chord_height > 0:
            default_height = self._detached_chord_height
        
        
        # Store reference for safe updates (will be called via timer)
        # Don't connect directly to resize events to avoid feedback loops
        
        self.chord_window.resize(piano_width, default_height)
        
        # Connect close event to handle manual window closure
        def on_chord_window_close(event):
            """Handle chord window being closed manually"""
            # Reset detached state
            self.chord_window_detached = False
            self.save_settings()  # Save state change
            
            if CHORD_DETECTOR_AVAILABLE:
                # Calculate chord height based on current piano size (proportional)
                current_width = self.width()
                scale = current_width / self._base_width
                chord_height = int(50 * scale)  # Base 50px scaled to current size
                
                # Set chord label size based on piano, not detached window size
                self.chord_label.setFixedSize(current_width, chord_height)
                self.chord_label.setGeometry(0, 0, current_width, chord_height)
                self.chord_label.setMinimumHeight(int(50 * scale))
                self.chord_label.setMaximumHeight(int(500 * scale))
                self.chord_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self.chord_label.setVisible(self.chord_detection_enabled)
            
            # Resize window to fit piano + chord label
            current_width = self.width()
            required_piano_height = int(current_width / self.piano_widget.piano_aspect)
            chord_height = int(50 * (current_width / self._base_width)) if (CHORD_DETECTOR_AVAILABLE and self.chord_detection_enabled) else 0
            required_total_height = chord_height + required_piano_height
            
            # Update fixed size
            self.setFixedSize(current_width, required_total_height)
            self._position_widgets()
            # Clean up
            self.chord_window = None
            event.accept()
        
        self.chord_window.closeEvent = on_chord_window_close
        self.chord_window.show()
        
    
    def toggle_borderless_mode(self):
        """Toggle borderless window mode"""
        self._borderless_mode = not self._borderless_mode

        # Disable key clicking in borderless mode (interferes with window dragging)
        if self._borderless_mode:
            self.piano_widget.click_enabled = False

        self._apply_borderless_mode()
        self.save_settings()
    
    def _apply_borderless_mode(self):
        """Apply borderless mode to window"""
        if self._borderless_mode:
            # Remove window frame
            self.setWindowFlags(Qt.FramelessWindowHint)
        else:
            # Restore normal window frame
            self.setWindowFlags(Qt.Window)
        
        # Always ensure title is set
        self.setWindowTitle("Ivory")
        # Show window again after flag change
        self.show()
        
        # Apply borderless mode to chord window if it exists
        if self.chord_window:
            if self._borderless_mode:
                self.chord_window.setWindowFlags(Qt.FramelessWindowHint)
            else:
                self.chord_window.setWindowFlags(Qt.Window)
            self.chord_window.setWindowTitle("Ivory")
            self.chord_window.show()
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging borderless window"""
        if self._borderless_mode and event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging borderless window"""
        if self._borderless_mode and event.buttons() == Qt.LeftButton and hasattr(self, '_drag_position'):
            self.move(event.globalPos() - self._drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self._borderless_mode and event.button() == Qt.LeftButton and hasattr(self, '_drag_position'):
            delattr(self, '_drag_position')
        super().mouseReleaseEvent(event)
    
    def eventFilter(self, obj, event):
        """Event filter to enable dragging from child widgets when borderless"""
        # Only enable dragging when borderless mode is enabled
        if self._borderless_mode and isinstance(event, QMouseEvent):
            # Handle left mouse button press for dragging
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # Set drag position and let event continue (widget can still handle it if needed)
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                return False  # Let the event continue to the widget
            # Handle mouse move for dragging - CRITICAL: must handle this in event filter
            elif event.type() == QEvent.MouseMove and event.buttons() == Qt.LeftButton and hasattr(self, '_drag_position'):
                self.move(event.globalPos() - self._drag_position)
                return True  # Consume the event to prevent widget-specific handling
            # Handle mouse release
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if hasattr(self, '_drag_position'):
                    delattr(self, '_drag_position')
        return super().eventFilter(obj, event)
    
    def show_about(self):
        """Show About dialog with website link"""
        dialog = QDialog(self)
        dialog.setWindowTitle("About Ivory")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(150)
        
        # Apply theme based on dark mode: ivory on black (dark mode) or black on ivory (light mode)
        if self.dark_mode:
            bg_color = "#000000"
            text_color = "#E8DCC0"
            button_bg = "#1a1a1a"
            button_hover = "#2a2a2a"
            button_border = "#E8DCC0"
        else:
            bg_color = "#E8DCC0"
            text_color = "#000000"
            button_bg = "#d4c8b0"
            button_hover = "#c0b49c"
            button_border = "#000000"
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                font-family: "Courier New", Courier, monospace;
                font-weight: bold;
            }}
            QLabel a {{
                color: {text_color};
            }}
            QDialogButtonBox {{
                background-color: {bg_color};
            }}
            QPushButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {button_border};
                padding: 4px 12px;
                font-family: "Courier New", Courier, monospace;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
        """)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Add title
        title_label = QLabel("Ivory")
        title_font = QFont("Courier New", 16, QFont.Bold)
        if not title_font.exactMatch():
            title_font = QFont("Courier", 16, QFont.Bold)
        if not title_font.exactMatch():
            title_font = QFont("monospace", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Add description
        desc_label = QLabel("Simple MIDI Keyboard Monitor with Advanced Chord Detection")
        desc_font = QFont("Courier New", 10, QFont.Bold)
        if not desc_font.exactMatch():
            desc_font = QFont("Courier", 10, QFont.Bold)
        if not desc_font.exactMatch():
            desc_font = QFont("monospace", 10, QFont.Bold)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # Add website link
        link_text = f'<a href="https://shambhaline.neocities.org" style="color: {text_color};">shambhaline@neocities.org</a>'
        link_label = QLabel(link_text)
        link_font = QFont("Courier New", 10, QFont.Bold)
        if not link_font.exactMatch():
            link_font = QFont("Courier", 10, QFont.Bold)
        if not link_font.exactMatch():
            link_font = QFont("monospace", 10, QFont.Bold)
        link_label.setFont(link_font)
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)
        
        # Add spacer to push version and button to bottom
        layout.addStretch()
        
        # Create horizontal layout for bottom section (version on left, button on right)
        bottom_layout = QHBoxLayout()
        
        # Add version label in bottom left
        version_label = QLabel(f"v{__version__}")
        version_font = QFont("Courier New", 8)
        if not version_font.exactMatch():
            version_font = QFont("Courier", 8)
        if not version_font.exactMatch():
            version_font = QFont("monospace", 8)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        bottom_layout.addWidget(version_label)
        
        # Add spacer to push button to right
        bottom_layout.addStretch()
        
        # Add close button
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        bottom_layout.addWidget(buttons)
        
        # Add bottom layout to main layout
        layout.addLayout(bottom_layout)
        
        dialog.exec_()
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        self.dark_mode = False
        self.white_key_idle_color = QColor(232, 220, 192)  # #E8DCC0
        self.black_key_idle_color = QColor(26, 26, 26)  # #1a1a1a
        self.white_key_active_color = QColor(108, 155, 210)  # #6C9BD2
        self.black_key_active_color = QColor(108, 155, 210)  # #6C9BD2
        self.sustain_color = QColor(210, 163, 108)  # #D2A36C
        self.prefer_flats = True
        self.chord_detection_enabled = True
        self._window_size_percent = 100
        self._borderless_mode = False
        self.chord_window_detached = False
        self._detached_chord_height = 50
        self._click_enabled = False
        
        # Apply borderless mode change (will be False after reset)
        self._apply_borderless_mode()
        
        # Reset window size
        self.set_window_size_percent(100)
        
        # Reset click_enabled on piano widget
        if hasattr(self, 'piano_widget'):
            self.piano_widget.click_enabled = False
        
        # Update chord detector preferences
        if self.chord_detector:
            self.chord_detector.set_note_preference(self.prefer_flats)
        
        # Close detached window if open
        if self.chord_window:
            self.chord_window.close()
            self.chord_window = None
        
        # Show chord label if enabled
        if CHORD_DETECTOR_AVAILABLE:
            self.chord_label.setVisible(self.chord_detection_enabled)
        
        self.update_piano_colors()
        self.save_settings()
    
    def closeEvent(self, event):
        """Handle window close"""
        # Stop MIDI thread
        self.midi_thread_running = False

        # Stop all timers
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if hasattr(self, 'chord_timer'):
            self.chord_timer.stop()
        if hasattr(self, '_chord_width_update_timer'):
            self._chord_width_update_timer.stop()

        # Close MIDI port
        if self.inport:
            self.inport.close()

        # Close chord window
        if self.chord_window:
            self.chord_window.close()

        event.accept()


class SingleApplication(QApplication):
    """QApplication with single-instance support"""
    
    def __init__(self, appid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._appid = appid
        self._shared_memory = QSharedMemory(appid)
        self._created_shared_memory = False  # Track if we created it

        # Try to attach to existing shared memory first
        if self._shared_memory.attach():
            # Another instance exists
            self._is_running = True
            self._shared_memory.detach()  # Detach immediately, we don't need it
        else:
            # First instance - create shared memory
            if self._shared_memory.create(1):
                self._is_running = False
                self._created_shared_memory = True  # We created it, so we must delete it
            else:
                # Failed to create - assume another instance exists
                self._is_running = True
    
    def is_running(self):
        """Check if another instance is already running"""
        return self._is_running

    def __del__(self):
        """Destructor to ensure shared memory is cleaned up"""
        self.cleanup()

    def cleanup(self):
        """Clean up shared memory"""
        # Only cleanup if we created the shared memory
        if hasattr(self, '_created_shared_memory') and self._created_shared_memory:
            if hasattr(self, '_shared_memory'):
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

    # Fork the process to detach from terminal (Unix/Linux/macOS only)
    # This allows closing the terminal without killing Ivory
    # 
    # IMPORTANT: Windows compatibility - os.fork() doesn't exist on Windows
    # Always check hasattr(os, 'fork') before calling fork() to avoid AttributeError
    # See WINDOWS_COMPATIBILITY.md for details
    #
    if hasattr(os, 'fork'):
        if os.fork() > 0:
            # Parent process - exit immediately
            sys.exit(0)
        # Child process continues
        # Redirect stdout/stderr to /dev/null (Unix only)
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    else:
        # Windows: fork() doesn't exist, so we can't detach from terminal
        # On Windows, the app will run in the terminal window
        # This is acceptable behavior for Windows users
        pass

    # Create application (removed single-instance check - it was causing issues)
    app = QApplication(sys.argv)
    app.setApplicationName("Ivory")
    app.setOrganizationName("Ivory")
    
    # Try to set application icon if available
    # Handle both development and PyInstaller bundle paths
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle
            icon_path = resource_path("icons/ivory.png")
        else:
            # Development
            icon_path = Path(__file__).parent / "icons" / "ivory.png"
    except:
        icon_path = None
    
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    monitor = MIDIMonitor(port_name=args.port)
    # Set window title
    monitor.setWindowTitle("Ivory")
    monitor.show()
    # Force window to be raised and activated
    monitor.raise_()
    monitor.activateWindow()
    
    # Run event loop
    exit_code = app.exec_()

    sys.exit(exit_code)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Show error dialog if possible, otherwise print to stderr
        import traceback
        error_msg = f"Ivory encountered an error:\n\n{str(e)}\n\n{traceback.format_exc()}"
        try:
            # Try to show error dialog (only if PyQt5 is available)
            if PYQT5_AVAILABLE:
                from PyQt5.QtWidgets import QApplication, QMessageBox
                if not QApplication.instance():
                    error_app = QApplication(sys.argv)
                QMessageBox.critical(None, "Ivory Error", error_msg)
            else:
                print(error_msg, file=sys.stderr)
        except:
            # Fallback to stderr
            print(error_msg, file=sys.stderr)
        sys.exit(1)
