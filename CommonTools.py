from ctypes import windll, Structure, c_long, byref
import win32api, win32con, re, winsound, win32gui, win32console
from pytesseract import pytesseract
import numpy as np
import cv2, time
from PIL import ImageGrab, Image
from BlackJack import *
import inspect

# Screen Dimension
screenWidth = windll.user32.GetSystemMetrics(0)
screenHeight = windll.user32.GetSystemMetrics(1)

defaultDC = win32gui.GetDC(win32gui.GetActiveWindow())

# tesseract config
tconfig = "-c tessedit_char_whitelist=0123456789/ --psm 9"

# setup tesseract
pytesseract.tesseract_cmd = "tesseract.exe"

# a dictionary of all window and their hwnd, key is window name
window_tups = []
window_search_cache = {}

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
    time.sleep(0.1)
    return win32gui.GetForegroundWindow()

def SetupAllWindowHWND():
    window_tups.clear()
    window_search_cache.clear()
    def windowEnumHandler(hwnd, top_windows):
        top_windows.append((hwnd,win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(windowEnumHandler, window_tups)

def GetHWNDByKeyword(keyword):
    # check if we initialized all windows
    if len(window_tups) == 0:
        SetupAllWindowHWND()
    
    hwnd = window_search_cache.get(keyword)

    # if didn't find in cache, do a loop search.
    if hwnd == None:
        for i in window_tups:
            if keyword.lower() in i[1].lower():
                hwnd = i[0]
                window_search_cache[keyword] = hwnd
                break
    return hwnd

def SetFrontWindowByKeyword(keyword):
    hwnd = GetHWNDByKeyword(keyword)
    if hwnd == None:
        print("Failed to find window by keyword:", keyword)
        return False

    win32gui.SetForegroundWindow(hwnd)
    return True

def MoveConsoleToFront():
    win32gui.ShowWindow(win32console.GetConsoleWindow(),2)
    win32gui.ShowWindow(win32console.GetConsoleWindow(),1)

 
def screenToImg(pt,img):
    return (pt[0] * (img.size[0]*1.0/screenWidth), pt[1] * (img.size[1]*1.0/screenHeight))

def getColor(pt, src = None):
    #click(pt)  
    img = ImageGrab.grab() if src == None else src
    color = img.getpixel(screenToImg(pt,img))
    return color

# Color comparison
def colorCompare(c1, c2, t, ERR):
    if t == 'rgb':
        #print(np.sqrt(sum((c1 - c2)**2)))
        return np.sqrt(sum((c1 - c2)**2)) < ERR
    else:
        #print(c1,c2,t)
        return abs(c1[t]-c2[t]) < ERR

def BGRInt2RGBTup(bgr):
    red = bgr & 255
    green = (bgr>>8) & 255
    blue = (bgr>>16) & 255
    return (red,green,blue)

def RGB2HSV(rgb):
    r = rgb[0]/255
    g = rgb[1]/255
    b = rgb[2]/255
    cmax = max(r,g,b)
    cmin = min(r,g,b)
    delta = cmax-cmin
    s = 0 if cmax == 0 else delta/cmax
    h = 0
    if delta != 0:
        if cmax == r:
            h = 60 * (((g-b)/delta)%6)
        elif cmax == g:
            h = 60 * (((b-r)/delta)+2)
        else:
            h = 60 * (((r-g)/delta)+4)
    return (h,s,cmax)

def getColorWIN32(pt,winDC = defaultDC, screen_dim=(1920,1080), ):
    x = int(pt[0]*screen_dim[0]/screenWidth)
    y = int(pt[1]*screen_dim[1]/screenHeight)
    #return BGRInt2RGBTup(win32gui.GetPixel(win32gui.GetDC(win32gui.GetActiveWindow()), x , y))
    return BGRInt2RGBTup(win32gui.GetPixel(winDC, x , y))

def PerfTimer(func, times, arg):
    start = time.perf_counter()
    for i in range(times):
        func(arg)
    end = time.perf_counter()
    return end - start

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
    # subimg_bw = toThreshold(subimg) if BW == True else toBilateral(subimg)
    subimg_bw = toThreshold(subimg) if BW == True else subimg
    if show:
        subimg.show()
        subimg_bw.show()
    text = pytesseract.image_to_string(subimg_bw, config = configs)
    return text

def getTextNoCrop(src, configs, BL = False, BW = False, show = False):
    subimg = toBilateral(src) if BL == True else src
    subimg_bw = toThreshold(subimg) if BW == True else subimg
    if show:
        subimg.show()
        subimg_bw.show()
    text = pytesseract.image_to_string(subimg_bw, config = configs)
    return text

def CalculatePoints(cards):
    large_sum = 0
    small_sum = 0
    seen_ace = False
    for card in cards:
        soft_amnt = amnt = card
        if card % 10 == 1:
            amnt = soft_amnt = 1
            if seen_ace == False:
                soft_amnt += 10
            seen_ace = True
        small_sum += amnt
        large_sum += soft_amnt
        #print(small_sum,large_sum,seen_ace)
    
    if seen_ace and large_sum > 21:
        seen_ace = False 
        large_sum -= 10

    return seen_ace,max(large_sum,small_sum)
    
def Test(cards, TC, split):
    is_soft, points = CalculatePoints(cards)
    for i in range(1,11):
        print(i, Decide(cards, TC, points, i, is_soft, split), is_soft, cards, points)

def TestWindows():
    while True:
        SetFrontWindowByKeyword("pywin32")
        time.sleep(0.05)
        pos = queryPos()
        color = getColorWIN32(pos)
        if color[0] < 128:
            print(color)
            break
        console_window = win32console.GetConsoleWindow()
        print("console window:",console_window)
        win32gui.SetForegroundWindow(console_window)

def GetCaller(index = 1):
    return inspect.stack()[index].function