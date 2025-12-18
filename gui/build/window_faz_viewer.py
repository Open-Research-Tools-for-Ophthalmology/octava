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
import cv2
from modules.resize_image import *
from PIL import Image, ImageTk
from modules.faz_utils import display_faz_image, load_faz_grayscale_arr
from modules.auto_faz.auto_faz import auto_faz


def subwindow4(canvas, editable=False):
    # Check if an image is loaded
    if not hasattr(canvas, "original_img"):
        messagebox.showwarning(
            "No Image Loaded", "Please load an image before processing."
        )
        return

    subwindow4 = Toplevel()
    subwindow4.title(editable and "FAZ Editor" or "FAZ Viewer")
    subwindow4.geometry("800x650")
    subwindow4.configure(bg="#FBE3D6")

    # States
    subwindow4.original_pil = Image.fromarray(
        canvas.original_img.astype(np.uint8), mode="L"
    )
    subwindow4.zoom_level = 1.0
    subwindow4.active_tool = "draw"  # TODO "draw/drag", "pan", "zoom" , "null"
    subwindow4.polygon_points = []
    subwindow4.pan_start = None
    subwindow4.pan_offset = [0, 0]
    subwindow4.drag_point_index = None  # Track which point is being dragged


    # Drag: ask if want to load existing grayscale mask
    draggable = False
    if editable and hasattr(canvas, "faz_grayscale_arr") and canvas.faz_grayscale_arr is not None:
        result = messagebox.askyesno(
            title="Load Confirmation",
            message="You have an existing FAZ segmentation. Do you want to load it?",
            parent=subwindow4
        ) # assign parent to focus on subwindow4
        if result is True: 
            draggable = True

    # Edit: Show header if editable
    if editable:
        # Header frame (title and toolbox)
        header_frame = Frame(subwindow4, bg="#FBE3D6", height=50)
        header_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Header text
        header_label = Label(
            header_frame,
            text=("Drag " if draggable else "Click ") + "points to define a polygon around the FAZ",
            font=("Roboto", 14),
            bg="#FBE3D6",
            fg=theme_blue,
        )
        header_label.pack(side="top", padx=5)
    
    # Canvas frame (must be created before set_active_tool function)
    subcanvas4 = Canvas(
        subwindow4,
        bg="#FBE3D6",
        bd=0,
        highlightthickness=0,
        relief="ridge", # elevated style
        cursor="crosshair" if editable else "arrow",
    )
    subcanvas4.pack(fill="both", expand=True, padx=50, pady=(5, 10))
    
    # Edit: Show tool frame if editable
    if editable:
        def set_active_tool(tool_name):
            print("Tool set to :", tool_name)
            subwindow4.active_tool = tool_name

            # Update button colors
            for name, btn in subwindow4.tool_buttons.items():
                if name == tool_name:
                    print("Setting active tool button to yellow highlight color:", name)
                    btn.configure(fg_color=button_yellow_hover)
                else:
                    btn.configure(fg_color=button_blue_colour)

            # Update cursor
            #! See https://www.tcl-lang.org/man/tcl8.6/TkCmd/cursors.htm (stdlib\tkinter\__init__.pyi), some wont work cross platform
            if tool_name == "draw":
                subcanvas4.config(cursor="crosshair")
            elif tool_name == "drag":
                subcanvas4.config(cursor="hand2")
            elif tool_name == "pan":
                subcanvas4.config(cursor="fleur")
            elif tool_name == "zoom":
                subcanvas4.config(cursor="double_arrow")
            else:
                subcanvas4.config(cursor="crosshair")

        def pack_tool_button(button, text):
            button.pack(side="left", padx=2)
            subwindow4.tool_buttons[text] = button

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
        subwindow4.tool_buttons = {}

        if draggable:
            # Drag tool button
            btn_drag = ctk.CTkButton(
                tools_frame, text="⦿", command=lambda: set_active_tool("drag"), **btn_config
            )
            pack_tool_button(btn_drag, "drag")
        else:
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

        # Editor initialization, set draw/drag tool as active by default
        set_active_tool("drag" if draggable else "draw")

    # Edit: Update image display after 1. pan 2. zoom
    def update_image_display():
        print("Updating image display with zoom level:", subwindow4.zoom_level, "and pan offset:", subwindow4.pan_offset)
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
        display_height = int(canvas_height * subwindow4.zoom_level)
        display_width = int(display_height)

        # Create image copy for drawing
        img_to_display = subwindow4.original_pil.copy()

        # Zoom: Resize image
        resized_img = img_to_display.resize(
            (display_width, display_height), Image.LANCZOS
        )
        img_tk = ImageTk.PhotoImage(resized_img)

        # Pan: Add x/y offset
        img_x = canvas_width // 2 + subwindow4.pan_offset[0]
        img_y = canvas_height // 2 + subwindow4.pan_offset[1]
        subcanvas4.create_image(
            img_x, img_y, image=img_tk, anchor="center", tags="image"
        )

        # Draw: update relative position for point mapping
        subwindow4.img_display_size = (display_width, display_height)
        subwindow4.img_position = (
            img_x - display_width // 2,
            img_y - display_height // 2,
        )
  
        # Polygon: If first point is last point, then fill the polygon
        if len(subwindow4.polygon_points) > 2 and subwindow4.polygon_points[0] == subwindow4.polygon_points[-1]:
            print("Filling polygon with points:", subwindow4.polygon_points)
            
            # Canvas polygon accepts a flattened list of x,y coordinates
            flat_points = []
            for point in subwindow4.polygon_points:
                x = subwindow4.img_position[0] + point[0] * subwindow4.zoom_level
                y = subwindow4.img_position[1] + point[1] * subwindow4.zoom_level
                flat_points.extend([x, y])
            subcanvas4.create_polygon(*flat_points, fill='#800080', outline="black", tags="polygon")
        
        # Lines: if polygon hasn't been enclosed yet
        for i, point in enumerate(subwindow4.polygon_points):
            x = subwindow4.img_position[0] + point[0] * subwindow4.zoom_level
            y = subwindow4.img_position[1] + point[1] * subwindow4.zoom_level
            subcanvas4.create_oval( # I know it says oval but it's our circle
                x - 4, y - 4, x + 4, y + 4, fill=point_blue_colour, outline="black", tags="point"
            )

            # Draw lines
            if i > 0:
                prev_point = subwindow4.polygon_points[i - 1]
                prev_x = subwindow4.img_position[0] + prev_point[0] * subwindow4.zoom_level
                prev_y = subwindow4.img_position[1] + prev_point[1] * subwindow4.zoom_level
                subcanvas4.create_line(
                    prev_x, prev_y, x, y, fill=point_blue_colour, width=3, tags="line"
                )

        # Keep reference to prevent garbage collection
        subcanvas4.image_ref = img_tk

    # View: Display fixed image without interaction
    # TODO the result from auto faz is binary mask, lets show the FAZ overlay on original image instead
    def display_fixed_image():
        # FIXME here the FAZ is loading from local file, which evades the resize logic
        grayscale_arr = auto_faz(filepath=canvas.filePath)

        # grayscale image from array
        grayscale_img = Image.fromarray(grayscale_arr.astype(np.uint8), mode='L')

        # colour image from array
        colour_arr = cv2.cvtColor(grayscale_arr, cv2.COLOR_GRAY2RGB)
        # Convert white to purple
        colour_arr[np.where((colour_arr == [255, 255, 255]).all(axis=2))] = (128, 0, 128)
        colour_img = Image.fromarray(colour_arr.astype(np.uint8), mode='RGB')

        # Make black pixels alpha=0 transparent
        alpha = np.sum(colour_arr, axis=-1) > 0
        alpha = np.uint8(alpha * 255)
        transparent_img = Image.fromarray(np.dstack((colour_arr, alpha)), mode='RGBA') # A for alpha channel
        print("grayscale_arr type/shape:", type(grayscale_arr), grayscale_arr.shape, "grayscale_img type:", type(grayscale_img), "colour_img type:", type(colour_img), "transparent_img type:", type(transparent_img))

        # Store to main canvas
        canvas.faz_grayscale_arr = grayscale_arr
        canvas.faz_grayscale_img = grayscale_img
        # canvas.faz_colour_img = colour_img
        # canvas.faz_transparent_img = transparent_img

        # Fit to canvas
        canvas_width = subcanvas4.winfo_width()
        canvas_height = subcanvas4.winfo_height()
        display_height = canvas_height
        display_width = display_height

        # Resize image
        # Create image copy for background, convert to RGBA for overlay
        img_to_display = subwindow4.original_pil.copy().convert("RGBA")
        
        # Resize both images to display size
        #! PhotoImage.paste: The size must match the target region.
        #! PhotoImage.paste: If the mode does not match, the image is converted to the mode of the bitmap image 
        #! which our original iamge is grayscale, an "L" with no A and RGB
        resized_background = img_to_display.resize(
            (display_width, display_height), Image.LANCZOS
        )
        resized_overlay = transparent_img.resize(
            (display_width, display_height), Image.LANCZOS
        )

        # Composite the overlay on top of the background
        resized_background.paste(resized_overlay, (0, 0), resized_overlay)
        print("resized_background channels:", resized_background.getbands())

        img_tk = ImageTk.PhotoImage(resized_background)

        # Center image
        img_x = canvas_width // 2
        img_y = canvas_height // 2
        subcanvas4.create_image(
            img_x, img_y, image=img_tk, anchor="center", tags="image"
        )

        # Keep reference to prevent garbage collection
        subcanvas4.image_ref = img_tk


    # Event handlers - unified approach to prevent tool switching conflicts
    # Handle mouse click on canvas
    # @listener left mouse click
    def on_canvas_click(event):
        print("Canvas clicked at:", event.x, event.y)
        
        # Reset all interaction states when clicking
        subwindow4.drag_point_index = None  # Clear any drag state
        
        if subwindow4.active_tool == "pan":
            print("[on_canvas_click] Pan registered")
            # Register the starting pan position
            subwindow4.pan_start = (event.x, event.y)
            
        elif subwindow4.active_tool == "draw":
            print("[on_canvas_click] Adding polygon point")
            subwindow4.pan_start = None  # Clear pan state
            
            # Add point to polygon
            if hasattr(subwindow4, "img_position") and hasattr(
                subwindow4, "img_display_size"
            ):
                # Convert canvas coordinates to image coordinates
                img_x = (event.x - subwindow4.img_position[0]) / subwindow4.zoom_level
                img_y = (event.y - subwindow4.img_position[1]) / subwindow4.zoom_level

                # Check if click is within image bounds
                if (
                    0 <= img_x <= subwindow4.img_display_size[0]
                    and 0 <= img_y <= subwindow4.img_display_size[1]
                ):
                    # Check if clicking near first point to close the polygon
                    if len(subwindow4.polygon_points) > 2:
                        first_point = subwindow4.polygon_points[0]
                        distance = (
                            (img_x - first_point[0]) ** 2
                            + (img_y - first_point[1]) ** 2
                        ) ** 0.5

                        if distance < 10:  # Close polygon
                            subwindow4.polygon_points.append((first_point[0], first_point[1]))
                            print("polygon_points: ", subwindow4.polygon_points)
                            update_image_display()
                            set_active_tool("null")  # Disable further drawing
                            confirm_polygon()
                            return
                        
                    # Add new point
                    subwindow4.polygon_points.append((img_x, img_y))
                    update_image_display()
                    
        elif subwindow4.active_tool == "drag":
            print("[on_canvas_click] Drag point selected")
            subwindow4.pan_start = None  # Clear pan state
            
            # Check if clicking near an existing point to start dragging
            img_x = (event.x - subwindow4.img_position[0]) / subwindow4.zoom_level
            img_y = (event.y - subwindow4.img_position[1]) / subwindow4.zoom_level

            for i, point in enumerate(subwindow4.polygon_points):
                distance = ((img_x - point[0]) ** 2 + (img_y - point[1]) ** 2) ** 0.5
                if distance < 5:
                    print("Selected point for dragging:", point)
                    subwindow4.drag_point_index = i  # Store which point we're dragging
                    break

    # Handle mouse wheel for zooming when zoom tool is active
    # @listener mouse wheel
    def on_mouse_wheel(event):
        print("Mouse wheel event:", event.delta)
        if subwindow4.active_tool == "zoom":
            # Determine zoom direction
            if event.delta > 0:
                # Zoom in
                subwindow4.zoom_level *= 1.1
            else:
                # Zoom out
                subwindow4.zoom_level /= 1.1

            # Clamp zoom level from 0.5x to 5x (when zooming out too much, points cant be assigned)
            subwindow4.zoom_level = max(0.5, min(subwindow4.zoom_level, 5))
            update_image_display()

    # Handle drag motion and end
    # @listener mouse drag events
    def on_drag_motion(event):
        if subwindow4.active_tool == "pan" and subwindow4.pan_start:
            # Handle pan motion
            print("Pan motion at:", event.x, event.y)
            dx = event.x - subwindow4.pan_start[0]
            dy = event.y - subwindow4.pan_start[1]
            subwindow4.pan_offset[0] += dx
            subwindow4.pan_offset[1] += dy
            subwindow4.pan_start = (event.x, event.y)
            update_image_display()
            
        elif subwindow4.active_tool == "drag" and subwindow4.drag_point_index is not None:
            # Handle drag motion
            img_x = (event.x - subwindow4.img_position[0]) / subwindow4.zoom_level
            img_y = (event.y - subwindow4.img_position[1]) / subwindow4.zoom_level
            # If the drag item is the first/last point, update them both
            if subwindow4.drag_point_index == 0:
                subwindow4.polygon_points[0] = (img_x, img_y)
                subwindow4.polygon_points[-1] = (img_x, img_y)
            else:
                subwindow4.polygon_points[subwindow4.drag_point_index] = (img_x, img_y)
            update_image_display()

    # Unified release handler - handles both pan and drag end
    def on_drag_end(event):
        if subwindow4.active_tool == "pan":
            subwindow4.pan_start = None
        elif subwindow4.active_tool == "drag":
            subwindow4.drag_point_index = None

    def confirm_polygon():
        result = messagebox.askyesno(
            title="Segmentation Confirmation",
            message="Is segmentation sufficient?",
            parent=subwindow4
        ) # assign parent to focus on subwindow4
        if result is True:  # Yes - Save
            # Save the polygon information to main canvas
            messagebox.showinfo("Saved", "FAZ polygon saved successfully!")
            canvas.faz_polygon_points = subwindow4.polygon_points

            # Store binary mask to canvas
            grayscale_arr = np.zeros(canvas.original_img.shape, dtype=np.uint8)

            # Create a mask from the polygon points
            poly_arr = np.array(subwindow4.polygon_points, dtype=np.int32)
            # Refit to original image size
            poly_arr = (poly_arr * canvas.original_img.shape[0] / subwindow4.img_display_size[1] * subwindow4.zoom_level).astype(np.int32)
            grayscale_arr = cv2.fillPoly(grayscale_arr, [poly_arr], color=255)
            grayscale_img = Image.fromarray(grayscale_arr.astype(np.uint8), mode='L')
            print("grayscale_arr type/shape:", type(grayscale_arr), grayscale_arr.shape, "grayscale_img type:", type(grayscale_img))

            # Store to main canvas
            canvas.faz_grayscale_arr = grayscale_arr
            canvas.faz_grayscale_img = grayscale_img

            # Destroy the window and show preview!
            subwindow4.destroy()
            display_faz_image(canvas)

        elif result is False:  # No - Draw again (Edit: Clear canvas) (Drag: Close without saving)
            if draggable:
                # Just close the window without saving
                subwindow4.destroy()
                return
            subwindow4.polygon_points = []
            set_active_tool("draw")
            update_image_display()

    # Key Binding events - unified event handlers
    subcanvas4.bind("<ButtonPress-1>", on_canvas_click)
    subcanvas4.bind("<B1-Motion>", on_drag_motion)
    subcanvas4.bind("<ButtonRelease-1>", on_drag_end)
    subcanvas4.bind("<MouseWheel>", on_mouse_wheel)

    # Close window event
    def on_close():
        print("FAZ Viewer/Editer closed.")

        if draggable:
            return confirm_polygon()

        # Purge!
        subwindow4.destroy()

        if not editable:
            # Viewer: send for preview
            display_faz_image(canvas)

    # Initial display after window is rendered (100ms)
    subwindow4.after(100, update_image_display if editable else display_fixed_image)

    # Drag: load existing grayscale mask and make dragable polygon (200ms)
    if draggable:
        def load_existing_polygon():
            polygon_points = load_faz_grayscale_arr(canvas)
            # TODO Scale polygon_points to current image display size
            scale_ratio = subcanvas4.winfo_height() / canvas.faz_grayscale_arr.shape[1]
            print("draggable subcanvas4.winfo_height(), canvas.faz_grayscale_arr.height, image scale_ratio:", subcanvas4.winfo_height(), canvas.faz_grayscale_arr.shape[1], scale_ratio)
            polygon_points = [(pt[0] * scale_ratio, pt[1] * scale_ratio) for pt in polygon_points]
            polygon_points.append(polygon_points[0]) # close the polygon
            subwindow4.polygon_points = polygon_points
            print("Loaded existing FAZ polygon points:", subwindow4.polygon_points)
            update_image_display() # render the calculated polygon
        
        subwindow4.after(200, load_existing_polygon)

    subwindow4.protocol("WM_DELETE_WINDOW", on_close)
    subwindow4.resizable(True, True)
    subwindow4.mainloop()
