# -----------------------------------------------------------------------------
# Sketch Maker Application
#
# Description:
#   This application transforms images into artistic sketch-like drawings.
#   Users can load an image, adjust settings for noise reduction, line detail,
#   and thickness, and save the resulting sketch.
#
# Developer:
#   - Name: Cyrax Kane
#   - Contact: cynetixsolution@gmail.com
#   - GitHub: https://github.com/your_github_profile
#
# To run this application, you need the following Python libraries:
# - opencv-python: For image processing.
# - numpy: For numerical operations.
# - Pillow (PIL): For integrating images with tkinter.
#
# You can install them using pip:
# pip install opencv-python numpy Pillow
#
# To launch the application, run this script from your terminal:
# python3 Edge_Maker.py
# -----------------------------------------------------------------------------

import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, IntVar, messagebox
from tkinter import ttk
from PIL import Image, ImageTk

# --- Color Constants ---
BG_COLOR = '#2E2E2E'
FG_COLOR = '#FFFFFF'
ACCENT_COLOR = '#4A90E2'
HOVER_COLOR = '#5AA0F2'
BORDER_COLOR = '#4A4A4A'

def create_edge_drawing(img, median_blur_ksize, adaptive_thresh_block_size, adaptive_thresh_C, mode):
    """
    Creates an edge drawing from an image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if median_blur_ksize % 2 == 0:
        median_blur_ksize += 1
    gray_blurred = cv2.medianBlur(gray, median_blur_ksize)

    if adaptive_thresh_block_size <= 1:
        adaptive_thresh_block_size = 3
    if adaptive_thresh_block_size % 2 == 0:
        adaptive_thresh_block_size += 1
    edges = cv2.adaptiveThreshold(gray_blurred, 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, adaptive_thresh_block_size, adaptive_thresh_C)

    if mode == 0:  # Black on White
        return cv2.bitwise_not(edges)
    else:  # White on Black
        return edges

class SketchMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sketch Maker")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(800, 600)

        self.input_image = None
        self.output_image = None
        self.last_w = 0
        self.last_h = 0

        self.setup_styles()
        self.setup_ui()

        default_image_path = "test.png"
        if os.path.exists(default_image_path):
            self.load_image(default_image_path)

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure('.', background=BG_COLOR, foreground=FG_COLOR)
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR, padding=5, font=('Helvetica', 10))
        style.configure('TButton', background=ACCENT_COLOR, foreground='white', padding=10, font=('Helvetica', 10, 'bold'), borderwidth=0)
        style.map('TButton', background=[('active', HOVER_COLOR), ('hover', HOVER_COLOR)])
        
        style.configure('TRadiobutton', background=BG_COLOR, foreground=FG_COLOR, font=('Helvetica', 10))
        style.map('TRadiobutton', background=[('active', BG_COLOR)])

        style.configure('TScale', background=ACCENT_COLOR)
        style.configure('TLabelframe', background=BG_COLOR, bordercolor=BORDER_COLOR, relief=tk.SOLID)
        style.configure('TLabelframe.Label', background=BG_COLOR, foreground=ACCENT_COLOR, font=('Helvetica', 11, 'bold'))

    def setup_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Top Frame (Title) ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(top_frame, text="Sketch Maker", font=('Helvetica', 24, 'bold'), foreground=ACCENT_COLOR, anchor="center").grid(row=0, column=0)

        # --- Middle Frame ---
        middle_frame = ttk.Frame(self.root, padding="10")
        middle_frame.grid(row=1, column=0, sticky="nsew")
        middle_frame.grid_columnconfigure(1, weight=1)
        middle_frame.grid_rowconfigure(0, weight=1)

        # --- Control Frame (Left) ---
        control_frame = ttk.Frame(middle_frame, width=200)
        control_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        control_frame.grid_propagate(False)

        ttk.Button(control_frame, text="Open Image", command=self.open_image).pack(pady=10, fill=tk.X)
        mode_frame = ttk.LabelFrame(control_frame, text="Mode", padding="15")
        mode_frame.pack(pady=10, fill=tk.X)
        self.mode = IntVar()
        self.mode.set(0)
        ttk.Radiobutton(mode_frame, text="Black on White", variable=self.mode, value=0, command=self.update_image).pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="White on Black", variable=self.mode, value=1, command=self.update_image).pack(anchor="w")
        ttk.Button(control_frame, text="Save Image", command=self.save_image).pack(pady=10, side="bottom", fill=tk.X)
        ttk.Button(control_frame, text="Exit", command=self.root.destroy).pack(pady=5, side="bottom", fill=tk.X)

        # --- Image Frame (Right) ---
        self.image_frame = ttk.Frame(middle_frame)
        self.image_frame.grid(row=0, column=1, sticky="nsew")
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(1, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.bind("<Configure>", self.on_resize)

        self.input_label = ttk.Label(self.image_frame, text="Input Image", anchor=tk.CENTER)
        self.input_label.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.output_label = ttk.Label(self.image_frame, text="Output Image", anchor=tk.CENTER)
        self.output_label.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # --- Bottom Frame (Settings) ---
        bottom_frame = ttk.LabelFrame(self.root, text="Settings", padding="10")
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=1)

        noise_frame = ttk.Frame(bottom_frame)
        noise_frame.grid(row=0, column=0, sticky="ew", padx=5)
        ttk.Label(noise_frame, text="Noise Reduction").pack()
        self.noise_reduction = ttk.Scale(noise_frame, from_=1, to=21, orient=tk.HORIZONTAL, command=self.update_image)
        self.noise_reduction.set(5)
        self.noise_reduction.pack(fill=tk.X)

        detail_frame = ttk.Frame(bottom_frame)
        detail_frame.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(detail_frame, text="Line Thickness").pack()
        self.line_detail = ttk.Scale(detail_frame, from_=3, to=31, orient=tk.HORIZONTAL, command=self.update_image)
        self.line_detail.set(9)
        self.line_detail.pack(fill=tk.X)

        thickness_frame = ttk.Frame(bottom_frame)
        thickness_frame.grid(row=0, column=2, sticky="ew", padx=5)
        ttk.Label(thickness_frame, text="Line Details").pack()
        self.line_thickness = ttk.Scale(thickness_frame, from_=1, to=21, orient=tk.HORIZONTAL, command=self.update_image)
        self.line_thickness.set(9)
        self.line_thickness.pack(fill=tk.X)

        # --- Footer ---
        footer_frame = ttk.Frame(self.root, padding="5")
        footer_frame.grid(row=3, column=0, sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(footer_frame, text="Developed by Cyrax Kane", font=("Helvetica", 8), anchor="center").grid(row=0, column=0)

    def on_resize(self, event):
        if event.width == self.last_w and event.height == self.last_h:
            return
        self.last_w, self.last_h = event.width, event.height
        self.display_loaded_images()

    def display_loaded_images(self):
        if self.input_image is not None:
            self.display_image(self.input_image, self.input_label)
        if self.output_image is not None:
            self.display_image(cv2.cvtColor(self.output_image, cv2.COLOR_GRAY2BGR), self.output_label)

    def load_image(self, path):
        try:
            n = np.fromfile(path, np.uint8)
            self.input_image = cv2.imdecode(n, cv2.IMREAD_COLOR)
            if self.input_image is None:
                raise ValueError("Image file could not be decoded.")
            self.update_image()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def open_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.load_image(path)

    def display_image(self, img_cv, label):
        label_w = self.image_frame.winfo_width() // 2
        label_h = self.image_frame.winfo_height()
        if label_w < 20 or label_h < 20: return

        h, w = img_cv.shape[:2]
        scale = min(label_w/w, label_h/h)
        if scale == 0: return
        
        img_resized = cv2.resize(img_cv, (int(w*scale), int(h*scale)))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        label.config(image=img_tk)
        label.image = img_tk

    def update_image(self, *args):
        if self.input_image is None: return

        noise = int(self.noise_reduction.get())
        detail = int(self.line_detail.get())
        thickness = int(self.line_thickness.get())
        mode = self.mode.get()

        self.output_image = create_edge_drawing(self.input_image, noise, detail, thickness, mode)
        self.display_loaded_images()

    def save_image(self):
        if self.output_image is not None:
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            path = filedialog.asksaveasfilename(initialdir=output_dir, defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")])
            if path:
                try:
                    _, buf = cv2.imencode(os.path.splitext(path)[1], self.output_image)
                    buf.tofile(path)
                    print(f"Image saved to {path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save image: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SketchMakerApp(root)
    root.mainloop()
