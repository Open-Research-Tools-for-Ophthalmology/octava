from pathlib import Path
from tkinter import (
    messagebox,
    Canvas,
    Toplevel,
    Frame,
    Label,
)
from theme import *
import customtkinter as ctk
from tkinter import Canvas
import numpy as np
from modules.resize_image import *
from PIL import Image, ImageTk
from modules.load_image import load_image
from resource_path import ICONS_PATH


def subwindow_subset(canvas):
    # Check if an image is loaded
    if not hasattr(canvas, "original_img"):
        messagebox.showwarning(
            "No Image Loaded", "Please load an image before processing."
        )
        return

    subwindow_subset = Toplevel()
    subwindow_subset.title("Subset Editor")
    subwindow_subset.geometry("800x650")
    subwindow_subset.configure(bg="#FBE3D6")

    # States
    subwindow_subset.original_pil = Image.fromarray(
        canvas.original_img.astype(np.uint8), mode="L"
    )
    subwindow_subset.zoom_level = 1.0
    subwindow_subset.active_tool = "draw"  # "draw", "pan", "zoom"
    subwindow_subset.sq_start = None  # Start point of square
    subwindow_subset.sq_end = None  # End point of square
    subwindow_subset.pan_start = None
    subwindow_subset.pan_offset = [0, 0]
    subwindow_subset.is_drawing = False  # Track if currently drawing square
    subwindow_subset.dragging_corner = None  # Track which corner is being dragged: 'tl', 'tr', 'bl', 'br'
    subwindow_subset.dragging_box = False  # Track if dragging entire bounding box
    subwindow_subset.drag_box_start = None  # Starting position for box drag
    subwindow_subset.canvas_height_prev = None  # Track canvas height for coordinate rescaling on window resize
    
    # Edit: Show header if editable
    # Header frame (title and toolbox)
    header_frame = Frame(subwindow_subset, bg="#FBE3D6", height=50)
    header_frame.pack(side="top", fill="x", padx=10, pady=5)

    # Header text
    header_label = Label(
        header_frame,
        text="Draw a square to define the cropping area",
        font=("Roboto", 14),
        bg="#FBE3D6",
        fg=theme_blue,
    )
    header_label.pack(side="top", padx=5)

    # Canvas frame (must be created before set_active_tool function)
    subcanvas_subset = Canvas(
        subwindow_subset,
        bg="#FBE3D6",
        bd=0,
        highlightthickness=0,
        relief="ridge", # elevated style
        cursor="crosshair",
    )
    subcanvas_subset.pack(fill="both", expand=True, padx=50, pady=(5, 10))
    
    # Confirm button
    button_confirm = ctk.CTkButton(
        subwindow_subset,
        text="Done",
        command=lambda: confirm_square(),
        width=120,
        height=40,
        font=("Roboto", 12 * -1),
        text_color=text_colour,
        fg_color=button_blue_colour,
        hover_color=button_blue_hover,
        corner_radius=6,
        border_width=1,
        border_color=button_border_colour,
    )
    button_confirm.pack(side="bottom", pady=10)

    # Edit: Show tool frame if editable
    def set_active_tool(tool_name):
        print("Tool set to :", tool_name)
        subwindow_subset.active_tool = tool_name

        # Update button colors
        for name, btn in subwindow_subset.tool_buttons.items():
            if name == tool_name:
                print("Setting active tool button to yellow highlight color:", name)
                btn.configure(fg_color=button_yellow_hover)
            else:
                btn.configure(fg_color=button_blue_colour)

        # Update cursor
        #! See https://www.tcl-lang.org/man/tcl8.6/TkCmd/cursors.htm (stdlib\tkinter\__init__.pyi), some won't work cross platform
        if tool_name == "draw":
            subcanvas_subset.config(cursor="crosshair")
        elif tool_name == "pan":
            subcanvas_subset.config(cursor="fleur")
        elif tool_name == "zoom":
            subcanvas_subset.config(cursor="double_arrow")
        else:
            subcanvas_subset.config(cursor="crosshair")

    def pack_tool_button(button, text):
        button.pack(side="left", padx=2)
        subwindow_subset.tool_buttons[text] = button

    # Draw tool button
    btn_config = {
        "width": 35,
        "height": 35,
        "font": ("Roboto", 18),
        "text_color": text_colour,
        "fg_color": button_blue_colour,
        "hover_color": button_yellow_hover,
        "corner_radius": 4,
        "border_width": 1,
        "border_color": button_border_colour,
    }

    # Tool buttons frame
    tools_frame = Frame(header_frame, bg="#FBE3D6")
    tools_frame.pack(side="right", padx=10)

    # Store button references
    subwindow_subset.tool_buttons = {}

    # Load tool icons
    icon_draw_pil = Image.open(ICONS_PATH / "draw.png")
    icon_pan_pil = Image.open(ICONS_PATH / "pan.png")
    icon_zoom_pil = Image.open(ICONS_PATH / "zoom.png")
    
    # Convert to CTkImage for proper rendering
    icon_draw = ctk.CTkImage(light_image=icon_draw_pil, dark_image=icon_draw_pil, size=(24, 24))
    icon_pan = ctk.CTkImage(light_image=icon_pan_pil, dark_image=icon_pan_pil, size=(24, 24))
    icon_zoom = ctk.CTkImage(light_image=icon_zoom_pil, dark_image=icon_zoom_pil, size=(24, 24))

    # Draw tool button
    btn_draw = ctk.CTkButton(
        tools_frame, image=icon_draw, text="", command=lambda: set_active_tool("draw"), **btn_config
    )
    pack_tool_button(btn_draw, "draw")

    # Pan tool button
    btn_pan = ctk.CTkButton(
        tools_frame, image=icon_pan, text="", command=lambda: set_active_tool("pan"), **btn_config
    )
    pack_tool_button(btn_pan, "pan")

    # Zoom tool button
    btn_zoom = ctk.CTkButton(
        tools_frame, image=icon_zoom, text="", command=lambda: set_active_tool("zoom"), **btn_config
    )
    pack_tool_button(btn_zoom, "zoom")

    # Editor initialization, set draw tool as active by default
    set_active_tool("draw")

    # Edit: Update image display after 1. pan 2. zoom 3. draw square
    def update_image_display():
        # Get current canvas size
        canvas_width = subcanvas_subset.winfo_width()
        canvas_height = subcanvas_subset.winfo_height()

        if canvas_width == 0 or canvas_height == 0:
            # Canvas not yet rendered
            return
        else:
            # Clear canvas before redrawing
            subcanvas_subset.delete("all")

        # Fit to canvas
        display_height = int(canvas_height * subwindow_subset.zoom_level)
        display_width = int(display_height)

        print("Updating image display with zoom level:", subwindow_subset.zoom_level, "and pan offset:", subwindow_subset.pan_offset, "and canvas_height/display_height:", canvas_height, display_height, "and img position: ", getattr(subwindow_subset, "img_position", None))

        # Handle if window resize: relative positions to be maintained, others like display will be refitted without need to scale
        if subwindow_subset.canvas_height_prev is not None and subwindow_subset.canvas_height_prev != canvas_height:
            scale_ratio = canvas_height / subwindow_subset.canvas_height_prev
            print(f"Canvas height changed from {subwindow_subset.canvas_height_prev} to {canvas_height}, rescaling square points by {scale_ratio}")
            if subwindow_subset.sq_start and subwindow_subset.sq_end:
                subwindow_subset.sq_start = (
                    subwindow_subset.sq_start[0] * scale_ratio,
                    subwindow_subset.sq_start[1] * scale_ratio
                )
                subwindow_subset.sq_end = (
                    subwindow_subset.sq_end[0] * scale_ratio,
                    subwindow_subset.sq_end[1] * scale_ratio
                )
            subwindow_subset.pan_offset[0] *= scale_ratio
            subwindow_subset.pan_offset[1] *= scale_ratio
        
        # Update previous canvas height
        subwindow_subset.canvas_height_prev = canvas_height

        # Create image copy for drawing
        img_to_display = subwindow_subset.original_pil.copy()

        # Zoom: Resize image
        resized_img = img_to_display.resize(
            (display_width, display_height), Image.LANCZOS
        )
        img_tk = ImageTk.PhotoImage(resized_img)

        # Pan: Add x/y offset
        img_x = canvas_width // 2 + subwindow_subset.pan_offset[0]
        img_y = canvas_height // 2 + subwindow_subset.pan_offset[1]
        subcanvas_subset.create_image(
            img_x, img_y, image=img_tk, anchor="center", tags="image"
        )

        # Draw: update relative position for point mapping
        subwindow_subset.img_display_size = (display_width, display_height)
        subwindow_subset.img_position = (
            img_x - display_width // 2,
            img_y - display_height // 2,
        )
  
        # square: Draw the cropping square if both start and end points exist
        if subwindow_subset.sq_start and subwindow_subset.sq_end:
            
            # Convert display coordinates to canvas coordinates
            x1 = subwindow_subset.img_position[0] + subwindow_subset.sq_start[0] * subwindow_subset.zoom_level
            y1 = subwindow_subset.img_position[1] + subwindow_subset.sq_start[1] * subwindow_subset.zoom_level
            x2 = subwindow_subset.img_position[0] + subwindow_subset.sq_end[0] * subwindow_subset.zoom_level
            y2 = subwindow_subset.img_position[1] + subwindow_subset.sq_end[1] * subwindow_subset.zoom_level
            
            # Draw semi-transparent square
            #! Stipple won't work on MacOS, and there is no alpha channel for the fill property
            # https://stackoverflow.com/questions/35994986/tkinter-stipple-option-misbehaving-in-os-x
            # 02232026: Remove fill/stipple and leave the square completely transparent
            subcanvas_subset.create_rectangle(
                x1, y1, x2, y2, 
                outline=point_blue_colour,
                # fill=button_blue_colour,
                # stipple="gray25",
                width=2, 
                tags="square"
            )
            
            # Draw corner handles
            handle_size = 6
            for corner_x, corner_y in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                subcanvas_subset.create_rectangle(
                    corner_x - handle_size, corner_y - handle_size,
                    corner_x + handle_size, corner_y + handle_size,
                    fill=point_blue_colour, 
                    outline="black",
                    tags="handle"
                )

        # Keep reference to prevent garbage collection
        subcanvas_subset.image_ref = img_tk

    # Helper function to check if mouse is near a corner within a threshold distance (in pixels)
    def get_corner_at_position(canvas_x, canvas_y, threshold=10):
        """Returns corner identifier if near a corner, None otherwise"""
        if not (subwindow_subset.sq_start and subwindow_subset.sq_end):
            return None
        
        # Convert display coordinates to canvas coordinates
        x1 = subwindow_subset.img_position[0] + subwindow_subset.sq_start[0] * subwindow_subset.zoom_level
        y1 = subwindow_subset.img_position[1] + subwindow_subset.sq_start[1] * subwindow_subset.zoom_level
        x2 = subwindow_subset.img_position[0] + subwindow_subset.sq_end[0] * subwindow_subset.zoom_level
        y2 = subwindow_subset.img_position[1] + subwindow_subset.sq_end[1] * subwindow_subset.zoom_level
        
        # Check each corner
        corners = {
            'tl': (x1, y1),  # top-left
            'tr': (x2, y1),  # top-right
            'bl': (x1, y2),  # bottom-left
            'br': (x2, y2),  # bottom-right
        }
        
        for corner_id, (cx, cy) in corners.items():
            distance = ((canvas_x - cx) ** 2 + (canvas_y - cy) ** 2) ** 0.5
            if distance <= threshold:
                return corner_id
        return None

    # Helper function to check if mouse is inside the square
    def is_inside_square(canvas_x, canvas_y):
        """Returns True if point is inside the square"""
        if not (subwindow_subset.sq_start and subwindow_subset.sq_end):
            return False
        
        # Convert display coordinates to canvas coordinates
        x1 = subwindow_subset.img_position[0] + subwindow_subset.sq_start[0] * subwindow_subset.zoom_level
        y1 = subwindow_subset.img_position[1] + subwindow_subset.sq_start[1] * subwindow_subset.zoom_level
        x2 = subwindow_subset.img_position[0] + subwindow_subset.sq_end[0] * subwindow_subset.zoom_level
        y2 = subwindow_subset.img_position[1] + subwindow_subset.sq_end[1] * subwindow_subset.zoom_level
        
        # Ensure min/max order
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return min_x <= canvas_x <= max_x and min_y <= canvas_y <= max_y

    # Event handlers
    # Handle active tool selected/mouse positions for cursor changes
    # @listener mouse motion
    def on_mouse_motion(event):
        """Update cursor when hovering over corners"""
        if subwindow_subset.active_tool == "draw" and not subwindow_subset.is_drawing:
            corner = get_corner_at_position(event.x, event.y)
            if corner:
                subcanvas_subset.config(cursor="hand2")
            elif is_inside_square(event.x, event.y):
                subcanvas_subset.config(cursor="fleur")  # Move cursor for dragging box
            else:
                subcanvas_subset.config(cursor="crosshair")
        elif subwindow_subset.active_tool == "pan":
            subcanvas_subset.config(cursor="fleur")
        elif subwindow_subset.active_tool == "zoom":
            subcanvas_subset.config(cursor="double_arrow")

    # Handle mouse click on canvas
    # @listener left mouse click
    def on_canvas_click(event):
        print("Canvas clicked at:", event.x, event.y)
        
        if subwindow_subset.active_tool == "pan":
            print("[on_canvas_click] Pan registered")
            # Register the starting pan position
            subwindow_subset.pan_start = (event.x, event.y)
            
        elif subwindow_subset.active_tool == "draw":
            # Check if clicking on a corner for resizing
            corner = get_corner_at_position(event.x, event.y)
            if corner:
                print(f"[on_canvas_click] Starting corner drag: {corner}")
                subwindow_subset.dragging_corner = corner
                return
            
            # Check if clicking inside square for moving
            if is_inside_square(event.x, event.y):
                print("[on_canvas_click] Starting box drag")
                subwindow_subset.dragging_box = True
                subwindow_subset.drag_box_start = (event.x, event.y)
                return
            
            print("[on_canvas_click] Starting square draw")
            subwindow_subset.pan_start = None  # Clear pan state
            
            # If none, then create a new square
            if hasattr(subwindow_subset, "img_position") and hasattr(
                subwindow_subset, "img_display_size"
            ):
                # Convert event (rel. canvas) coordinates to image (rel. display) coordinates
                rect_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                rect_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level

                # Check if click is within image bounds
                if (
                    0 <= rect_x <= subwindow_subset.img_display_size[0]
                    and 0 <= rect_y <= subwindow_subset.img_display_size[1]
                ):
                    # Start new square
                    subwindow_subset.sq_start = (rect_x, rect_y)
                    subwindow_subset.sq_end = (rect_x, rect_y)
                    subwindow_subset.is_drawing = True
                    update_image_display()

    # Handle mouse wheel for zooming when zoom tool is active
    # @listener mouse wheel
    def on_mouse_wheel(event):
        print("Mouse wheel event:", event.delta)
        if subwindow_subset.active_tool == "zoom":
            # Determine zoom direction
            if event.delta > 0:
                # Zoom in
                subwindow_subset.zoom_level *= 1.1
            else:
                # Zoom out
                subwindow_subset.zoom_level /= 1.1

            # Clamp zoom level from 0.5x to 5x (when zooming out too much, points cant be assigned)
            subwindow_subset.zoom_level = max(0.5, min(subwindow_subset.zoom_level, 5))
            update_image_display()

    # Handle drag motion and end
    # @listener mouse drag events
    def on_drag_motion(event):
        if subwindow_subset.active_tool == "pan" and subwindow_subset.pan_start:
            # Handle pan motion
            print("Pan motion at:", event.x, event.y)
            dx = event.x - subwindow_subset.pan_start[0]
            dy = event.y - subwindow_subset.pan_start[1]
            subwindow_subset.pan_offset[0] += dx
            subwindow_subset.pan_offset[1] += dy
            subwindow_subset.pan_start = (event.x, event.y)
            update_image_display()
        
        elif subwindow_subset.active_tool == "draw" and subwindow_subset.dragging_box:
            # Handle dragging entire bounding box
            if hasattr(subwindow_subset, "img_position"):
                # Convert event (rel. canvas) positions to image (rel. display) coordinates
                cursor_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                cursor_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                start_cursor_x = (subwindow_subset.drag_box_start[0] - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                start_cursor_y = (subwindow_subset.drag_box_start[1] - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                dx = cursor_x - start_cursor_x
                dy = cursor_y - start_cursor_y
                
                # Update both corners to move the box
                start_x = subwindow_subset.sq_start[0] + dx
                start_y = subwindow_subset.sq_start[1] + dy
                end_x = subwindow_subset.sq_end[0] + dx
                end_y = subwindow_subset.sq_end[1] + dy
                length = abs(end_x - start_x)
                
                # Clamp x coordinates
                if start_x < 0:
                    start_x = 0
                    end_x = length
                elif end_x > subwindow_subset.img_display_size[0] / subwindow_subset.zoom_level:
                    end_x = subwindow_subset.img_display_size[0] / subwindow_subset.zoom_level
                    start_x = end_x - length
                    
                # Clamp y coordinates
                if start_y < 0:
                    start_y = 0
                    end_y = length
                elif end_y > subwindow_subset.img_display_size[1] / subwindow_subset.zoom_level:
                    end_y = subwindow_subset.img_display_size[1] / subwindow_subset.zoom_level
                    start_y = end_y - length
                
                subwindow_subset.sq_start = (start_x, start_y)
                subwindow_subset.sq_end = (end_x, end_y)

                subwindow_subset.drag_box_start = (event.x, event.y)  # Update start position for next frame
                update_image_display()
            
        elif subwindow_subset.active_tool == "draw" and subwindow_subset.dragging_corner:
            # Handle corner dragging
            if hasattr(subwindow_subset, "img_position"):
                cursor_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                cursor_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                # Clamp to image bounds
                cursor_x = max(0, min(cursor_x, subwindow_subset.img_display_size[0] / subwindow_subset.zoom_level))
                cursor_y = max(0, min(cursor_y, subwindow_subset.img_display_size[1] / subwindow_subset.zoom_level))
                
                start_x, start_y, end_x, end_y = 0, 0, 0, 0
                if subwindow_subset.dragging_corner in ['tl']:
                    start_x, start_y = cursor_x, cursor_y
                    end_x, end_y = subwindow_subset.sq_end
                elif subwindow_subset.dragging_corner in ['tr']:
                    start_x, start_y = subwindow_subset.sq_start[0], cursor_y
                    end_x, end_y = cursor_x, subwindow_subset.sq_end[1]
                elif subwindow_subset.dragging_corner in ['bl']:
                    start_x, start_y = cursor_x, subwindow_subset.sq_start[1]
                    end_x, end_y = subwindow_subset.sq_end[0], cursor_y
                elif subwindow_subset.dragging_corner in ['br']:
                    start_x, start_y = subwindow_subset.sq_start
                    end_x, end_y = cursor_x, cursor_y

                # Fixate aspect ratio of square to 1:1 (square)
                length  = min(end_x - start_x, end_y - start_y)

                # Update the appropriate corner
                if subwindow_subset.dragging_corner == 'tl':  # top-left
                    subwindow_subset.sq_start = (end_x - length, end_y - length)
                elif subwindow_subset.dragging_corner == 'tr':  # top-right
                    subwindow_subset.sq_start = (subwindow_subset.sq_start[0], end_y - length)
                    subwindow_subset.sq_end = (start_x + length, subwindow_subset.sq_end[1])
                elif subwindow_subset.dragging_corner == 'bl':  # bottom-left
                    subwindow_subset.sq_start = (end_x - length, subwindow_subset.sq_start[1])
                    subwindow_subset.sq_end = (subwindow_subset.sq_end[0], start_y + length)
                elif subwindow_subset.dragging_corner == 'br':  # bottom-right
                    subwindow_subset.sq_end = (start_x + length, start_y + length)
                
                update_image_display()
            
        elif subwindow_subset.active_tool == "draw" and subwindow_subset.is_drawing:
            # Handle square drawing
            if hasattr(subwindow_subset, "img_position"):
                cursor_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                cursor_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                # Clamp to image bounds
                cursor_x = max(0, min(cursor_x, subwindow_subset.img_display_size[0] / subwindow_subset.zoom_level))
                cursor_y = max(0, min(cursor_y, subwindow_subset.img_display_size[1] / subwindow_subset.zoom_level))
                
                dx = cursor_x - subwindow_subset.sq_start[0]
                dy = cursor_y - subwindow_subset.sq_start[1]
                
                # Fixate aspect ratio of square to 1:1 (square)
                length = min(abs(dx), abs(dy))

                end_x = subwindow_subset.sq_start[0] + (length if dx >= 0 else -length)
                end_y = subwindow_subset.sq_start[1] + (length if dy >= 0 else -length)

                subwindow_subset.sq_end = (end_x, end_y)
                update_image_display()

    # Handle both pan and drag end
    # @listener mouse button release events
    def on_drag_end(event):
        if subwindow_subset.active_tool == "pan":
            subwindow_subset.pan_start = None
        elif subwindow_subset.active_tool == "draw":
            if subwindow_subset.dragging_corner:
                # Finished dragging corner
                subwindow_subset.dragging_corner = None
                # Update cursor
                corner = get_corner_at_position(event.x, event.y)
                if corner:
                    subcanvas_subset.config(cursor="hand2")
                elif is_inside_square(event.x, event.y):
                    subcanvas_subset.config(cursor="fleur")
                else:
                    subcanvas_subset.config(cursor="crosshair")
            elif subwindow_subset.dragging_box:
                # Finished dragging box
                subwindow_subset.dragging_box = False
                subwindow_subset.drag_box_start = None
                # Update cursor
                if is_inside_square(event.x, event.y):
                    subcanvas_subset.config(cursor="fleur")
                else:
                    subcanvas_subset.config(cursor="crosshair")
            elif subwindow_subset.is_drawing:
                # Finished drawing new square
                subwindow_subset.is_drawing = False

    # Handle canvas resize event
    # @listener canvas resize events
    def on_canvas_resize(event):
        if event.widget == subcanvas_subset:
            new_width = event.width
            new_height = event.height
            print(f"Canvas resized to: {new_width}x{new_height}")
            # update display
            update_image_display()

    def confirm_square():
        if not (subwindow_subset.sq_start and subwindow_subset.sq_end):
            messagebox.showwarning("No Area Selected", "Please select a valid area to crop.")
            return
        
        result = messagebox.askyesno(
            title="Crop Confirmation",
            message="Apply this cropping area?",
            parent=subwindow_subset
        )
        if result is True:  # Yes - Save
            # Scale to original image size
            orig_height, orig_width = canvas.original_img.shape
            print("Original image size:", orig_width, orig_height, "and display size:", subwindow_subset.img_display_size)
            scale_x = orig_width / subwindow_subset.img_display_size[0] * subwindow_subset.zoom_level
            scale_y = orig_height / subwindow_subset.img_display_size[1] * subwindow_subset.zoom_level

            # Get square coordinates
            x1, y1 = subwindow_subset.sq_start
            x2, y2 = subwindow_subset.sq_end
            
            # Ensure top-left and bottom-right order
            x_min = int(min(x1, x2))
            y_min = int(min(y1, y2))
            x_max = int(max(x1, x2))
            y_max = int(max(y1, y2))
            
            x_min_orig = int(x_min * scale_x)
            y_min_orig = int(y_min * scale_y)
            x_max_orig = int(x_max * scale_x)
            y_max_orig = int(y_max * scale_y)
            
            # Store cropped image
            # Numpy is row/column = y/x
            cropped_img = canvas.original_img[y_min_orig:y_max_orig, x_min_orig:x_max_orig]
            
            # Load into main canvas
            load_image(canvas, 550, 255, 180, 170, imgArr=cropped_img)

            # messagebox.showinfo("Saved", f"Image subset cropped!\nCoordinates: ({x_min_orig}, {y_min_orig}) to ({x_max_orig}, {y_max_orig})")
            print(f"Image cropped from display coordinates: ({x_min}, {y_min}) to ({x_max}, {y_max}), original coordinates: ({x_min_orig}, {y_min_orig}) to ({x_max_orig}, {y_max_orig})")
            
        subwindow_subset.destroy()
        
    # Key Binding events
    subcanvas_subset.bind("<Motion>", on_mouse_motion)
    subcanvas_subset.bind("<ButtonPress-1>", on_canvas_click)
    subcanvas_subset.bind("<B1-Motion>", on_drag_motion)
    subcanvas_subset.bind("<ButtonRelease-1>", on_drag_end)
    subcanvas_subset.bind("<MouseWheel>", on_mouse_wheel)
    subcanvas_subset.bind("<Configure>", on_canvas_resize)

    # Close window event
    def on_close():
        confirm_square()

    # Initial display after window is rendered (100ms)
    subwindow_subset.after(100, update_image_display)

    subwindow_subset.protocol("WM_DELETE_WINDOW", on_close)
    subwindow_subset.resizable(True, True)
    subwindow_subset.mainloop()
