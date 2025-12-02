import numpy as np
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HistogramPlotter:
    def __init__(self, master_frame, bg_color, bar_color, axis_color):
        """
        Initializes the plot and embeds it into the master_frame.
        """
        self.bg_color = bg_color
        self.bar_color = bar_color
        self.axis_color = axis_color
        
        # 1. Generate mock data (can be replaced with real data setter later)
        self.data = np.random.normal(50, 15, 500)

        # 2. Setup Figure
        self.fig = Figure(figsize=(2.4, 2.0), dpi=100)
        self.fig.patch.set_facecolor(self.bg_color)
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.bg_color)
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0.15, bottom=0.15, right=0.95, top=0.9)

        # 3. Embed Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=master_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


    def update_plot(self, bin_size):
        """
        Recalculates bins based on bin_size and redraws the plot.
        """
        self.current_bin_size = bin_size
        self.ax.clear()
        
        size = int(bin_size)

        # Calculate bins
        if len(self.data) > 0:
            self.ax.axis('on')
            bins = np.arange(min(self.data), max(self.data) + size, size)
            self.ax.hist(self.data, bins=bins, color=self.bar_color, 
                         alpha=0.8, edgecolor='black', linewidth=0.5)
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color(self.axis_color)
            self.ax.spines['bottom'].set_color(self.axis_color)
            self.ax.tick_params(axis='both', colors=self.axis_color, labelsize=8)
        else:
            self.ax.axis('off')
        self.canvas.draw()
        
    def set_data(self, new_data):
        """External method to update the dataset (for future use)."""
        self.data = new_data
        self.update_plot(bin_size=1) # Reset view

    def save_plot(self):
        current_size = getattr(self, 'current_bin_size', 5)
        default_name = f"Vessel Diameter Distribution (Bin size = {current_size})"
        filename = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("PDF", "*.pdf")],
            title="Save Histogram"
        )
        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor=self.bg_color)
            print(f"Histogram saved to {filename}")   