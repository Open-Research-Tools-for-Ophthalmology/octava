from os import path, listdir, rename
import tkinter as tk
from tkinter import Label, filedialog, ttk, messagebox
from pandas import read_excel
from load_image import *

def main():
    root = tk.Tk()
    root.title('Image Renamer')
    root.geometry("900x600")
    root.resizable(0, 0) 

    # Create and configure a style
    style = ttk.Style()
    style.configure('TButton', font=('Aerial', 14))

    # #Create a label and a Button to Open the dialog
    # select_oct_file_button= ttk.Button(root, text="  Select a single OCT MIP  ", command= lambda: select_file(root))
    # select_oct_file_button.pack(ipadx=2, pady=8)


    root.mainloop()









if __name__ == "__main__":
    main()