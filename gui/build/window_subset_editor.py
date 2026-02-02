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
    subwindow_subset.rect_start = None  # Start point of rectangle
    subwindow_subset.rect_end = None  # End point of rectangle
    subwindow_subset.pan_start = None
    subwindow_subset.pan_offset = [0, 0]
    subwindow_subset.is_drawing = False  # Track if currently drawing rectangle
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
        text="Draw a rectangle to define the cropping area",
        font=("Roboto", 14),
        bg="#FBE3D6",
        fg=theme_blue,
    )
    header_label.pack(side="top", padx=5)

    # Canvas frame (must be created before set_active_tool function)
    subcanvas4 = Canvas(
        subwindow_subset,
        bg="#FBE3D6",
        bd=0,
        highlightthickness=0,
        relief="ridge", # elevated style
        cursor="crosshair",
    )
    subcanvas4.pack(fill="both", expand=True, padx=50, pady=(5, 10))
    
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
        #! See https://www.tcl-lang.org/man/tcl8.6/TkCmd/cursors.htm (stdlib\tkinter\__init__.pyi), some wont work cross platform
        if tool_name == "draw":
            subcanvas4.config(cursor="crosshair")
        elif tool_name == "pan":
            subcanvas4.config(cursor="fleur")
        elif tool_name == "zoom":
            subcanvas4.config(cursor="double_arrow")
        else:
            subcanvas4.config(cursor="crosshair")

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

    # Draw tool button
    btn_draw = ctk.CTkButton(
        tools_frame, text="✎", command=lambda: set_active_tool("draw"), **btn_config
    )
    pack_tool_button(btn_draw, "draw")

    # Pan tool button
    btn_pan = ctk.CTkButton(
        tools_frame, text="✋", command=lambda: set_active_tool("pan"), **btn_config
    )
    pack_tool_button(btn_pan, "pan")

    # Zoom tool button
    btn_zoom = ctk.CTkButton(
        tools_frame, text="🔍", command=lambda: set_active_tool("zoom"), **btn_config
    )
    pack_tool_button(btn_zoom, "zoom")

    # Editor initialization, set draw tool as active by default
    set_active_tool("draw")

    # Edit: Update image display after 1. pan 2. zoom 3. draw rectangle
    def update_image_display():
        # Get current canvas size
        canvas_width = subcanvas4.winfo_width()
        canvas_height = subcanvas4.winfo_height()

        if canvas_width == 0 or canvas_height == 0:
            # Canvas not yet rendered
            return
        else:
            # Clear canvas before redrawing
            subcanvas4.delete("all")

        # Fit to canvas
        display_height = int(canvas_height * subwindow_subset.zoom_level)
        display_width = int(display_height)

        print("Updating image display with zoom level:", subwindow_subset.zoom_level, "and pan offset:", subwindow_subset.pan_offset, "and canvas_height/display_height:", canvas_height, display_height)

        # Rescale rectangle points only if canvas_height changed (canvas resize)
        if subwindow_subset.canvas_height_prev is not None and subwindow_subset.canvas_height_prev != canvas_height:
            scale_ratio = canvas_height / subwindow_subset.canvas_height_prev
            print(f"Canvas height changed from {subwindow_subset.canvas_height_prev} to {canvas_height}, rescaling rectangle points by {scale_ratio}")
            subwindow_subset.rect_start = (
                subwindow_subset.rect_start[0] * scale_ratio,
                subwindow_subset.rect_start[1] * scale_ratio
            )
            subwindow_subset.rect_end = (
                subwindow_subset.rect_end[0] * scale_ratio,
                subwindow_subset.rect_end[1] * scale_ratio
            )
        
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
        img_x = canvas_width // 2 + subwindow_subset.pan_offset[0] * subwindow_subset.zoom_level
        img_y = canvas_height // 2 + subwindow_subset.pan_offset[1] * subwindow_subset.zoom_level
        subcanvas4.create_image(
            img_x, img_y, image=img_tk, anchor="center", tags="image"
        )

        # Draw: update relative position for point mapping
        subwindow_subset.img_display_size = (display_width, display_height)
        subwindow_subset.img_position = (
            img_x - display_width // 2,
            img_y - display_height // 2,
        )
  
        # Rectangle: Draw the cropping rectangle if both start and end points exist
        if subwindow_subset.rect_start and subwindow_subset.rect_end:
            print("Drawing rectangle from:", subwindow_subset.rect_start, "to:", subwindow_subset.rect_end)
            
            # Convert image coordinates to canvas coordinates
            x1 = subwindow_subset.img_position[0] + subwindow_subset.rect_start[0] * subwindow_subset.zoom_level
            y1 = subwindow_subset.img_position[1] + subwindow_subset.rect_start[1] * subwindow_subset.zoom_level
            x2 = subwindow_subset.img_position[0] + subwindow_subset.rect_end[0] * subwindow_subset.zoom_level
            y2 = subwindow_subset.img_position[1] + subwindow_subset.rect_end[1] * subwindow_subset.zoom_level
            
            # Draw semi-transparent rectangle
            subcanvas4.create_rectangle(
                x1, y1, x2, y2, 
                outline=point_blue_colour,
                fill=button_blue_colour,
                stipple="gray25",  # Semi-transparent background
                width=2, 
                tags="rectangle"
            )
            
            # Draw corner handles
            handle_size = 6
            for corner_x, corner_y in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                subcanvas4.create_rectangle(
                    corner_x - handle_size, corner_y - handle_size,
                    corner_x + handle_size, corner_y + handle_size,
                    fill=point_blue_colour, 
                    outline="black",
                    tags="handle"
                )

        # Keep reference to prevent garbage collection
        subcanvas4.image_ref = img_tk

    # Helper function to check if mouse is near a corner
    def get_corner_at_position(canvas_x, canvas_y, threshold=10):
        """Returns corner identifier if near a corner, None otherwise"""
        if not (subwindow_subset.rect_start and subwindow_subset.rect_end):
            return None
        
        # Convert rect coordinates to canvas coordinates
        x1 = subwindow_subset.img_position[0] + subwindow_subset.rect_start[0] * subwindow_subset.zoom_level
        y1 = subwindow_subset.img_position[1] + subwindow_subset.rect_start[1] * subwindow_subset.zoom_level
        x2 = subwindow_subset.img_position[0] + subwindow_subset.rect_end[0] * subwindow_subset.zoom_level
        y2 = subwindow_subset.img_position[1] + subwindow_subset.rect_end[1] * subwindow_subset.zoom_level
        
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

    # Helper function to check if mouse is inside the rectangle
    def is_inside_rectangle(canvas_x, canvas_y):
        """Returns True if point is inside the rectangle"""
        if not (subwindow_subset.rect_start and subwindow_subset.rect_end):
            return False
        
        # Convert rect coordinates to canvas coordinates
        x1 = subwindow_subset.img_position[0] + subwindow_subset.rect_start[0] * subwindow_subset.zoom_level
        y1 = subwindow_subset.img_position[1] + subwindow_subset.rect_start[1] * subwindow_subset.zoom_level
        x2 = subwindow_subset.img_position[0] + subwindow_subset.rect_end[0] * subwindow_subset.zoom_level
        y2 = subwindow_subset.img_position[1] + subwindow_subset.rect_end[1] * subwindow_subset.zoom_level
        
        # Ensure min/max order
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return min_x <= canvas_x <= max_x and min_y <= canvas_y <= max_y

    # Event handlers - unified approach to prevent tool switching conflicts
    # Handle mouse motion for cursor changes
    # @listener mouse motion
    def on_mouse_motion(event):
        """Update cursor when hovering over corners"""
        if subwindow_subset.active_tool == "draw" and not subwindow_subset.is_drawing:
            corner = get_corner_at_position(event.x, event.y)
            if corner:
                subcanvas4.config(cursor="hand2")
            elif is_inside_rectangle(event.x, event.y):
                subcanvas4.config(cursor="fleur")  # Move cursor for dragging box
            else:
                subcanvas4.config(cursor="crosshair")
        elif subwindow_subset.active_tool == "pan":
            subcanvas4.config(cursor="fleur")
        elif subwindow_subset.active_tool == "zoom":
            subcanvas4.config(cursor="double_arrow")

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
            
            # Check if clicking inside rectangle for moving
            if is_inside_rectangle(event.x, event.y):
                print("[on_canvas_click] Starting box drag")
                subwindow_subset.dragging_box = True
                subwindow_subset.drag_box_start = (event.x, event.y)
                return
            
            print("[on_canvas_click] Starting rectangle draw")
            subwindow_subset.pan_start = None  # Clear pan state
            
            # Start drawing rectangle
            if hasattr(subwindow_subset, "img_position") and hasattr(
                subwindow_subset, "img_display_size"
            ):
                # Convert canvas coordinates to image coordinates
                img_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                img_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level

                # Check if click is within image bounds
                if (
                    0 <= img_x <= subwindow_subset.img_display_size[0]
                    and 0 <= img_y <= subwindow_subset.img_display_size[1]
                ):
                    # Start new rectangle
                    subwindow_subset.rect_start = (img_x, img_y)
                    subwindow_subset.rect_end = (img_x, img_y)
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
                # Convert both current and start positions to image coordinates
                current_img_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                current_img_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                start_img_x = (subwindow_subset.drag_box_start[0] - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                start_img_y = (subwindow_subset.drag_box_start[1] - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                # Calculate delta in image space
                dx = current_img_x - start_img_x
                dy = current_img_y - start_img_y
                
                # Update both corners to move the box
                new_x1 = subwindow_subset.rect_start[0] + dx
                new_y1 = subwindow_subset.rect_start[1] + dy
                new_x2 = subwindow_subset.rect_end[0] + dx
                new_y2 = subwindow_subset.rect_end[1] + dy
                
                # Clamp to image bounds
                width = abs(new_x2 - new_x1)
                height = abs(new_y2 - new_y1)
                
                # Clamp x coordinates
                if new_x1 < 0:
                    new_x1 = 0
                    new_x2 = width
                elif new_x2 > subwindow_subset.img_display_size[0]:
                    new_x2 = subwindow_subset.img_display_size[0]
                    new_x1 = new_x2 - width
                    
                # Clamp y coordinates
                if new_y1 < 0:
                    new_y1 = 0
                    new_y2 = height
                elif new_y2 > subwindow_subset.img_display_size[1]:
                    new_y2 = subwindow_subset.img_display_size[1]
                    new_y1 = new_y2 - height
                
                subwindow_subset.rect_start = (new_x1, new_y1)
                subwindow_subset.rect_end = (new_x2, new_y2)
                subwindow_subset.drag_box_start = (event.x, event.y)  # Update start position for next frame
                update_image_display()
            
        elif subwindow_subset.active_tool == "draw" and subwindow_subset.dragging_corner:
            # Handle corner dragging
            if hasattr(subwindow_subset, "img_position"):
                img_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                img_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                # Clamp to image bounds
                img_x = max(0, min(img_x, subwindow_subset.img_display_size[0]))
                img_y = max(0, min(img_y, subwindow_subset.img_display_size[1]))
                
                x1, y1 = subwindow_subset.rect_start
                x2, y2 = subwindow_subset.rect_end
                
                # Update the appropriate corner
                if subwindow_subset.dragging_corner == 'tl':  # top-left
                    subwindow_subset.rect_start = (img_x, img_y)
                elif subwindow_subset.dragging_corner == 'tr':  # top-right
                    subwindow_subset.rect_end = (img_x, subwindow_subset.rect_end[1])
                    subwindow_subset.rect_start = (subwindow_subset.rect_start[0], img_y)
                elif subwindow_subset.dragging_corner == 'bl':  # bottom-left
                    subwindow_subset.rect_start = (img_x, subwindow_subset.rect_start[1])
                    subwindow_subset.rect_end = (subwindow_subset.rect_end[0], img_y)
                elif subwindow_subset.dragging_corner == 'br':  # bottom-right
                    subwindow_subset.rect_end = (img_x, img_y)
                
                update_image_display()
            
        elif subwindow_subset.active_tool == "draw" and subwindow_subset.is_drawing:
            # Handle rectangle drawing
            if hasattr(subwindow_subset, "img_position"):
                img_x = (event.x - subwindow_subset.img_position[0]) / subwindow_subset.zoom_level
                img_y = (event.y - subwindow_subset.img_position[1]) / subwindow_subset.zoom_level
                
                # Clamp to image bounds
                img_x = max(0, min(img_x, subwindow_subset.img_display_size[0]))
                img_y = max(0, min(img_y, subwindow_subset.img_display_size[1]))
                
                subwindow_subset.rect_end = (img_x, img_y)
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
                    subcanvas4.config(cursor="hand2")
                elif is_inside_rectangle(event.x, event.y):
                    subcanvas4.config(cursor="fleur")
                else:
                    subcanvas4.config(cursor="crosshair")
            elif subwindow_subset.dragging_box:
                # Finished dragging box
                subwindow_subset.dragging_box = False
                subwindow_subset.drag_box_start = None
                # Update cursor
                if is_inside_rectangle(event.x, event.y):
                    subcanvas4.config(cursor="fleur")
                else:
                    subcanvas4.config(cursor="crosshair")
            elif subwindow_subset.is_drawing:
                # Finished drawing new rectangle
                subwindow_subset.is_drawing = False

    # Handle canvas resize event
    # @listener canvas resize events
    def on_canvas_resize(event):
        if event.widget == subcanvas4:
            new_width = event.width
            new_height = event.height
            print(f"Canvas resized to: {new_width}x{new_height}")
            # update display
            update_image_display()

    def confirm_rectangle():
        result = messagebox.askyesno(
            title="Crop Confirmation",
            message="Apply this cropping area?",
            parent=subwindow_subset
        )
        if result is True:  # Yes - Save

            # Scale to original image size
            orig_height, orig_width = canvas.original_img.shape
            scale_ratio = orig_height / subwindow_subset.img_display_size[1] / subwindow_subset.zoom_level

            # Get rectangle coordinates
            x1, y1 = subwindow_subset.rect_start
            x2, y2 = subwindow_subset.rect_end
            
            # Ensure top-left and bottom-right order
            x_min = int(min(x1, x2))
            y_min = int(min(y1, y2))
            x_max = int(max(x1, x2))
            y_max = int(max(y1, y2))
            
            x_min_orig = int(x_min * scale_ratio)
            y_min_orig = int(y_min * scale_ratio)
            x_max_orig = int(x_max * scale_ratio)
            y_max_orig = int(y_max * scale_ratio)
            
            # Store cropped image
            cropped_img = canvas.original_img[y_min_orig:y_max_orig, x_min_orig:x_max_orig]
            
            # Load into main canvas
            load_image(canvas, 550, 255, 180, 170, imgArr=cropped_img)

            messagebox.showinfo("Saved", f"Image subset cropped!\nCoordinates: ({x_min_orig}, {y_min_orig}) to ({x_max_orig}, {y_max_orig})")
            print(f"Image cropped to: {cropped_img.shape}, at coords: ({x_min_orig}, {y_min_orig}) to ({x_max_orig}, {y_max_orig})")
            
        subwindow_subset.destroy()
        
    # Key Binding events - unified event handlers
    subcanvas4.bind("<Motion>", on_mouse_motion)
    subcanvas4.bind("<ButtonPress-1>", on_canvas_click)
    subcanvas4.bind("<B1-Motion>", on_drag_motion)
    subcanvas4.bind("<ButtonRelease-1>", on_drag_end)
    subcanvas4.bind("<MouseWheel>", on_mouse_wheel)
    subcanvas4.bind("<Configure>", on_canvas_resize)

    # Close window event
    def on_close():
        confirm_rectangle()

    # Initial display after window is rendered (100ms)
    subwindow_subset.after(100, update_image_display)

    subwindow_subset.protocol("WM_DELETE_WINDOW", on_close)
    subwindow_subset.resizable(True, True)
    subwindow_subset.mainloop()
