import tkinter as tk
from CommonTools import *
import win32gui 
class TextOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_overrideredirect(True)
        self.root.geometry("+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        
        self.label = tk.Label(text='', font=("Helvetica", 20), fg = 'red', bg='white')
        self.label.pack(expand=True)
        self.label.master.wm_attributes("-transparentcolor", "white")

        self.root.update()
        self.hwnd = GetHWNDByKeyword('tk')
    
    def destroy(self):
        self.label.destroy()
        self.root.destroy()
    
    def MoveToFront(self):
        win32gui.SetForegroundWindow(self.hwnd)
    
    def Print(self, t):
        self.label.config(text=t)
        self.root.update()
        self.MoveToFront()