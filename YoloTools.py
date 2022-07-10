from pynput.mouse import Listener
from PIL import Image
from random import randint
import cv2
import numpy as np

#  hardcode dimension for now
dim = (1920.0, 1080.0)

# need to be converted
infinite_up = (625, 490)
infinite_down = (913,594)

class CardLabeler:
    def __init__(self):
        self.point_buffer = []
        self.lines = []
    def recordPoint(self,x,y):
        self.point_buffer.append((x,y))

        if len(self.point_buffer) == 2:
            # Record the class
            c = input("Please input the classification, ints only:")
            # Convert points to relative x,y center, width and height
            w = (self.point_buffer[1][0] - self.point_buffer[0][0]) / dim[0]
            h = (self.point_buffer[1][1] - self.point_buffer[0][1]) / dim[1]
            xc = (self.point_buffer[0][0] + 1.0)/dim[0] + w/2
            yc = (self.point_buffer[0][1] + 1.0)/dim[1] + w/2
            line = c + " " + xc + " " + yc + " " + w + " " + h
            self.lines.append(line)
            self.point_buffer.clear()
    def writeTo(fname = "label0.txt"):
        f = open(fname, "w")
        for i in self.lines:
            f.write("%s\n" % i)
        print("Done")
        f.close()

labeler = None

# does not need to convert coordinate.
def label_onclick(x,y,button,pressed):
    if pressed == True:
        # record
        if labeler != None:
            labeler.recordPoint(x,y)

def SelectFrames(fname, skip = 10):
    vidcap = cv2.VideoCapture(fname)
    success, image = vidcap.read()
    count = 0
    skips = skip
    while success:
        name = fname + "." + str(count) + ".png"
        if skips > 0:
            skips -= 1
            success, image = vidcap.read()
            continue
        #cv2.imshow(name, image)
        img = Image.fromarray(np.uint8(cv2.cvtColor(image,cv2.COLOR_BGR2RGB)))
        img.show()
        cmd = input("keep?(y/n) stop?(s)")
        if cmd == 'y':
            # cv2.imwrite(name, image)
            img.save(name)
            count += 1
            skips = skip
        elif cmd == 'n':
            skips = skip
        elif cmd == 's':
            break
        success, image = vidcap.read()

# draw convex hull
def ConvexHull(val, img):
    threshold = val
    src = np.array(img)
    src_gray = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)
    # Detect edges using Canny
    canny_output = cv2.Canny(src_gray, threshold, threshold * 2,None, 3)
    # Find contours
    contours,hierarchy = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Find the convex hull object for each contour
    hull_list = []
    contour_list = [[],[]]
    for i in range(len(contours)):
        # To do, figure out a way to deal with 6 and 9.
        # idea: get the rank included, we need all 4 ranks of 6 and 9
        drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        cv2.drawContours(drawing, contours, i, (255,0,0))
        dimg = Image.fromarray(np.uint8(drawing))
        dimg.show()
        cmd = input(str(contours[i].shape))
        #if cmd = '1':
            #contour_list[1].append(contours[i])
            #if len(contor_list) == 2:
                
        hull = cv2.convexHull(contours[i])
        hull_list.append(hull)
    # Draw contours + hull results
    #
    result_hulls = []
    for i in range(len(contours)):
        #drawing = np.copy(canny_output)
        drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        color = (randint(0,256), randint(0,256), randint(0,256))
        cv2.drawContours(drawing, contours, i, color)
        cv2.drawContours(drawing, hull_list, i, color)
        dimg = Image.fromarray(np.uint8(drawing))
        dimg.show()
        cmd = input("Keep?")
        if cmd == 'y':
            result_hulls.append(hull_list[i])
        elif cmd == 's':
            break
    # Show in a window
    # cv2.imshow('Contours', drawing)
    return result_hulls

class UnitCard:
    def __init__(self, fname):
        self.img = Image.open(fname)
        self.imgarray = np.array(self.img)
        self.hulls = ConvexHull(50, self.img)
        self.bbox = []
        # self.UpdateBBox()
        self.extended = np.zeros((115,352,3),dtype=np.uint8)
        self.reverse_mask = np.zeros((115,352,3),dtype=np.uint8)
        self.extended[:self.imgarray.shape[0], :self.imgarray.shape[1]] = self.imgarray
        self.xoff = int(self.extended.shape[1]/2 - self.imgarray.shape[1]/2)
        self.yoff = int(self.extended.shape[0]/2 - self.imgarray.shape[0]/2)
        self.__Centralize()
        #self.UpdateBBox()
        
    def __UpdateConvexHull(self, M):
        # Update convex hull
        new_hull = []
        for h in self.hulls:
            hull_matrix = np.zeros((h.shape[0],h.shape[1],h.shape[2]+1)).transpose()
            hull_matrix[:2,:,:] = h.transpose()
            hull_matrix[2,:,:] = 1
            new_hull.append(np.dot(M,hull_matrix.reshape((3,h.shape[0]))).reshape((2,1,h.shape[0])).transpose())
        self.hulls = new_hull

    def Translate(self, x, y):
        M = np.float32([[1,0,x],[0,1,y]])
        for i in range(3):
            self.extended[:,:,i] = cv2.warpAffine(self.extended[:,:,i],M,(self.extended.shape[1], self.extended.shape[0]))
        
        self.__UpdateConvexHull(M)
    
    def Rotate(self, theta):
        h = self.extended.shape[0]
        w = self.extended.shape[1]
        M = cv2.getRotationMatrix2D(((w-1.0)/2,(h-1.0)/2),theta,1)

        for i in range(3):
            self.extended[:,:,i] = cv2.warpAffine(self.extended[:,:,i], M ,(w,h))
        
        self.__UpdateConvexHull(M)
        
    def __Centralize(self):
        self.Translate(self.xoff, self.yoff)

    def CreateMask(self):
        self.reverse_mask *= 0
        self.reverse_mask += 255
        self.extended 
        #self.reverse_mask[:self.imgarray.shape[0],:self.imgarray.shape[1]] = 0
        #tempimg = Image.fromarray(np.uint8(self.reverse_mask))
        tempimg.show()
    def UpdateBBox(self):
        temp_img = np.copy(self.extended)
        self.bbox.clear()
        for i in self.hulls:
            min0 = int(min(i[:,0,0])-1)
            max0 = int(max(i[:,0,0])+1)
            min1 = int(min(i[:,0,1])-1)
            max1 = int(max(i[:,0,1])+1)
            self.bbox.append(((min0,min1),(max0,max1)))
            temp_img = cv2.rectangle(temp_img, self.bbox[-1][0],self.bbox[-1][1],(255,0,0),1)
        temp_IMG = Image.fromarray(np.uint8(temp_img))
        temp_IMG.show()    



