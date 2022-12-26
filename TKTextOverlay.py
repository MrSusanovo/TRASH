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

class OLGOverlay():
    def __init__(self):
        self.TextOverlay = TextOverlay()
        self.data = {"rc":0,"tc":0,"remaining":0,"bet":0,"fund":0,"state":0,"detect":None,"count":None,"action":None}
        self.OLGFormat = f"RC: {rc}, TC: {tc}, Remain: {remaining}\nBet:{bet}, Fund:{fund}, State:{state}\nDetect:{detect}, Count:{count}, Action:{action}"

    def Update(self):
        self.TextOverlay.Print(self.OLGFormat.format(**self.data))
    def destroy(self):
        self.TextOverlay.destroy()
