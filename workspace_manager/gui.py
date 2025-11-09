#!/usr/bin/env python3
"""
GUI module for Windows 11 Workspace Manager

Provides a modern, minimal graphical interface for viewing and managing workspaces.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import tkinter as tk
import threading
from PIL import Image, ImageTk
import io

from .config import get_default_config_path, ConfigManager


class WindowPositionSelector(ctk.CTkFrame):
    """Visual widget for positioning and sizing windows on screen"""

    def __init__(self, master, on_change: Optional[Callable] = None, other_windows: Optional[list] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_change = on_change
        self.other_windows = other_windows or []  # List of other windows to show as guides

        # Will be set after widget is visible
        self.screen_width = None
        self.screen_height = None
        self.taskbar_height = 40  # Approximate taskbar height

        # Canvas dimensions (will be calculated based on screen aspect ratio)
        self.canvas_width = 600
        self.canvas_height = 340

        # Scale factor (will be calculated)
        self.scale_x = 1.0
        self.scale_y = 1.0

        # Window rectangle (in screen coordinates)
        self.window_x = 100
        self.window_y = 100
        self.window_width = 800
        self.window_height = 600

        # Drag state
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # Resize state
        self.resizing = False
        self.resize_handle = None  # 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.resize_original_rect = None

        # Screen label reference
        self.screen_label = None

        # Detect screen resolution and setup UI
        self.after(100, self._detect_screen_and_setup)

    def _detect_screen_and_setup(self):
        """Detect screen resolution and setup UI"""
        # Get actual screen resolution
        self.update_idletasks()
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # Calculate canvas dimensions maintaining aspect ratio
        # Keep max width of 600, calculate height based on aspect ratio
        aspect_ratio = self.screen_height / self.screen_width
        self.canvas_width = 600
        self.canvas_height = int(self.canvas_width * aspect_ratio)

        # Limit canvas height to reasonable size
        if self.canvas_height > 400:
            self.canvas_height = 400
            self.canvas_width = int(self.canvas_height / aspect_ratio)

        # Calculate scale factors
        self.scale_x = self.canvas_width / self.screen_width
        self.scale_y = self.canvas_height / self.screen_height

        # Now create the UI
        self._create_ui()
        self._draw_window()

    def _create_ui(self):
        """Create the UI"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Posicionar y dimensionar ventana (arrastra y redimensiona el rectángulo)",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        header.pack(pady=(0, 10))

        # Canvas frame with border
        canvas_frame = ctk.CTkFrame(self, fg_color=("gray80", "gray25"), corner_radius=8)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#1a1a1a",
            highlightthickness=1,
            highlightbackground="#404040"
        )
        self.canvas.pack(padx=2, pady=2)

        # Draw grid
        self._draw_grid()

        # Draw screen border
        self.canvas.create_rectangle(
            0, 0, self.canvas_width, self.canvas_height,
            outline="#404040",
            width=2
        )

        # Draw taskbar area at bottom
        taskbar_y = (self.screen_height - self.taskbar_height) * self.scale_y
        self.canvas.create_rectangle(
            0, taskbar_y, self.canvas_width, self.canvas_height,
            fill="#2a2a2a",
            outline="#404040",
            width=1,
            tags="taskbar"
        )

        # Add taskbar label
        self.canvas.create_text(
            self.canvas_width / 2, taskbar_y + 10,
            text="Barra de Tareas",
            anchor="n",
            fill="#606060",
            font=("Arial", 8),
            tags="taskbar"
        )

        # Add screen label (save reference for updates)
        self.screen_label = self.canvas.create_text(
            10, 10,
            text=f"Pantalla: {self.screen_width}x{self.screen_height}",
            anchor="nw",
            fill="#808080",
            font=("Arial", 9)
        )

        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Motion>", self._on_mouse_move)

        # Info label
        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#3b82f6", "#60a5fa")
        )
        self.info_label.pack(pady=(5, 0))

        self._update_info()

    def _draw_grid(self):
        """Draw grid on canvas"""
        # Vertical lines every 10% (192 pixels = 10% of 1920)
        for i in range(1, 10):
            x = i * self.canvas_width / 10
            self.canvas.create_line(
                x, 0, x, self.canvas_height,
                fill="#2a2a2a",
                width=1,
                dash=(2, 4)
            )

        # Horizontal lines every 10%
        for i in range(1, 10):
            y = i * self.canvas_height / 10
            self.canvas.create_line(
                0, y, self.canvas_width, y,
                fill="#2a2a2a",
                width=1,
                dash=(2, 4)
            )

    def _draw_window(self):
        """Draw the window rectangle"""
        # Only draw if canvas exists
        if not hasattr(self, 'canvas') or self.canvas is None:
            return

        # Clear previous window elements
        self.canvas.delete("window")
        self.canvas.delete("guide_window")

        # Draw other windows as guides (semi-transparent shadows)
        for other_window in self.other_windows:
            ox1 = other_window.get("x", 0) * self.scale_x
            oy1 = other_window.get("y", 0) * self.scale_y
            ox2 = (other_window.get("x", 0) + other_window.get("width", 800)) * self.scale_x
            oy2 = (other_window.get("y", 0) + other_window.get("height", 600)) * self.scale_y

            # Draw guide window (gray, semi-transparent look)
            self.canvas.create_rectangle(
                ox1, oy1, ox2, oy2,
                fill="",
                outline="#808080",
                width=1,
                dash=(4, 4),
                tags="guide_window"
            )

            # Draw a filled semi-transparent version
            self.canvas.create_rectangle(
                ox1, oy1, ox2, oy2,
                fill="#808080",
                outline="",
                stipple="gray25",
                tags="guide_window"
            )

            # Add label showing which app
            app_id = other_window.get("app_id", "")
            if app_id:
                center_x = (ox1 + ox2) / 2
                center_y = (oy1 + oy2) / 2
                self.canvas.create_text(
                    center_x, center_y,
                    text=app_id,
                    fill="#a0a0a0",
                    font=("Arial", 9, "italic"),
                    tags="guide_window"
                )

        # Convert to canvas coordinates
        x1 = self.window_x * self.scale_x
        y1 = self.window_y * self.scale_y
        x2 = (self.window_x + self.window_width) * self.scale_x
        y2 = (self.window_y + self.window_height) * self.scale_y

        # Draw window rectangle
        self.window_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#3b82f6",
            outline="#60a5fa",
            width=2,
            stipple="gray50",
            tags="window"
        )

        # Draw resize handles (corners)
        handle_size = 8
        handles = [
            ("nw", x1, y1),
            ("ne", x2, y1),
            ("sw", x1, y2),
            ("se", x2, y2),
        ]

        for handle_id, hx, hy in handles:
            self.canvas.create_rectangle(
                hx - handle_size/2, hy - handle_size/2,
                hx + handle_size/2, hy + handle_size/2,
                fill="#60a5fa",
                outline="#3b82f6",
                width=1,
                tags=("window", f"handle_{handle_id}")
            )

        # Draw edge handles (middle of edges)
        edge_handles = [
            ("n", (x1 + x2) / 2, y1),
            ("s", (x1 + x2) / 2, y2),
            ("e", x2, (y1 + y2) / 2),
            ("w", x1, (y1 + y2) / 2),
        ]

        for handle_id, hx, hy in edge_handles:
            self.canvas.create_rectangle(
                hx - handle_size/2, hy - handle_size/2,
                hx + handle_size/2, hy + handle_size/2,
                fill="#60a5fa",
                outline="#3b82f6",
                width=1,
                tags=("window", f"handle_{handle_id}")
            )

        # Draw size label
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        self.canvas.create_text(
            center_x, center_y,
            text=f"{self.window_width}x{self.window_height}",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="window"
        )

        # Draw position label
        self.canvas.create_text(
            x1 + 5, y1 + 5,
            text=f"({self.window_x}, {self.window_y})",
            anchor="nw",
            fill="white",
            font=("Arial", 9),
            tags="window"
        )

    def _update_info(self):
        """Update info label"""
        if hasattr(self, 'info_label') and self.info_label:
            self.info_label.configure(
                text=f"Posición: ({self.window_x}, {self.window_y})  •  Tamaño: {self.window_width}x{self.window_height}"
            )

    def _get_handle_at_pos(self, x, y):
        """Get resize handle at position"""
        items = self.canvas.find_overlapping(x-2, y-2, x+2, y+2)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("handle_"):
                    return tag.replace("handle_", "")
        return None

    def _is_inside_window(self, x, y):
        """Check if point is inside window"""
        x1 = self.window_x * self.scale_x
        y1 = self.window_y * self.scale_y
        x2 = (self.window_x + self.window_width) * self.scale_x
        y2 = (self.window_y + self.window_height) * self.scale_y

        return x1 < x < x2 and y1 < y < y2

    def _on_mouse_move(self, event):
        """Handle mouse movement for cursor changes"""
        handle = self._get_handle_at_pos(event.x, event.y)

        if handle:
            # Set cursor based on handle
            cursors = {
                "nw": "top_left_corner",
                "ne": "top_right_corner",
                "sw": "bottom_left_corner",
                "se": "bottom_right_corner",
                "n": "top_side",
                "s": "bottom_side",
                "e": "right_side",
                "w": "left_side"
            }
            self.canvas.configure(cursor=cursors.get(handle, "arrow"))
        elif self._is_inside_window(event.x, event.y):
            self.canvas.configure(cursor="fleur")
        else:
            self.canvas.configure(cursor="arrow")

    def _on_mouse_down(self, event):
        """Handle mouse down"""
        handle = self._get_handle_at_pos(event.x, event.y)

        if handle:
            # Start resizing
            self.resizing = True
            self.resize_handle = handle
            self.resize_start_x = event.x
            self.resize_start_y = event.y
            self.resize_original_rect = (
                self.window_x, self.window_y,
                self.window_width, self.window_height
            )
        elif self._is_inside_window(event.x, event.y):
            # Start dragging
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.drag_offset_x = event.x - self.window_x * self.scale_x
            self.drag_offset_y = event.y - self.window_y * self.scale_y

    def _on_mouse_drag(self, event):
        """Handle mouse drag"""
        if self.dragging:
            # Calculate new position
            new_x = int((event.x - self.drag_offset_x) / self.scale_x)
            new_y = int((event.y - self.drag_offset_y) / self.scale_y)

            # Clamp to screen bounds (considering taskbar)
            max_y = self.screen_height - self.taskbar_height - self.window_height
            new_x = max(0, min(new_x, self.screen_width - self.window_width))
            new_y = max(0, min(new_y, max_y))

            self.window_x = new_x
            self.window_y = new_y

            self._draw_window()
            self._update_info()

            if self.on_change:
                self.on_change()

        elif self.resizing:
            dx = event.x - self.resize_start_x
            dy = event.y - self.resize_start_y

            # Convert to screen coordinates
            dx_screen = int(dx / self.scale_x)
            dy_screen = int(dy / self.scale_y)

            orig_x, orig_y, orig_w, orig_h = self.resize_original_rect

            # Calculate available space (considering taskbar)
            available_height = self.screen_height - self.taskbar_height

            # Apply resize based on handle
            if 'n' in self.resize_handle:
                new_y = orig_y + dy_screen
                new_h = orig_h - dy_screen
                if new_h >= 100:  # Minimum height
                    self.window_y = max(0, new_y)
                    self.window_height = new_h
                    # Ensure doesn't exceed available space
                    if self.window_y + self.window_height > available_height:
                        self.window_height = available_height - self.window_y

            if 's' in self.resize_handle:
                new_h = orig_h + dy_screen
                if new_h >= 100:
                    # Don't exceed available height (screen - taskbar)
                    max_h = available_height - self.window_y
                    self.window_height = min(new_h, max_h)

            if 'w' in self.resize_handle:
                new_x = orig_x + dx_screen
                new_w = orig_w - dx_screen
                if new_w >= 100:  # Minimum width
                    self.window_x = max(0, new_x)
                    self.window_width = new_w
                    # Ensure doesn't exceed screen width
                    if self.window_x + self.window_width > self.screen_width:
                        self.window_width = self.screen_width - self.window_x

            if 'e' in self.resize_handle:
                new_w = orig_w + dx_screen
                if new_w >= 100:
                    # Don't exceed screen width
                    max_w = self.screen_width - self.window_x
                    self.window_width = min(new_w, max_w)

            self._draw_window()
            self._update_info()

            if self.on_change:
                self.on_change()

    def _on_mouse_up(self, event):
        """Handle mouse up"""
        self.dragging = False
        self.resizing = False
        self.resize_handle = None

    def set_values(self, x: int, y: int, width: int, height: int):
        """Set window values programmatically"""
        # If screen dimensions aren't set yet, just store the values
        if self.screen_width is None or self.screen_height is None:
            self.window_x = x
            self.window_y = y
            self.window_width = width
            self.window_height = height
            return

        # Calculate available space (considering taskbar)
        available_height = self.screen_height - self.taskbar_height

        self.window_x = max(0, min(x, self.screen_width - width))
        self.window_y = max(0, min(y, available_height - height))
        self.window_width = max(100, min(width, self.screen_width))
        self.window_height = max(100, min(height, available_height))

        self._draw_window()
        self._update_info()

    def get_values(self) -> tuple:
        """Get current window values"""
        return (self.window_x, self.window_y, self.window_width, self.window_height)

    def set_other_windows(self, other_windows: list):
        """Update the list of other windows to show as guides"""
        self.other_windows = other_windows or []
        self._draw_window()


class ProgramSelectorDialog(ctk.CTkToplevel):
    """Dialog for selecting an installed program"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.result = None
        self.selected_app = None
        self.app_widgets = []
        self.loading = True

        # Window configuration
        self.title("Seleccionar Programa Instalado")
        self.geometry("700x600")
        self.resizable(True, True)

        # Make modal
        self.transient(master)
        self.grab_set()

        # Create UI
        self._create_ui()

        # Start loading programs in background
        self.after(100, self._start_loading_programs)

        # Center window
        self.after(100, self._center_window)

    def _center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the dialog UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="Selecciona un programa instalado",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(0, 10))

        # Search box
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar programa...",
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Loading label
        self.loading_label = ctk.CTkLabel(
            main_frame,
            text="Cargando programas instalados...",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        )
        self.loading_label.pack(pady=5)

        # Programs list (scrollable)
        self.programs_scroll = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=("gray90", "gray17"),
            corner_radius=10
        )
        self.programs_scroll.pack(fill="both", expand=True, pady=(0, 15))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            width=120,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        self.select_btn = ctk.CTkButton(
            button_frame,
            text="Seleccionar",
            width=120,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            command=self._select,
            state="disabled"
        )
        self.select_btn.pack(side="right")

    def _start_loading_programs(self):
        """Start loading programs in a background thread"""
        thread = threading.Thread(target=self._load_programs, daemon=True)
        thread.start()

    def _load_programs(self):
        """Load installed programs (runs in background thread)"""
        from workspace_manager.app_finder import find_all_installed_programs

        count = 0
        for app_info in find_all_installed_programs():
            # Update UI in main thread
            self.after(0, lambda a=app_info: self._add_program_to_list(a))
            count += 1

        # Finished loading
        self.after(0, self._finish_loading)

    def _add_program_to_list(self, app_info):
        """Add a program to the list (called from main thread)"""
        from workspace_manager.app_finder import AppInfo

        # Create program card
        card = ctk.CTkFrame(
            self.programs_scroll,
            fg_color=("white", "gray20"),
            corner_radius=8,
            cursor="hand2"
        )
        card.pack(fill="x", pady=3, padx=5)

        # Store app info in widget
        card.app_info = app_info
        card.search_text = app_info.name.lower()

        # Make card clickable
        card.bind("<Button-1>", lambda e, c=card: self._select_program(c))

        # Content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=10, pady=10)
        content.bind("<Button-1>", lambda e, c=card: self._select_program(c))

        # Icon
        if app_info.icon_data:
            try:
                pil_image = Image.open(io.BytesIO(app_info.icon_data))
                # Convert to CTkImage
                icon = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(48, 48)
                )
                icon_label = ctk.CTkLabel(content, image=icon, text="")
                icon_label.image = icon  # Keep reference
                icon_label.pack(side="left", padx=(0, 15))
                icon_label.bind("<Button-1>", lambda e, c=card: self._select_program(c))
            except Exception:
                pass

        # Info frame
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        info_frame.bind("<Button-1>", lambda e, c=card: self._select_program(c))

        # Program name
        name_label = ctk.CTkLabel(
            info_frame,
            text=app_info.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        name_label.pack(fill="x")
        name_label.bind("<Button-1>", lambda e, c=card: self._select_program(c))

        # Exe path
        path_label = ctk.CTkLabel(
            info_frame,
            text=app_info.exe_path,
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
            anchor="w"
        )
        path_label.pack(fill="x")
        path_label.bind("<Button-1>", lambda e, c=card: self._select_program(c))

        # Store widget for search
        self.app_widgets.append(card)

    def _finish_loading(self):
        """Called when loading is complete"""
        self.loading = False
        self.loading_label.configure(text=f"Encontrados {len(self.app_widgets)} programas")

    def _select_program(self, card):
        """Select a program card"""
        # Deselect all cards
        for widget in self.app_widgets:
            widget.configure(border_width=0)

        # Select this card
        card.configure(border_width=2, border_color=("#3b82f6", "#2563eb"))

        # Store selection
        self.selected_app = card.app_info

        # Enable select button
        self.select_btn.configure(state="normal")

    def _on_search(self, event=None):
        """Filter programs based on search"""
        search_term = self.search_entry.get().lower()

        visible_count = 0
        for widget in self.app_widgets:
            if search_term in widget.search_text:
                widget.pack(fill="x", pady=3, padx=5)
                visible_count += 1
            else:
                widget.pack_forget()

        # Update loading label
        if self.loading:
            self.loading_label.configure(text="Cargando programas instalados...")
        else:
            self.loading_label.configure(
                text=f"Mostrando {visible_count} de {len(self.app_widgets)} programas"
            )

    def _select(self):
        """Confirm selection"""
        if self.selected_app:
            self.result = {
                "name": self.selected_app.name,
                "exe_path": self.selected_app.exe_path
            }
            self.grab_release()
            self.destroy()

    def _cancel(self):
        """Cancel selection"""
        self.result = None
        self.grab_release()
        self.destroy()


class AppConfigDialog(ctk.CTkToplevel):
    """Dialog for configuring a single application instance"""

    def __init__(self, master, app_data: Optional[Dict[str, Any]] = None, all_apps: Optional[List[Dict[str, Any]]] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.result = None
        self.app_data = app_data or {}
        self.all_apps = all_apps or []  # All apps in the workspace to show as guides

        # Window configuration
        self.title("Configurar Aplicación")
        self.geometry("750x900")
        self.resizable(True, True)

        # Make modal
        self.transient(master)
        self.grab_set()

        # Create UI
        self._create_ui()

        # Load existing data if editing
        if app_data:
            self._load_data(app_data)

        # Center window
        self.after(100, self._center_window)

    def _center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the dialog UI"""
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Scrollable frame for form
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        # App ID
        ctk.CTkLabel(scroll_frame, text="ID de la Aplicación:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.id_entry = ctk.CTkEntry(scroll_frame, placeholder_text="ej: vscode-1, chrome-main, terminal-dev")
        self.id_entry.pack(fill="x", pady=(0, 15))

        # Executable section
        ctk.CTkLabel(scroll_frame, text="Ejecutable:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))

        exe_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        exe_frame.pack(fill="x", pady=(0, 15))

        self.exe_entry = ctk.CTkEntry(exe_frame, placeholder_text="Ruta al ejecutable (.exe)")
        self.exe_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Button container for exe selection
        exe_buttons = ctk.CTkFrame(exe_frame, fg_color="transparent")
        exe_buttons.pack(side="right")

        browse_installed_btn = ctk.CTkButton(
            exe_buttons,
            text="Programas Instalados",
            width=150,
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            command=self._browse_installed_programs
        )
        browse_installed_btn.pack(side="left", padx=(0, 5))

        browse_exe_btn = ctk.CTkButton(
            exe_buttons,
            text="Buscar Archivo...",
            width=120,
            command=self._browse_exe
        )
        browse_exe_btn.pack(side="left")

        # Working directory section
        ctk.CTkLabel(scroll_frame, text="Carpeta de trabajo / Proyecto:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))

        work_dir_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        work_dir_frame.pack(fill="x", pady=(0, 15))

        self.work_dir_entry = ctk.CTkEntry(work_dir_frame, placeholder_text="Carpeta inicial (opcional)")
        self.work_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_dir_btn = ctk.CTkButton(work_dir_frame, text="Buscar...", width=100, command=self._browse_directory)
        browse_dir_btn.pack(side="right")

        # Arguments section
        ctk.CTkLabel(scroll_frame, text="Argumentos adicionales:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.args_entry = ctk.CTkEntry(scroll_frame, placeholder_text='ej: --profile "Default" o archivo.txt (separados por espacio)')
        self.args_entry.pack(fill="x", pady=(0, 15))

        # Virtual Desktop
        ctk.CTkLabel(scroll_frame, text="Escritorio Virtual:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))

        desktop_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        desktop_frame.pack(fill="x", pady=(0, 15))

        self.desktop_var = ctk.IntVar(value=0)
        self.desktop_spinbox = ctk.CTkEntry(desktop_frame, width=100, textvariable=self.desktop_var)
        self.desktop_spinbox.pack(side="left")
        # Bind to update guides when desktop changes
        self.desktop_spinbox.bind("<KeyRelease>", self._on_desktop_change)

        ctk.CTkLabel(desktop_frame, text="(0 = primer escritorio, 1 = segundo, etc.)",
                     text_color=("gray50", "gray60")).pack(side="left", padx=10)

        # Window configuration section
        window_label = ctk.CTkLabel(scroll_frame, text="Configuración de Ventana:",
                                      font=ctk.CTkFont(size=13, weight="bold"))
        window_label.pack(anchor="w", pady=(10, 10))

        # Get initial desktop (use current app's desktop if editing, otherwise 0)
        initial_desktop = self.app_data.get("virtual_desktop", 0) if self.app_data else 0

        # Get initial other windows for the same desktop
        initial_other_windows = self._get_other_windows_for_desktop(initial_desktop)

        # Visual window position selector
        self.position_selector = WindowPositionSelector(
            scroll_frame,
            on_change=self._on_position_change,
            other_windows=initial_other_windows,
            fg_color=("gray90", "gray17"),
            corner_radius=10
        )
        self.position_selector.pack(fill="both", expand=True, pady=(0, 15))

        # Manual entry fields (read-only, updated from visual selector)
        manual_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray90", "gray17"), corner_radius=10)
        manual_frame.pack(fill="x", pady=(0, 15), padx=5)

        manual_header = ctk.CTkLabel(
            manual_frame,
            text="O introduce valores manualmente:",
            font=ctk.CTkFont(size=11)
        )
        manual_header.pack(anchor="w", padx=15, pady=(10, 5))

        # Position
        pos_frame = ctk.CTkFrame(manual_frame, fg_color="transparent")
        pos_frame.pack(fill="x", padx=15, pady=5)

        pos_inputs = ctk.CTkFrame(pos_frame, fg_color="transparent")
        pos_inputs.pack(fill="x")

        ctk.CTkLabel(pos_inputs, text="X:", width=60).pack(side="left", padx=(0, 5))
        self.x_entry = ctk.CTkEntry(pos_inputs, width=100, placeholder_text="0")
        self.x_entry.pack(side="left", padx=(0, 20))
        self.x_entry.bind("<KeyRelease>", self._on_manual_entry_change)

        ctk.CTkLabel(pos_inputs, text="Y:", width=60).pack(side="left", padx=(0, 5))
        self.y_entry = ctk.CTkEntry(pos_inputs, width=100, placeholder_text="0")
        self.y_entry.pack(side="left")
        self.y_entry.bind("<KeyRelease>", self._on_manual_entry_change)

        # Size
        size_frame = ctk.CTkFrame(manual_frame, fg_color="transparent")
        size_frame.pack(fill="x", padx=15, pady=(5, 15))

        size_inputs = ctk.CTkFrame(size_frame, fg_color="transparent")
        size_inputs.pack(fill="x")

        ctk.CTkLabel(size_inputs, text="Ancho:", width=60).pack(side="left", padx=(0, 5))
        self.width_entry = ctk.CTkEntry(size_inputs, width=100, placeholder_text="800")
        self.width_entry.pack(side="left", padx=(0, 20))
        self.width_entry.bind("<KeyRelease>", self._on_manual_entry_change)

        ctk.CTkLabel(size_inputs, text="Alto:", width=60).pack(side="left", padx=(0, 5))
        self.height_entry = ctk.CTkEntry(size_inputs, width=100, placeholder_text="600")
        self.height_entry.pack(side="left")
        self.height_entry.bind("<KeyRelease>", self._on_manual_entry_change)

        # Buttons at bottom
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))

        cancel_btn = ctk.CTkButton(button_frame, text="Cancelar", width=120,
                                    fg_color=("gray75", "gray30"),
                                    hover_color=("gray65", "gray40"),
                                    command=self._cancel)
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(button_frame, text="Guardar", width=120,
                                  fg_color=("#3b82f6", "#2563eb"),
                                  hover_color=("#2563eb", "#1d4ed8"),
                                  command=self._save)
        save_btn.pack(side="right")

    def _browse_exe(self):
        """Browse for executable file"""
        filename = filedialog.askopenfilename(
            title="Seleccionar Ejecutable",
            filetypes=[
                ("Ejecutables", "*.exe"),
                ("Todos los archivos", "*.*")
            ]
        )
        if filename:
            self.exe_entry.delete(0, 'end')
            self.exe_entry.insert(0, filename)

    def _browse_installed_programs(self):
        """Browse for installed programs"""
        dialog = ProgramSelectorDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            # Set exe path
            self.exe_entry.delete(0, 'end')
            self.exe_entry.insert(0, dialog.result["exe_path"])

            # Auto-fill ID if empty
            if not self.id_entry.get().strip():
                # Generate a simple ID from program name
                program_name = dialog.result["name"]
                # Remove special characters and spaces
                simple_id = program_name.lower().replace(" ", "-")
                simple_id = ''.join(c for c in simple_id if c.isalnum() or c == '-')
                self.id_entry.delete(0, 'end')
                self.id_entry.insert(0, simple_id)

    def _browse_directory(self):
        """Browse for working directory"""
        dirname = filedialog.askdirectory(
            title="Seleccionar Carpeta de Trabajo"
        )
        if dirname:
            self.work_dir_entry.delete(0, 'end')
            self.work_dir_entry.insert(0, dirname)

    def _on_position_change(self):
        """Called when position selector changes"""
        x, y, width, height = self.position_selector.get_values()

        # Update entry fields
        self.x_entry.delete(0, 'end')
        self.x_entry.insert(0, str(x))

        self.y_entry.delete(0, 'end')
        self.y_entry.insert(0, str(y))

        self.width_entry.delete(0, 'end')
        self.width_entry.insert(0, str(width))

        self.height_entry.delete(0, 'end')
        self.height_entry.insert(0, str(height))

    def _on_manual_entry_change(self, event=None):
        """Called when manual entry fields change"""
        try:
            x = int(self.x_entry.get() or "0")
            y = int(self.y_entry.get() or "0")
            width = int(self.width_entry.get() or "800")
            height = int(self.height_entry.get() or "600")

            # Update position selector
            self.position_selector.set_values(x, y, width, height)
        except ValueError:
            # Ignore invalid input
            pass

    def _on_desktop_change(self, event=None):
        """Called when desktop selection changes"""
        try:
            desktop_idx = int(self.desktop_var.get())
            # Update the guides to show other windows in the same desktop
            other_windows = self._get_other_windows_for_desktop(desktop_idx)
            self.position_selector.set_other_windows(other_windows)
        except ValueError:
            # Ignore invalid input
            pass

    def _get_other_windows_for_desktop(self, desktop_idx: int) -> List[Dict[str, Any]]:
        """Get other windows configured for the same desktop"""
        other_windows = []

        # Get current app ID if editing
        current_app_id = self.app_data.get("id", "")

        for app in self.all_apps:
            # Skip if it's the current app being edited
            if app.get("id") == current_app_id:
                continue

            # Only include apps from the same desktop
            if app.get("virtual_desktop", 0) == desktop_idx:
                window = app.get("window", {})
                other_windows.append({
                    "x": window.get("x", 0),
                    "y": window.get("y", 0),
                    "width": window.get("width", 800),
                    "height": window.get("height", 600),
                    "app_id": app.get("id", "unknown")
                })

        return other_windows

    def _load_data(self, data: Dict[str, Any]):
        """Load existing application data"""
        self.id_entry.insert(0, data.get("id", ""))
        self.exe_entry.insert(0, data.get("exe", ""))

        if data.get("working_dir"):
            self.work_dir_entry.insert(0, data["working_dir"])

        if data.get("args"):
            self.args_entry.insert(0, " ".join(data["args"]))

        self.desktop_var.set(data.get("virtual_desktop", 0))

        window = data.get("window", {})
        x = window.get("x", 0)
        y = window.get("y", 0)
        width = window.get("width", 800)
        height = window.get("height", 600)

        # Load into position selector (which will update the entry fields)
        self.position_selector.set_values(x, y, width, height)
        self._on_position_change()

    def _validate(self) -> bool:
        """Validate form data"""
        if not self.id_entry.get().strip():
            messagebox.showerror("Error", "El ID de la aplicación es requerido")
            return False

        if not self.exe_entry.get().strip():
            messagebox.showerror("Error", "El ejecutable es requerido")
            return False

        # Validate numeric fields
        try:
            int(self.x_entry.get() or "0")
            int(self.y_entry.get() or "0")
            width = int(self.width_entry.get() or "800")
            height = int(self.height_entry.get() or "600")

            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")

        except ValueError:
            messagebox.showerror("Error", "Los valores de posición y tamaño deben ser números válidos")
            return False

        return True

    def _save(self):
        """Save the application configuration"""
        if not self._validate():
            return

        # Parse arguments
        args_text = self.args_entry.get().strip()
        args = []
        if args_text:
            # Simple split by space (TODO: handle quoted strings properly)
            import shlex
            try:
                args = shlex.split(args_text)
            except:
                args = args_text.split()

        # Build result
        self.result = {
            "id": self.id_entry.get().strip(),
            "exe": self.exe_entry.get().strip(),
            "args": args,
            "working_dir": self.work_dir_entry.get().strip() or None,
            "virtual_desktop": self.desktop_var.get(),
            "window": {
                "x": int(self.x_entry.get() or "0"),
                "y": int(self.y_entry.get() or "0"),
                "width": int(self.width_entry.get() or "800"),
                "height": int(self.height_entry.get() or "600")
            }
        }

        self.grab_release()
        self.destroy()

    def _cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.grab_release()
        self.destroy()


class WorkspaceDialog(ctk.CTkToplevel):
    """Dialog for creating/editing a workspace"""

    def __init__(self, master, workspace_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(master, **kwargs)

        self.result = None
        self.workspace_data = workspace_data or {"apps": []}
        self.apps = list(workspace_data.get("apps", []) if workspace_data else [])

        # Window configuration
        title = "Editar Workspace" if workspace_data else "Nuevo Workspace"
        self.title(title)
        self.geometry("900x700")
        self.resizable(True, True)

        # Make modal
        self.transient(master)
        self.grab_set()

        # Create UI
        self._create_ui()

        # Load existing data if editing
        if workspace_data:
            self._load_data(workspace_data)

        # Center window
        self.after(100, self._center_window)

    def _center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the dialog UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header, text="Configuración del Workspace",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")

        # Basic info section
        info_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray17"), corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))

        # Name
        name_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_container.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(name_container, text="Nombre:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(name_container, placeholder_text="Nombre del workspace")
        self.name_entry.pack(fill="x")

        # Description
        desc_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        desc_container.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(desc_container, text="Descripción:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.desc_entry = ctk.CTkEntry(desc_container, placeholder_text="Descripción opcional")
        self.desc_entry.pack(fill="x")

        # Applications section
        apps_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        apps_header.pack(fill="x", pady=(10, 10))

        ctk.CTkLabel(apps_header, text="Aplicaciones:",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        add_app_btn = ctk.CTkButton(apps_header, text="+ Agregar Aplicación", width=150,
                                     fg_color=("#3b82f6", "#2563eb"),
                                     hover_color=("#2563eb", "#1d4ed8"),
                                     command=self._add_app)
        add_app_btn.pack(side="right")

        # Apps list (scrollable)
        self.apps_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent", height=300)
        self.apps_scroll.pack(fill="both", expand=True, pady=(0, 15))

        self._refresh_apps_list()

        # Buttons at bottom
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(button_frame, text="Cancelar", width=120,
                                    fg_color=("gray75", "gray30"),
                                    hover_color=("gray65", "gray40"),
                                    command=self._cancel)
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(button_frame, text="Guardar Workspace", width=150,
                                  fg_color=("#10b981", "#059669"),
                                  hover_color=("#059669", "#047857"),
                                  command=self._save)
        save_btn.pack(side="right")

    def _load_data(self, data: Dict[str, Any]):
        """Load existing workspace data"""
        self.name_entry.insert(0, data.get("name", ""))
        self.desc_entry.insert(0, data.get("description", ""))

    def _refresh_apps_list(self):
        """Refresh the applications list display"""
        # Clear current list
        for widget in self.apps_scroll.winfo_children():
            widget.destroy()

        if not self.apps:
            # Empty state
            empty_label = ctk.CTkLabel(
                self.apps_scroll,
                text="No hay aplicaciones configuradas\n\nHaz clic en '+ Agregar Aplicación' para comenzar",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60")
            )
            empty_label.pack(pady=50)
            return

        # Group apps by virtual desktop
        desktop_apps = {}
        for app in self.apps:
            desktop = app.get("virtual_desktop", 0)
            if desktop not in desktop_apps:
                desktop_apps[desktop] = []
            desktop_apps[desktop].append(app)

        # Display apps grouped by virtual desktop
        for desktop_idx, apps_list in sorted(desktop_apps.items()):
            # Desktop header
            desktop_header = ctk.CTkFrame(self.apps_scroll, fg_color=("gray85", "gray20"), corner_radius=8)
            desktop_header.pack(fill="x", pady=(5, 2), padx=5)

            ctk.CTkLabel(desktop_header, text=f"Escritorio Virtual {desktop_idx}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=("#3b82f6", "#60a5fa")).pack(side="left", padx=15, pady=8)

            # Apps in this desktop
            for app in apps_list:
                app_card = ctk.CTkFrame(self.apps_scroll, fg_color=("gray90", "gray17"), corner_radius=8)
                app_card.pack(fill="x", pady=2, padx=10)

                app_info_frame = ctk.CTkFrame(app_card, fg_color="transparent")
                app_info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)

                # App ID and exe
                id_label = ctk.CTkLabel(app_info_frame, text=app.get("id", "unknown"),
                                         font=ctk.CTkFont(size=13, weight="bold"),
                                         anchor="w")
                id_label.pack(anchor="w")

                exe_name = Path(app.get("exe", "")).name
                exe_label = ctk.CTkLabel(app_info_frame, text=exe_name,
                                          font=ctk.CTkFont(size=11),
                                          text_color=("gray50", "gray60"),
                                          anchor="w")
                exe_label.pack(anchor="w")

                # Window info
                window = app.get("window", {})
                size_text = f"{window.get('width', 0)}x{window.get('height', 0)} @ ({window.get('x', 0)}, {window.get('y', 0)})"
                size_label = ctk.CTkLabel(app_info_frame, text=size_text,
                                           font=ctk.CTkFont(size=10),
                                           text_color=("gray50", "gray60"),
                                           anchor="w")
                size_label.pack(anchor="w")

                # Buttons
                button_frame = ctk.CTkFrame(app_card, fg_color="transparent")
                button_frame.pack(side="right", padx=10)

                edit_btn = ctk.CTkButton(button_frame, text="Editar", width=70, height=28,
                                          fg_color=("gray75", "gray30"),
                                          hover_color=("gray65", "gray40"),
                                          command=lambda a=app: self._edit_app(a))
                edit_btn.pack(side="left", padx=2)

                delete_btn = ctk.CTkButton(button_frame, text="Eliminar", width=70, height=28,
                                            fg_color=("#ef4444", "#dc2626"),
                                            hover_color=("#dc2626", "#b91c1c"),
                                            command=lambda a=app: self._delete_app(a))
                delete_btn.pack(side="left", padx=2)

    def _add_app(self):
        """Add a new application"""
        dialog = AppConfigDialog(self, all_apps=self.apps)
        self.wait_window(dialog)

        if dialog.result:
            self.apps.append(dialog.result)
            self._refresh_apps_list()

    def _edit_app(self, app: Dict[str, Any]):
        """Edit an existing application"""
        dialog = AppConfigDialog(self, app_data=app, all_apps=self.apps)
        self.wait_window(dialog)

        if dialog.result:
            # Replace the app in the list
            for i, a in enumerate(self.apps):
                if a.get("id") == app.get("id"):
                    self.apps[i] = dialog.result
                    break
            self._refresh_apps_list()

    def _delete_app(self, app: Dict[str, Any]):
        """Delete an application"""
        if messagebox.askyesno("Confirmar", f"¿Eliminar la aplicación '{app.get('id')}'?"):
            self.apps = [a for a in self.apps if a.get("id") != app.get("id")]
            self._refresh_apps_list()

    def _validate(self) -> bool:
        """Validate workspace data"""
        if not self.name_entry.get().strip():
            messagebox.showerror("Error", "El nombre del workspace es requerido")
            return False

        if not self.apps:
            messagebox.showwarning("Advertencia", "No hay aplicaciones configuradas en este workspace")
            # Allow empty workspace but warn user

        return True

    def _save(self):
        """Save the workspace configuration"""
        if not self._validate():
            return

        self.result = {
            "name": self.name_entry.get().strip(),
            "description": self.desc_entry.get().strip(),
            "apps": self.apps
        }

        self.grab_release()
        self.destroy()

    def _cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.grab_release()
        self.destroy()


class WorkspaceCard(ctk.CTkFrame):
    """A card widget displaying workspace information"""

    def __init__(self, master, workspace: Dict[str, Any], refresh_callback=None, **kwargs):
        super().__init__(master, **kwargs)

        self.workspace = workspace
        self.refresh_callback = refresh_callback
        self.is_collapsed = True  # Start collapsed by default
        self.configure(fg_color=("gray85", "gray20"), corner_radius=10)

        # Header with name and description
        header_frame = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))

        # Make the entire header clickable
        header_frame.bind("<Button-1>", lambda e: self._toggle_collapse())

        # Collapse/Expand indicator
        self.toggle_btn = ctk.CTkLabel(
            header_frame,
            text="▶",
            width=30,
            font=ctk.CTkFont(size=14),
            cursor="hand2"
        )
        self.toggle_btn.pack(side="left", padx=(0, 10))
        self.toggle_btn.bind("<Button-1>", lambda e: self._toggle_collapse())

        # Left section for name (clickable)
        left_section = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_section.pack(side="left", fill="x", expand=True)
        left_section.bind("<Button-1>", lambda e: self._toggle_collapse())

        name_label = ctk.CTkLabel(
            left_section,
            text=workspace.get("name", "Unnamed"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
            cursor="hand2"
        )
        name_label.pack(fill="x")
        name_label.bind("<Button-1>", lambda e: self._toggle_collapse())

        # Right section for buttons (not clickable for toggle)
        button_section = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_section.pack(side="right")

        # Delete button (trash icon only)
        delete_btn = ctk.CTkButton(
            button_section,
            text="🗑",
            width=28,
            height=28,
            font=ctk.CTkFont(size=15),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            command=lambda: self._delete_workspace()
        )
        delete_btn.pack(side="left", padx=3)

        # Edit button
        edit_btn = ctk.CTkButton(
            button_section,
            text="Editar",
            width=80,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=lambda: self._edit_workspace()
        )
        edit_btn.pack(side="left", padx=5)

        # Launch button
        launch_btn = ctk.CTkButton(
            button_section,
            text="Lanzar",
            width=80,
            height=28,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            command=lambda: self._launch_workspace()
        )
        launch_btn.pack(side="left")

        # Summary section (always visible when collapsed)
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Create summary text
        apps = workspace.get("apps", [])
        num_apps = len(apps)
        num_desktops = len(set(app.get("virtual_desktop", 0) for app in apps)) if apps else 0

        summary_text = f"{num_apps} aplicación{'es' if num_apps != 1 else ''}"
        if num_desktops > 0:
            summary_text += f" • {num_desktops} escritorio{'s' if num_desktops != 1 else ''} virtual{'es' if num_desktops != 1 else ''}"

        if workspace.get("description"):
            summary_text = workspace["description"][:80] + ("..." if len(workspace["description"]) > 80 else "")
            summary_text += f" • {num_apps} app{'s' if num_apps != 1 else ''}"

        self.summary_label = ctk.CTkLabel(
            self.summary_frame,
            text=summary_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w"
        )
        self.summary_label.pack(fill="x")

        # Details section (collapsible)
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Description (in details)
        if workspace.get("description"):
            desc_label = ctk.CTkLabel(
                self.details_frame,
                text=workspace["description"],
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60"),
                anchor="w",
                justify="left"
            )
            desc_label.pack(fill="x", padx=15, pady=(0, 10))

        # Apps section (in details)
        if apps:
            apps_label = ctk.CTkLabel(
                self.details_frame,
                text=f"Aplicaciones ({len(apps)}):",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            apps_label.pack(fill="x", padx=15, pady=(5, 5))

            # Apps container
            apps_container = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            apps_container.pack(fill="x", padx=15, pady=(0, 15))

            # Group apps by virtual desktop
            desktop_apps = {}
            for app in apps:
                desktop = app.get("virtual_desktop", 0)
                if desktop not in desktop_apps:
                    desktop_apps[desktop] = []
                desktop_apps[desktop].append(app)

            # Display apps grouped by virtual desktop
            for desktop_idx, desktop_apps_list in sorted(desktop_apps.items()):
                desktop_frame = ctk.CTkFrame(
                    apps_container,
                    fg_color=("gray90", "gray17"),
                    corner_radius=6
                )
                desktop_frame.pack(fill="x", pady=3)

                # Desktop header
                desktop_header = ctk.CTkLabel(
                    desktop_frame,
                    text=f"Escritorio Virtual {desktop_idx}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=("#3b82f6", "#60a5fa"),
                    anchor="w"
                )
                desktop_header.pack(fill="x", padx=10, pady=(8, 5))

                # Apps in this desktop
                for app in desktop_apps_list:
                    app_frame = ctk.CTkFrame(desktop_frame, fg_color="transparent")
                    app_frame.pack(fill="x", padx=10, pady=2)

                    # App icon/bullet
                    bullet = ctk.CTkLabel(
                        app_frame,
                        text="•",
                        font=ctk.CTkFont(size=14),
                        width=20
                    )
                    bullet.pack(side="left")

                    # App info
                    app_id = app.get("id", "unknown")
                    exe_name = Path(app.get("exe", "")).name

                    app_label = ctk.CTkLabel(
                        app_frame,
                        text=f"{app_id}",
                        font=ctk.CTkFont(size=11),
                        anchor="w"
                    )
                    app_label.pack(side="left", fill="x", expand=True)

                    # Window size info
                    window = app.get("window", {})
                    if window:
                        size_text = f"{window.get('width', 0)}x{window.get('height', 0)}"
                        size_label = ctk.CTkLabel(
                            app_frame,
                            text=size_text,
                            font=ctk.CTkFont(size=10),
                            text_color=("gray50", "gray60")
                        )
                        size_label.pack(side="right", padx=5)

                # Add bottom padding to desktop frame
                ctk.CTkLabel(desktop_frame, text="", height=5).pack()

        # Start in collapsed state (don't pack details_frame)

    def _toggle_collapse(self):
        """Toggle between collapsed and expanded states"""
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            # Collapse: hide details, show summary
            self.details_frame.pack_forget()
            # Find the header frame to pack after it
            header = self.toggle_btn.master
            self.summary_frame.pack(fill="x", padx=15, pady=(0, 10), after=header)
            self.toggle_btn.configure(text="▶")
        else:
            # Expand: hide summary, show details
            self.summary_frame.pack_forget()
            # Find the header frame to pack after it
            header = self.toggle_btn.master
            self.details_frame.pack(fill="x", padx=0, pady=(0, 0), after=header)
            self.toggle_btn.configure(text="▼")

    def _launch_workspace(self):
        """Launch this workspace"""
        workspace_name = self.workspace.get("name", "Unnamed")
        num_apps = len(self.workspace.get("apps", []))

        # Show confirmation dialog
        result = messagebox.askyesno(
            "Lanzar Workspace",
            f"¿Deseas lanzar el workspace '{workspace_name}'?\n\n"
            f"Se iniciarán {num_apps} aplicación{'es' if num_apps != 1 else ''}.",
            icon='question'
        )

        if not result:
            return

        # Launch in background thread to avoid blocking UI
        def launch_thread():
            from workspace_manager.launcher import launch_workspace
            try:
                success = launch_workspace(self.workspace)

                # Only show errors or warnings
                if not success:
                    self.after(0, lambda: messagebox.showwarning(
                        "Workspace Lanzado con Advertencias",
                        f"Workspace '{workspace_name}' lanzado pero algunas aplicaciones no se iniciaron correctamente.\n\n"
                        "Revisa la consola para más detalles."
                    ))
            except Exception as e:
                # Show error in main thread
                self.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Error al lanzar workspace: {str(e)}"
                ))

        # Start launch thread
        thread = threading.Thread(target=launch_thread, daemon=True)
        thread.start()

    def _delete_workspace(self):
        """Delete workspace with confirmation"""
        workspace_name = self.workspace.get("name", "Unnamed")

        # Show confirmation dialog
        result = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar el workspace '{workspace_name}'?\n\n"
            "Esta acción no se puede deshacer.",
            icon='warning'
        )

        if result:
            try:
                # Load current workspaces
                config_path = get_default_config_path()

                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Filter out the workspace to delete
                workspaces = data.get("workspaces", [])
                workspaces = [w for w in workspaces if w.get("name") != workspace_name]

                # Save updated workspaces
                data["workspaces"] = workspaces

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo(
                    "Workspace Eliminado",
                    f"Workspace '{workspace_name}' eliminado exitosamente!"
                )

                # Refresh the list
                if self.refresh_callback:
                    self.refresh_callback()

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al eliminar workspace: {str(e)}"
                )

    def _edit_workspace(self):
        """Edit workspace"""
        dialog = WorkspaceDialog(self.master.master, workspace_data=self.workspace)
        self.wait_window(dialog)

        if dialog.result:
            # Import config manager and save
            from workspace_manager.config import ConfigManager
            from workspace_manager.models import Workspace, AppInstance, WindowConfig

            # Convert dialog result to Workspace model
            workspace = Workspace(
                name=dialog.result["name"],
                description=dialog.result["description"],
                apps=[]
            )

            for app_data in dialog.result["apps"]:
                app = AppInstance(
                    id=app_data["id"],
                    exe=app_data["exe"],
                    args=app_data.get("args", []),
                    working_dir=app_data.get("working_dir"),
                    virtual_desktop=app_data.get("virtual_desktop", 0),
                    window=WindowConfig(
                        x=app_data["window"]["x"],
                        y=app_data["window"]["y"],
                        width=app_data["window"]["width"],
                        height=app_data["window"]["height"]
                    )
                )
                workspace.add_app(app)

            try:
                config_manager = ConfigManager()  # Uses default path in Documents
                config_manager.add_workspace(workspace, overwrite=True)

                messagebox.showinfo(
                    "Workspace Guardado",
                    f"Workspace '{workspace.name}' guardado exitosamente!"
                )

                # Refresh the list
                if self.refresh_callback:
                    self.refresh_callback()

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al guardar workspace: {str(e)}"
                )


class WorkspaceManagerGUI(ctk.CTk):
    """Main GUI application for Workspace Manager"""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Workspace Manager")
        self.geometry("900x700")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Load workspaces
        self.workspaces = self._load_workspaces()

        # Create UI
        self._create_header()
        self._create_workspace_list()

    def _load_workspaces(self) -> List[Dict[str, Any]]:
        """Load workspaces from JSON file"""
        config_path = get_default_config_path()

        # If file doesn't exist, return empty list (will be created on first save)
        if not config_path.exists():
            return []

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("workspaces", [])
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al cargar workspaces:\n{str(e)}"
            )
            return []

    def _create_header(self):
        """Create the header section"""
        header = ctk.CTkFrame(self, fg_color="transparent", height=80)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        # Title
        title_label = ctk.CTkLabel(
            header,
            text="Workspace Manager",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left", anchor="w")

        # Button container
        button_frame = ctk.CTkFrame(header, fg_color="transparent")
        button_frame.pack(side="right", anchor="e")

        # New workspace button
        new_btn = ctk.CTkButton(
            button_frame,
            text="+ Nuevo Workspace",
            width=160,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            command=self._new_workspace
        )
        new_btn.pack(side="right", padx=5)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="⟳ Actualizar",
            width=120,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._refresh_workspaces
        )
        refresh_btn.pack(side="right", padx=5)

    def _create_workspace_list(self):
        """Create the scrollable workspace list"""
        # Container frame
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        self.scroll_frame.pack(fill="both", expand=True)

        # Add workspace cards
        if not self.workspaces:
            # Empty state
            empty_label = ctk.CTkLabel(
                self.scroll_frame,
                text="No hay workspaces configurados\n\nHaz clic en '+ Nuevo Workspace' para crear uno",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray60")
            )
            empty_label.pack(pady=100)
        else:
            for workspace in self.workspaces:
                card = WorkspaceCard(self.scroll_frame, workspace, refresh_callback=self._refresh_workspaces)
                card.pack(fill="x", pady=8, padx=5)

    def _new_workspace(self):
        """Create new workspace"""
        dialog = WorkspaceDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            # Import config manager and save
            from workspace_manager.config import ConfigManager
            from workspace_manager.models import Workspace, AppInstance, WindowConfig

            # Convert dialog result to Workspace model
            workspace = Workspace(
                name=dialog.result["name"],
                description=dialog.result["description"],
                apps=[]
            )

            for app_data in dialog.result["apps"]:
                app = AppInstance(
                    id=app_data["id"],
                    exe=app_data["exe"],
                    args=app_data.get("args", []),
                    working_dir=app_data.get("working_dir"),
                    virtual_desktop=app_data.get("virtual_desktop", 0),
                    window=WindowConfig(
                        x=app_data["window"]["x"],
                        y=app_data["window"]["y"],
                        width=app_data["window"]["width"],
                        height=app_data["window"]["height"]
                    )
                )
                workspace.add_app(app)

            try:
                config_manager = ConfigManager()  # Uses default path in Documents
                config_manager.add_workspace(workspace, overwrite=False)

                messagebox.showinfo(
                    "Workspace Creado",
                    f"Workspace '{workspace.name}' creado exitosamente!"
                )

                # Refresh the list
                self._refresh_workspaces()

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al crear workspace: {str(e)}"
                )

    def _refresh_workspaces(self):
        """Refresh the workspace list"""
        # Reload workspaces
        self.workspaces = self._load_workspaces()

        # Clear current workspace list
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Recreate workspace cards
        if not self.workspaces:
            empty_label = ctk.CTkLabel(
                self.scroll_frame,
                text="No hay workspaces configurados\n\nHaz clic en '+ Nuevo Workspace' para crear uno",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray60")
            )
            empty_label.pack(pady=100)
        else:
            for workspace in self.workspaces:
                card = WorkspaceCard(self.scroll_frame, workspace, refresh_callback=self._refresh_workspaces)
                card.pack(fill="x", pady=8, padx=5)


def run_gui():
    """Launch the GUI application"""
    app = WorkspaceManagerGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
