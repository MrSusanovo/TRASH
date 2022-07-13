from pynput.mouse import Listener
from PIL import Image, ImageGrab
from random import randint, randrange
from CommonTools import screenToImgRect
import cv2
import numpy as np

#  hardcode dimension for now
dim = (1920.0, 1080.0)

# need to be converted
infinite_up = (625, 490)
infinite_down = (913,594)
# Yolo Region, need to be converted
yolo_up = (530, 462)
yolo_down = (796, 589)


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
def ConvexHull(val, img, indices = None):
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
        #dimg.show()
        #cmd = input(str(contours[i].shape))
        #if cmd = '1':
            #contour_list[1].append(contours[i])
            #if len(contor_list) == 2:
                
        hull = cv2.convexHull(contours[i])
        hull_list.append(hull)
    # Draw contours + hull results
    #
    result_hulls = []
    if indices != None:
        for i in indices:
            result_hulls.append(hull_list[i])
        return result_hulls

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
    def __init__(self, arg):
        filename = ""
        hull_indices = None
        # Accept a list or a string as parameter
        if type(arg) == type(""):
            filename = arg
            self.label = None
        else:
            # extract filename from parameter.
            filename = arg[0]
            self.label = int(arg[-1])
            hull_indices = []
            for i in arg[1:-1]:
                hull_indices.append(int(i))
        
        self.labels = []
        self.img = Image.open(filename)
        self.imgarray = np.array(self.img)
        self.hulls = ConvexHull(70, self.img, hull_indices)
        self.bbox = []
        # self.UpdateBBox()
        self.__CreateExtendAndMask()
        self.__Centralize()

        # backup centralized data
        self.base_hulls = []
        for i in self.hulls:
            h = np.copy(i)
            self.base_hulls.append(h)
        self.base_img = np.copy(self.extended)
        self.base_mask = np.copy(self.mask_positive)
        #self.UpdateBBox()

    def Reset(self):
        self.extended = np.copy(self.base_img)
        self.mask_positive = np.copy(self.base_mask)
        self.hulls.clear()
        self.bbox = []
        self.labels = []
        for h in self.base_hulls:
            newh = np.copy(h)
            self.hulls.append(newh)
        self.UpdateBBox()

    def __CreateExtendAndMask(self):
        pts = screenToImgRect(yolo_up, yolo_down, ImageGrab.grab())
        height = int(pts[3] - pts[1])
        width = int(pts[2] - pts[0])
        # Create Extended img
        self.extended = np.zeros((height,width,3),dtype=np.uint8)
        self.extended[:self.imgarray.shape[0], :self.imgarray.shape[1]] = self.imgarray
        self.xoff = int(self.extended.shape[1]/2 - self.imgarray.shape[1]/2)
        self.yoff = int(self.extended.shape[0]/2 - self.imgarray.shape[0]/2)
        # Create Mask
        self.mask_positive = np.zeros((height,width,3), dtype=np.uint8)
        self.mask_positive[:self.imgarray.shape[0],:self.imgarray.shape[1]] = 1

    def __UpdateConvexHull(self, M, affine = True):
        # Update convex hull
        new_hull = []
        
        for h in self.hulls:
            hull_matrix = np.zeros((h.shape[0],h.shape[1],h.shape[2]+1)).transpose()
            hull_matrix[:2,:,:] = h.transpose()
            hull_matrix[2,:,:] = 1
            if affine == True:
                new_hull.append(np.dot(M,hull_matrix.reshape((3,h.shape[0]))).reshape((2,1,h.shape[0])).transpose())
            else:
                new_hull.append(np.dot(M,hull_matrix.reshape((3,h.shape[0])))[:2].reshape((2,1,h.shape[0])).transpose())
        '''
        for h in self.hulls:
            hshape = h.shape
            if affine == True:
                new_hull.append(cv2.warpAffine(h.reshape(hshape[0],hshape[2]), M, (hshape[0],hshape[2])).reshape(hshape))
            else:
                new_hull.append(cv2.warpPerspective(h.reshape(hshape[0],hshape[2]), M, (hshape[0],hshape[2])).reshape(hshape))
        '''
        self.hulls = new_hull

    def Translate(self, x, y):
        M = np.float32([[1,0,x],[0,1,y]])
        for i in range(3):
            self.extended[:,:,i] = cv2.warpAffine(self.extended[:,:,i],M,(self.extended.shape[1], self.extended.shape[0]))
            self.mask_positive[:,:,i] = cv2.warpAffine(self.mask_positive[:,:,i],M,(self.extended.shape[1], self.extended.shape[0]))
        
        self.__UpdateConvexHull(M)
    
    def RandomTrans(self):
        diag = np.sqrt(self.img.size[0]**2 + self.img.size[1]**2)
        xlimit = int((self.extended.shape[1] - diag) / 2)
        ylimit = int((self.extended.shape[0] - diag) /2)
        self.Translate(randrange(-xlimit, xlimit), randrange(-ylimit,ylimit))
    
    def Rotate(self, theta):
        h = self.extended.shape[0]
        w = self.extended.shape[1]
        M = cv2.getRotationMatrix2D(((w-1.0)/2,(h-1.0)/2),theta,1)
        #print("R shape:", M.shape)

        for i in range(3):
            self.extended[:,:,i] = cv2.warpAffine(self.extended[:,:,i], M ,(w,h))
            self.mask_positive[:,:,i] = cv2.warpAffine(self.mask_positive[:,:,i],M,(w,h))
        
        self.__UpdateConvexHull(M)
    
    # Only on centralized images
    def Perspective(self, oldpts, newpts):
        h = self.extended.shape[0]
        w = self.extended.shape[1]
        M = cv2.getPerspectiveTransform(oldpts, newpts)
        #print("P shape:",M.shape)

        for i in range(3):
            self.extended[:,:,i] = cv2.warpPerspective(self.extended[:,:,i], M, (w,h))
            self.mask_positive[:,:,i] = cv2.warpPerspective(self.mask_positive[:,:,i],M,(w,h))

        self.__UpdateConvexHull(M, False)
    
    # Randomized perspective
    def RandPerspective(self, deviation):
        pts1 = np.float32([[self.xoff, self.yoff],[self.xoff + self.imgarray.shape[1], self.yoff],[self.xoff, self.yoff + self.imgarray.shape[0]],[self.xoff+self.imgarray.shape[1], self.yoff+self.imgarray.shape[0]]])
        #deviate_pts = np.float32([[randrange(-deviation, deviation+1), randrange(-deviation, deviation+1)],[randrange(-deviation, deviation+1), randrange(-deviation, deviation+1)],[0,0],[0,0]])
        #sigma_x = randrange(-deviation,deviation+1)
        sigma_x = 0
        sigma_y = randrange(0,deviation+1)
        deviate_pts = np.float32([[-sigma_x,-sigma_y],[sigma_x, -sigma_y],[0,0],[0,0]])
        pts2 = pts1 + deviate_pts

        self.Perspective(pts1, pts2)
    
    def RandTransform(self):
        self.RandPerspective(int(self.img.size[1]/2))
        self.Rotate(randrange(-90,91))
        self.RandomTrans()
        self.UpdateBBox()
        
    def __Centralize(self):
        self.Translate(self.xoff, self.yoff)
        self.UpdateBBox()

    def CreateMask(self):
        self.reverse_mask *= 0
        self.reverse_mask += 255
        self.extended 
        #self.reverse_mask[:self.imgarray.shape[0],:self.imgarray.shape[1]] = 0
        #tempimg = Image.fromarray(np.uint8(self.reverse_mask))
        tempimg.show()
    def UpdateBBox(self, show_box = False):
        temp_img = np.copy(self.extended)
        self.bbox.clear()
        '''
        for i in self.hulls:
            min0 = int(min(i[:,0,0])-2)
            max0 = int(max(i[:,0,0])+2)
            min1 = int(min(i[:,0,1])-2)
            max1 = int(max(i[:,0,1])+2)
            self.bbox.append(((min0,min1),(max0,max1)))
            temp_img = cv2.rectangle(temp_img, self.bbox[-1][0],self.bbox[-1][1],(255,0,0),1)
            '''
        min0 = max0 = min1 = max1 = None
        for i in self.hulls:
            tmin0 = int(min(i[:,0,0]))
            tmax0 = int(max(i[:,0,0]))
            tmin1 = int(min(i[:,0,1]))
            tmax1 = int(max(i[:,0,1]))
            if min0 == None:
                min0 = tmin0
                min1 = tmin1
                max0 = tmax0
                max1 = tmax1
            else:
                min0 = min(min0,tmin0)
                min1 = min(min1,tmin1)
                max0 = max(max0, tmax0)
                max1 = max(max1, tmax1)
        self.bbox.append(((min0-2, min1-2),(max0+2,max1+2)))
        if self.label != None:
            self.labels.append(self.label)
        if show_box == True:
            temp_img = cv2.rectangle(temp_img, self.bbox[-1][0],self.bbox[-1][1],(255,0,0),1)
            temp_IMG = Image.fromarray(np.uint8(temp_img))
            temp_IMG.show()

    def OverlayImg(self, array, show = False):
        # Generate negative mask
        negative_mask = np.vectorize(lambda x: 1 if x < 1 else 0)(self.mask_positive)
        imgarray = array * negative_mask + self.extended

        # Show it
        if show == True:
            #temp_img = Image.fromarray(np.uint8(imgarray))
            #temp_img.show()
            self.DrawBBox(imgarray)
        return imgarray
    
    def DrawBBox(self,array):
        temp_img = np.copy(array)
        for box in self.bbox:
            temp_img = cv2.rectangle(temp_img, box[0],box[1],(255,0,0),1)
        temp_IMG = Image.fromarray(np.uint8(temp_img))
        temp_IMG.show()

    
    def OverlayCard(self, card, show = False):
        other_region = np.copy(card.mask_positive[:,:,0])
        other_sum = sum(sum(other_region))
        newboxes = []
        newlabels = []
        # determin if card covers existing boxes
        for box in self.bbox:
            boxmask = np.copy(self.mask_positive[:,:,0])
            boxmask *= 0
            # Watchout, np array are y x chanenl
            boxmask[box[0][1]:box[1][1]+1, box[0][0]:box[1][0]+1] = 1
            boxsum = sum(sum(boxmask))
            new_mask = np.vectorize(lambda x: 1 if x >= 1 else 0)(boxmask + other_region)
            # new_mask_img = Image.fromarray(np.uint8(new_mask * 255))
            # new_mask_img.show()
            newsum = sum(sum(new_mask))
            if newsum == (other_sum + boxsum):
                newboxes.append(box)
                newlabels.append(self.label)
        self.bbox = newboxes
        self.labels = newlabels
        # copy boxes from the other image
        for box in card.bbox:
            self.bbox.append(box)
            self.labels.append(card.label)
        self.extended = card.OverlayImg(self.extended)
        # update positive mask
        self.mask_positive = np.vectorize(lambda x: 1 if x >= 1 else 0)(self.mask_positive + card.mask_positive)
        if show == True:
            '''
            temp_img = np.copy(self.extended)
            for box in self.bbox:
                temp_img = cv2.rectangle(temp_img, box[0],box[1],(255,0,0),1)
            temp_IMG = Image.fromarray(np.uint8(temp_img))
            temp_IMG.show()
            '''
            self.DrawBBox(self.extended)


    def GetAnotation(self):
        objects = []
        index = 0
        for box in self.bbox:
            anotation = str(self.labels[index])
            width = box[1][0] - box[0][0]
            xcenter = (box[1][0] + box[0][0])/2.0
            height = box[1][1] - box[0][1]
            ycenter = (box[1][1] + box[0][1])/2.0

            r_width = width/self.extended.shape[1]
            r_height = height/self.extended.shape[0]
            r_x = xcenter/self.extended.shape[1]
            r_y = ycenter/self.extended.shape[0]
            anotation += " " + str(r_x) + " " + str(r_y) + " " + str(r_width) + " " + str(r_height)
            objects.append(anotation)
            index += 1
        return objects

    def OverlayOnBackground(self, fname, show=False):
        img = Image.open(fname)
        if img.size[0] >= self.extended.shape[1] and img.size[1] >= self.extended.shape[0]:
            # Convert to nparray
            imgarray = np.array(img.crop((0,0,self.extended.shape[1],self.extended.shape[0]))) 
            return self.OverlayImg(imgarray, show)

