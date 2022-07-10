from ctypes import windll, Structure, c_long, byref
import win32api, win32con, re, winsound
from pytesseract import pytesseract
import numpy as np
import cv2
from PIL import ImageGrab, Image

# Screen Dimension
screenWidth = windll.user32.GetSystemMetrics(0)
screenHeight = windll.user32.GetSystemMetrics(1)

# tesseract config
tconfig = "-c tessedit_char_whitelist=0123456789/ --psm 9"

# setup tesseract
pytesseract.tesseract_cmd = "tesseract.exe"

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

def queryPos():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return (pt.x,pt.y)

def click(pt):
    win32api.SetCursorPos(pt)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,pt[0],pt[1],0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,pt[0],pt[1],0,0)

def getWindow(pt):
    click(pt)
    sleep(0.1)
    return win32gui.GetForegroundWindow()

def screenToImg(pt,img):
    return (pt[0] * (img.size[0]*1.0/screenWidth), pt[1] * (img.size[1]*1.0/screenHeight))

def getColor(pt, src = None):
    #click(pt)
    img = ImageGrab.grab() if src == None else src
    color = img.getpixel(screenToImg(pt,img))
    return color

def screenToImgRect(pt1, pt2, img):
    img1 = screenToImg(pt1, img)
    img2 = screenToImg(pt2, img)
    return (img1[0],img1[1],img2[0],img2[1])

def toBilateral(img):
    src = np.array(img)
    blur = cv2.bilateralFilter(src, 5,75,75)
    return Image.fromarray(np.uint8(blur))

def toThreshold(img):
    src = np.array(img)
    gray = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)
    #blur = cv2.GaussianBlur(gray,(3,3),cv2.BORDER_DEFAULT)
    # blur = cv2.bilateralFilter(src, 5,75,75)
    ret,thr1 = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
    return Image.fromarray(np.uint8(thr1))

def getText(up, down, configs, BL = False, BW = False, show=False, src = None):
    img = ImageGrab.grab() if src == None else src
    rect = screenToImgRect(up,down,img)
    subimg = toBilateral(img.crop(rect)) if BL == True else img.crop(rect)
    # pre_process subimg
    subimg_bw = toThreshold(subimg) if BW == True else toBilateral(subimg)
    if show:
        subimg.show()
        subimg_bw.show()
    text = pytesseract.image_to_string(subimg_bw, config = configs)
    return text
