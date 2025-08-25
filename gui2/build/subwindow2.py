from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel


def close(subwindow):
  subwindow.destroy()
  subwindow.update()

def subwindow2():
  REGIONAL_ANALYSIS_ASSETS_PATH = Path("/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui2/subwindow2/build/assets/frame0")
   

  def relative_to_assets(path: str) -> Path:
      return REGIONAL_ANALYSIS_ASSETS_PATH / path


  subwindow = Toplevel()
  subwindow.title("Regional analysis settings")
  subwindow.geometry("349x380")
  subwindow.configure(bg = "#FBE3D6")


  canvas = Canvas(
      subwindow,
      bg = "#FBE3D6",
      height = 380,
      width = 349,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  canvas.place(x = 0, y = 0)
  canvas.create_text(
      45.0,
      27.0,
      anchor="nw",
      text="Regional analysis settings",
      fill="#10203F",
      font=("Roboto Bold", 16 * -1)
  )

  canvas.create_text(
      48.0,
      72.0,
      anchor="nw",
      text="Eyes",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      106.0,
      anchor="nw",
      text="Load FAZ masks",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      140.0,
      anchor="nw",
      text="Square grid",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      174.0,
      anchor="nw",
      text="ETDRS grid",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      208.0,
      anchor="nw",
      text="Extended DTDRS grid",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      242.0,
      anchor="nw",
      text="Foveal rings",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      276.0,
      anchor="nw",
      text="Optic nerve head",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  button_image_1 = PhotoImage(
      file=relative_to_assets("button_1.png"))
  button_1 = Button(
      subwindow,
      image=button_image_1,
      borderwidth=0,
      highlightthickness=0,
      command=lambda: close(subwindow),
      relief="flat"
  )
  button_1.place(
      x=114.0,
      y=314.0,
      width=121.0,
      height=37.0
  )
  subwindow.resizable(False, False)
  subwindow.mainloop()
