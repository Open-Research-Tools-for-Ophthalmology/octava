import os
import cv2
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
from resource_path import ICONS_PATH

def window_onh_editor(canvas):
    # Check if an image is loaded
    if not hasattr(canvas, "original_img"):
        messagebox.showwarning(
            "No Image Loaded", "Please load an image before processing."
        )
        return

    # Check if the image size is too small for ONH mask (need to be at least 4mm since the mask is 4mm)
    if float(canvas.image_size_var.get()) < 4:
        messagebox.showwarning(
            "Image Too Small", "ONH mask requires image size to be at least 4mm."
        )
        return
    
    subwindow_onh = Toplevel()
    subwindow_onh.title("Optical Nerve Head Editor")
    subwindow_onh.geometry("800x650")
    subwindow_onh.configure(bg="#FBE3D6")

    # States
    subwindow_onh.original_pil = Image.fromarray(
        canvas.original_img.astype(np.uint8), mode="L"
    )
    subwindow_onh.zoom_level = 1.0
    subwindow_onh.active_tool = "drag"  # "drag", "pan", "zoom"
    subwindow_onh.sq_start = None  # Start point of square
    subwindow_onh.sq_end = None  # End point of square
    subwindow_onh.pan_start = None
    subwindow_onh.pan_offset = [0, 0]
    subwindow_onh.dragging_box = False  # Track if dragging entire bounding box
    subwindow_onh.drag_box_start = None  # Starting position for box drag
    subwindow_onh.canvas_height_prev = None  # Track canvas height for coordinate rescaling on window resize
        
    # Edit: Show header if editable
    # Header frame (title and toolbox)
    header_frame = Frame(subwindow_onh, bg="#FBE3D6", height=50)
    header_frame.pack(side="top", fill="x", padx=10, pady=5)

    # Header text
    header_label = Label(
        header_frame,
        text="Adjust the position of the ring mask for ONH analysis",
        font=("Roboto", 14),
        bg="#FBE3D6",
        fg=theme_blue,
    )
    header_label.pack(side="top", padx=5)

    # Canvas frame (must be created before set_active_tool function)
    subcanvas_onh = Canvas(
        subwindow_onh,
        bg="#FBE3D6",
        bd=0,
        highlightthickness=0,
        relief="ridge", # elevated style
        cursor="crosshair",
    )
    subcanvas_onh.pack(fill="both", expand=True, padx=50, pady=(5, 10))
    
      # Confirm button
    button_confirm = ctk.CTkButton(
        subwindow_onh,
        text="Done",
        command=lambda: on_close(),
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
        subwindow_onh.active_tool = tool_name

        # Update button colors
        for name, btn in subwindow_onh.tool_buttons.items():
            if name == tool_name:
                print("Setting active tool button to yellow highlight color:", name)
                btn.configure(fg_color=button_yellow_hover)
            else:
                btn.configure(fg_color=button_blue_colour)

        # Update cursor
        #! See https://www.tcl-lang.org/man/tcl8.6/TkCmd/cursors.htm (stdlib\tkinter\__init__.pyi), some wont work cross platform
        if tool_name == "drag":
            subcanvas_onh.config(cursor="crosshair")
        elif tool_name == "pan":
            subcanvas_onh.config(cursor="fleur")
        elif tool_name == "zoom":
            subcanvas_onh.config(cursor="double_arrow")
        else:
            subcanvas_onh.config(cursor="crosshair")

    def pack_tool_button(button, text):
        button.pack(side="left", padx=2)
        subwindow_onh.tool_buttons[text] = button

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
    subwindow_onh.tool_buttons = {}

  # Load tool icons
    icon_drag_pil = Image.open(ICONS_PATH / "drag.png")
    icon_pan_pil = Image.open(ICONS_PATH / "pan.png")
    icon_zoom_pil = Image.open(ICONS_PATH / "zoom.png")
    
    # Convert to CTkImage for proper rendering
    # icon_draw = ctk.CTkImage(light_image=icon_draw_pil, dark_image=icon_draw_pil, size=(24, 24))
    icon_drag = ctk.CTkImage(light_image=icon_drag_pil, dark_image=icon_drag_pil, size=(24, 24))
    icon_pan = ctk.CTkImage(light_image=icon_pan_pil, dark_image=icon_pan_pil, size=(24, 24))
    icon_zoom = ctk.CTkImage(light_image=icon_zoom_pil, dark_image=icon_zoom_pil, size=(24, 24))

    # Draw tool button
    btn_drag = ctk.CTkButton(
        tools_frame, image=icon_drag, text="", command=lambda: set_active_tool("drag"), **btn_config
    )
    pack_tool_button(btn_drag, "drag")

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
    set_active_tool("drag") 

    # Edit: Update image display after 1. pan 2. zoom 3. drag rings
    def update_image_display():
        # Get current canvas size
        canvas_width = subcanvas_onh.winfo_width()
        canvas_height = subcanvas_onh.winfo_height()

        if canvas_width == 0 or canvas_height == 0:
            # Canvas not yet rendered
            return
        else:
            # Clear canvas before redrawing
            subcanvas_onh.delete("all")

        # Fit to canvas
        display_height = int(canvas_height * subwindow_onh.zoom_level)
        display_width = int(display_height)

        print("Updating image display with zoom level:", subwindow_onh.zoom_level, "and pan offset:", subwindow_onh.pan_offset, "and canvas_height/display_height:", canvas_height, display_height, "and img position: ", getattr(subwindow_onh, "img_position", None))

        # Initialize default ring positions to center of the image on first render
        if subwindow_onh.canvas_height_prev is None:
            center_x = display_width // 2
            center_y = display_height // 2
            default_radius = size_to_pixels(2) * (display_width / canvas.original_img.shape[0]) # 2mm radius == 4mm diameter default mask scaled rel. canvas
            subwindow_onh.sq_start = (center_x - default_radius, center_y - default_radius)
            subwindow_onh.sq_end = (center_x + default_radius, center_y + default_radius)
            print("Initializing default ring positions at the center x, y:", subwindow_onh.sq_start, subwindow_onh.sq_end)

        # Handle if window resize: relative positions to be maintained, others like display will be refitted without need to scale
        if subwindow_onh.canvas_height_prev is not None and subwindow_onh.canvas_height_prev != canvas_height:
            scale_ratio = canvas_height / subwindow_onh.canvas_height_prev
            print(f"Canvas height changed from {subwindow_onh.canvas_height_prev} to {canvas_height}, rescaling square points by {scale_ratio}")
            if subwindow_onh.sq_start and subwindow_onh.sq_end:
                subwindow_onh.sq_start = (
                    subwindow_onh.sq_start[0] * scale_ratio,
                    subwindow_onh.sq_start[1] * scale_ratio
                )
                subwindow_onh.sq_end = (
                    subwindow_onh.sq_end[0] * scale_ratio,
                    subwindow_onh.sq_end[1] * scale_ratio
                )
            subwindow_onh.pan_offset[0] *= scale_ratio
            subwindow_onh.pan_offset[1] *= scale_ratio
        
        # Update previous canvas height
        subwindow_onh.canvas_height_prev = canvas_height

        # Create image copy for drawing
        img_to_display = subwindow_onh.original_pil.copy()

        # Zoom: Resize image
        resized_img = img_to_display.resize(
            (display_width, display_height), Image.LANCZOS
        )
        img_tk = ImageTk.PhotoImage(resized_img)

        # Pan: Add x/y offset
        img_x = canvas_width // 2 + subwindow_onh.pan_offset[0]
        img_y = canvas_height // 2 + subwindow_onh.pan_offset[1]
        subcanvas_onh.create_image(
            img_x, img_y, image=img_tk, anchor="center", tags="image"
        )

        # Draw: update relative position for point mapping
        subwindow_onh.img_display_size = (display_width, display_height)
        subwindow_onh.img_position = (
            img_x - display_width // 2,
            img_y - display_height // 2,
        )
  
        # square: Draw the cropping square if both start and end points exist
        if subwindow_onh.sq_start and subwindow_onh.sq_end:
            
            # Convert display coordinates to canvas coordinates
            x1 = subwindow_onh.img_position[0] + subwindow_onh.sq_start[0] * subwindow_onh.zoom_level
            y1 = subwindow_onh.img_position[1] + subwindow_onh.sq_start[1] * subwindow_onh.zoom_level
            x2 = subwindow_onh.img_position[0] + subwindow_onh.sq_end[0] * subwindow_onh.zoom_level
            y2 = subwindow_onh.img_position[1] + subwindow_onh.sq_end[1] * subwindow_onh.zoom_level
            
            # Calculate center and radii from bounding box (square coordinates)
            # Bounding box is still used internally but not displayed
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Outer radius is half the width/height of bounding box
            radius_outer = min(abs(x2 - x1), abs(y2 - y1)) / 2
            # Inner radius is half of outer (1:2 ratio as per MATLAB)
            radius_inner = radius_outer / 2
            
            # Draw outer ring
            subcanvas_onh.create_oval(
                center_x - radius_outer, center_y - radius_outer,
                center_x + radius_outer, center_y + radius_outer,
                outline="red",
                width=2,
                tags="ring_outer"
            )
            
            # Draw inner ring
            subcanvas_onh.create_oval(
                center_x - radius_inner, center_y - radius_inner,
                center_x + radius_inner, center_y + radius_inner,
                outline="yellow",
                width=2,
                tags="ring_inner"
            )
            
        # Keep reference to prevent garbage collection
        subcanvas_onh.image_ref = img_tk

    # Helper function to check if mouse is inside the square
    def is_inside_square(canvas_x, canvas_y):
        """Returns True if point is inside the square"""
        if not (subwindow_onh.sq_start and subwindow_onh.sq_end):
            return False
        
        # Convert display coordinates to canvas coordinates
        x1 = subwindow_onh.img_position[0] + subwindow_onh.sq_start[0] * subwindow_onh.zoom_level
        y1 = subwindow_onh.img_position[1] + subwindow_onh.sq_start[1] * subwindow_onh.zoom_level
        x2 = subwindow_onh.img_position[0] + subwindow_onh.sq_end[0] * subwindow_onh.zoom_level
        y2 = subwindow_onh.img_position[1] + subwindow_onh.sq_end[1] * subwindow_onh.zoom_level
        
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        distance = ((canvas_x - center_x) ** 2 + (canvas_y - center_y) ** 2) ** 0.5
        return distance <= (x2 - x1) / 2
    
    # Event handlers
    # Handle active tool selected/mouse positions for cursor changes
    # @listener mouse motion
    def on_mouse_motion(event):
        """Update cursor when hovering over corners or center"""
        if subwindow_onh.active_tool == "drag":
            if is_inside_square(event.x, event.y):
                subcanvas_onh.config(cursor="fleur")  # Move cursor for center
            else:
                subcanvas_onh.config(cursor="crosshair")
        elif subwindow_onh.active_tool == "pan":
            subcanvas_onh.config(cursor="fleur")
        elif subwindow_onh.active_tool == "zoom":
            subcanvas_onh.config(cursor="double_arrow")

    # Handle mouse click on canvas
    # @listener left mouse click
    def on_canvas_click(event):
        print("Canvas clicked at:", event.x, event.y)
        
        if subwindow_onh.active_tool == "pan":
            print("[on_canvas_click] Pan registered")
            # Register the starting pan position
            subwindow_onh.pan_start = (event.x, event.y)
            
        elif subwindow_onh.active_tool == "drag":
            # Check if clicking on center handle for moving rings
            if is_inside_square(event.x, event.y):
                print("[on_canvas_click] Starting center drag")
                subwindow_onh.dragging_box = True
                subwindow_onh.drag_box_start = (event.x, event.y)
                return
            
    # Handle mouse wheel for zooming when zoom tool is active
    # @listener mouse wheel
    def on_mouse_wheel(event):
        print("Mouse wheel event:", event.delta)
        if subwindow_onh.active_tool == "zoom":
            # Determine zoom direction
            if event.delta > 0:
                # Zoom in
                subwindow_onh.zoom_level *= 1.1
            else:
                # Zoom out
                subwindow_onh.zoom_level /= 1.1

            # Clamp zoom level from 0.5x to 5x (when zooming out too much, points cant be assigned)
            subwindow_onh.zoom_level = max(0.5, min(subwindow_onh.zoom_level, 5))
            update_image_display()

    # Handle drag motion and end
    # @listener mouse drag events
    def on_drag_motion(event):
        if subwindow_onh.active_tool == "pan" and subwindow_onh.pan_start:
            # Handle pan motion
            print("Pan motion at:", event.x, event.y)
            dx = event.x - subwindow_onh.pan_start[0]
            dy = event.y - subwindow_onh.pan_start[1]
            subwindow_onh.pan_offset[0] += dx
            subwindow_onh.pan_offset[1] += dy
            subwindow_onh.pan_start = (event.x, event.y)
            update_image_display()
        
        elif subwindow_onh.active_tool == "drag" and subwindow_onh.dragging_box:
            # Handle dragging entire bounding box
            if hasattr(subwindow_onh, "img_position"):
                # Convert event (rel. canvas) positions to image (rel. display) coordinates
                cursor_x = (event.x - subwindow_onh.img_position[0]) / subwindow_onh.zoom_level
                cursor_y = (event.y - subwindow_onh.img_position[1]) / subwindow_onh.zoom_level
                
                start_cursor_x = (subwindow_onh.drag_box_start[0] - subwindow_onh.img_position[0]) / subwindow_onh.zoom_level
                start_cursor_y = (subwindow_onh.drag_box_start[1] - subwindow_onh.img_position[1]) / subwindow_onh.zoom_level
                
                dx = cursor_x - start_cursor_x
                dy = cursor_y - start_cursor_y
                
                # Update both corners to move the box
                start_x = subwindow_onh.sq_start[0] + dx
                start_y = subwindow_onh.sq_start[1] + dy
                end_x = subwindow_onh.sq_end[0] + dx
                end_y = subwindow_onh.sq_end[1] + dy
                length = abs(end_x - start_x)
                
                # Clamp x coordinates
                if start_x < 0:
                    start_x = 0
                    end_x = length
                elif end_x > subwindow_onh.img_display_size[0] / subwindow_onh.zoom_level:
                    end_x = subwindow_onh.img_display_size[0] / subwindow_onh.zoom_level
                    start_x = end_x - length
                    
                # Clamp y coordinates
                if start_y < 0:
                    start_y = 0
                    end_y = length
                elif end_y > subwindow_onh.img_display_size[1] / subwindow_onh.zoom_level:
                    end_y = subwindow_onh.img_display_size[1] / subwindow_onh.zoom_level
                    start_y = end_y - length
                
                subwindow_onh.sq_start = (start_x, start_y)
                subwindow_onh.sq_end = (end_x, end_y)

                subwindow_onh.drag_box_start = (event.x, event.y)  # Update start position for next frame
                update_image_display()

    # Handle both pan and drag end
    # @listener mouse button release events
    def on_drag_end(event):
        if subwindow_onh.active_tool == "pan":
            subwindow_onh.pan_start = None
        elif subwindow_onh.active_tool == "drag":
            # Finished dragging center
            subwindow_onh.dragging_box = False
            subwindow_onh.drag_box_start = None
            # Update cursor
            if is_inside_square(event.x, event.y):
                subcanvas_onh.config(cursor="fleur")
            else:
                subcanvas_onh.config(cursor="crosshair")

    # Handle canvas resize event
    # @listener canvas resize events
    def on_canvas_resize(event):
        if event.widget == subcanvas_onh:
            new_width = event.width
            new_height = event.height
            print(f"Canvas resized to: {new_width}x{new_height}")
            # update display
            update_image_display()

    def confirm_square():
        if not (subwindow_onh.sq_start and subwindow_onh.sq_end):
            return
        
        result = messagebox.askyesno(
            title="ONH Ring Confirmation",
            message="Apply these ring masks for analysis?",
            parent=subwindow_onh
        )
        if result is True:  # Yes - Save
            # Scale to original image size
            orig_height, orig_width = canvas.original_img.shape
            print("Original image size:", orig_width, orig_height, "and display size:", subwindow_onh.img_display_size)
            scale_x = orig_width / subwindow_onh.img_display_size[0] * subwindow_onh.zoom_level
            scale_y = orig_height / subwindow_onh.img_display_size[1] * subwindow_onh.zoom_level

            # Get square coordinates
            x1, y1 = subwindow_onh.sq_start
            x2, y2 = subwindow_onh.sq_end
            
            # Calculate center in display coordinates
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Scale rel. original image coordinates
            center_x_orig = int(center_x * scale_x)
            center_y_orig = int(center_y * scale_y)
            radius_outer_orig = int((x2 - x1) / 2 * scale_x)
            radius_inner_orig = int((x2 - x1) / 2 * scale_x) / 2

            # Store ring parameters and create mask for @author Joshua's future use
            canvas.onh_center = (center_x_orig, center_y_orig)
            canvas.onh_radius_outer = radius_outer_orig
            canvas.onh_radius_inner = radius_inner_orig
            
            # Create intersection mask between inner and outer ring
            y_coords, x_coords = np.ogrid[:orig_height, :orig_width]
            dist_from_center = np.sqrt((x_coords - center_x_orig)**2 + (y_coords - center_y_orig)**2)
            inter_mask = (dist_from_center > radius_inner_orig) & (dist_from_center <= radius_outer_orig)
            
            # Store intersection for @author Joshua's future use   
            masked_img = np.where(inter_mask, canvas.original_img, 0).astype(np.uint8)
            canvas.onh_mask_arr = inter_mask
            canvas.onh_mask_img = masked_img

            masked_preview = resize_image(
                Image.fromarray(masked_img, mode="L"),
                (200, 200)
            )
            masked_preview_tk = ImageTk.PhotoImage(masked_preview)
            if hasattr(canvas, "original_img_id"):
                canvas.itemconfigure(canvas.original_img_id, image=masked_preview_tk)
            else:
                canvas.original_img_id = canvas.create_image(550, 255, image=masked_preview_tk)
            if not hasattr(canvas, "_image_refs"):
                canvas._image_refs = {}
            canvas._image_refs["original_img"] = masked_preview_tk

            # # --- Save binary image to local ---
            # curr_idx = len([f for f in os.listdir(os.path.join(canvas.save_dir, "images")) if 'ONH_Mask' in f])
            # img_path = os.path.join(canvas.save_dir, "images", f"{canvas.FileLabelName}_ONH_Mask_{curr_idx}.png")
            # cv2.imwrite(img_path, masked_img)

            print(f"ONH mask saved. Center: ({center_x_orig}, {center_y_orig}), Inner radius: {radius_inner_orig}, Outer radius: {radius_outer_orig}")
                
        subwindow_onh.destroy()
        
    # Key Binding events
    subcanvas_onh.bind("<Motion>", on_mouse_motion)
    subcanvas_onh.bind("<ButtonPress-1>", on_canvas_click)
    subcanvas_onh.bind("<B1-Motion>", on_drag_motion)
    subcanvas_onh.bind("<ButtonRelease-1>", on_drag_end)
    subcanvas_onh.bind("<MouseWheel>", on_mouse_wheel)
    subcanvas_onh.bind("<Configure>", on_canvas_resize)

    # Close window event
    def on_close():
        confirm_square()

    # Initial display after window is rendered (100ms)
    subwindow_onh.after(100, update_image_display)

    subwindow_onh.protocol("WM_DELETE_WINDOW", on_close)
    subwindow_onh.resizable(True, True)
    subwindow_onh.mainloop()
