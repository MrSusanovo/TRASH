import numpy as np
from CommonTools import *
from YoloTools import yolo_down, yolo_up
import cv2
import time
import os
# Constants.
INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.45
CONFIDENCE_THRESHOLD = 0.2

# Text parameters.
FONT_FACE = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.5
THICKNESS = 1

# Colors.
BLACK  = (0,0,0)
BLUE   = (255,178,50)
YELLOW = (0,255,255)

pa = (537,468)
pb = (831, 595)
#pa = (728,542)
#pb = (794,586)
classes = ['1','2','3','4','5','6','7','8','9','10','11','12','13']
def cropMatrix(img, rect):
    w = int(rect[2]-rect[0]) + 1
    h = int(rect[3]-rect[1]) + 1
    new_img = np.zeros((h,w,3))
    new_img += img[int(rect[1]):int(rect[3]),int(rect[0]):int(rect[2]),:]
    canvas = np.zeros((640,640,3))
    canvas[:h,:w,:] = new_img
    return canvas


def draw_label(im, label, x, y):
    """Draw text onto image at location."""
    # Get text size.
    text_size = cv2.getTextSize(label, FONT_FACE, FONT_SCALE, THICKNESS)
    dim, baseline = text_size[0], text_size[1]
    # Use text size to create a BLACK rectangle.
    cv2.rectangle(im, (x,y), (x + dim[0], y + dim[1] + baseline), (0,0,0), cv2.FILLED);
    # Display text inside the rectangle.
    cv2.putText(im, label, (x, y + dim[1]), FONT_FACE, FONT_SCALE, YELLOW, THICKNESS, cv2.LINE_AA)

def post_process_no_draw(input_image, outputs):
    # Lists to hold respective values while unwrapping.
    class_ids = []
    confidences = []
    boxes = []
    # Rows.
    rows = outputs[0].shape[1]
    image_height, image_width = input_image.shape[:2]
    # Resizing factor.
    x_factor = image_width / INPUT_WIDTH
    y_factor =  image_height / INPUT_HEIGHT
    # Iterate through detections.
    for r in range(rows):
        row = outputs[0][0][r]
        confidence = row[4]
        # Discard bad detections and continue.
        if confidence >= CONFIDENCE_THRESHOLD:
            classes_scores = row[5:]
            # Get the index of max class score.
            class_id = np.argmax(classes_scores)
            #  Continue if the class score is above threshold.
            if (classes_scores[class_id] > SCORE_THRESHOLD):
                confidences.append(confidence)
                class_ids.append(class_id)
                cx, cy, w, h = row[0], row[1], row[2], row[3]
                left = int((cx - w/2) * x_factor)
                top = int((cy - h/2) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                box = np.array([left, top, width, height])
                boxes.append(box)
     # Perform non maximum suppression to eliminate redundant, overlapping boxes with lower confidences.
    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
    b_buf = []
    c_buf = []
    for i in indices:
        b_buf.append(boxes[i])
        c_buf.append(classes[class_ids[i]])
    return (b_buf,c_buf)

def post_process_mask(input_image, raw_result):
    # filter outputs
    confidence_mask = (raw_result[0][:,:,4].max(axis=0) > CONFIDENCE_THRESHOLD)
    outputs = raw_result[0][:,confidence_mask,:]
    #print(outputs.shape)
    class_score_mask = (outputs[:,:,5:].max(axis=2) > SCORE_THRESHOLD)[0]
    outputs = outputs[:,class_score_mask,:]
    #print(outputs.shape)
    # Lists to hold respective values while unwrapping.
    class_ids = []
    confidences = []
    boxes = []
    # Rows.
    rows = outputs.shape[1]
    image_height, image_width = input_image.shape[:2]
    # Resizing factor.
    x_factor = image_width / INPUT_WIDTH
    y_factor =  image_height / INPUT_HEIGHT
    # Iterate through detections.
    for r in range(rows):
        row = outputs[0][r]
        confidence = row[4]
        class_id = np.argmax(row[5:])
        
        #  Continue if the class score is above threshold.
        confidences.append(confidence)
        class_ids.append(class_id)
        cx, cy, w, h = row[0], row[1], row[2], row[3]
        left = int((cx - w/2) * x_factor)
        top = int((cy - h/2) * y_factor)
        width = int(w * x_factor)
        height = int(h * y_factor)
        box = np.array([left, top, width, height])
        boxes.append(box)
     # Perform non maximum suppression to eliminate redundant, overlapping boxes with lower confidences.
    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
    
    b_buf = []
    c_buf = []
    for i in indices:
        b_buf.append(boxes[i])
        c_buf.append(classes[class_ids[i]])
    return (b_buf,c_buf)
    '''
    for i in indices:
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]             
        # Draw bounding box.             
        cv2.rectangle(input_image, (left, top), (left + width, top + height), BLUE, THICKNESS)
        # Class label.                      
        label = "{}:{:.2f}".format(classes[class_ids[i]], confidences[i])             
        # Draw label.             
        draw_label(input_image, label, left+width, top+height)
    return input_image
    '''
    

def post_process(input_image, outputs):
    # Lists to hold respective values while unwrapping.
    class_ids = []
    confidences = []
    boxes = []
    # Rows.
    rows = outputs[0].shape[1]
    image_height, image_width = input_image.shape[:2]
    # Resizing factor.
    x_factor = image_width / INPUT_WIDTH
    y_factor =  image_height / INPUT_HEIGHT
    # Iterate through detections.
    for r in range(rows):
        row = outputs[0][0][r]
        confidence = row[4]
        # Discard bad detections and continue.
        if confidence >= CONFIDENCE_THRESHOLD:
            classes_scores = row[5:]
            # Get the index of max class score.
            class_id = np.argmax(classes_scores)
            #  Continue if the class score is above threshold.
            if (classes_scores[class_id] > SCORE_THRESHOLD):
                confidences.append(confidence)
                class_ids.append(class_id)
                cx, cy, w, h = row[0], row[1], row[2], row[3]
                left = int((cx - w/2) * x_factor)
                top = int((cy - h/2) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                box = np.array([left, top, width, height])
                boxes.append(box)
     # Perform non maximum suppression to eliminate redundant, overlapping boxes with lower confidences.
    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
    for i in indices:
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]             
        # Draw bounding box.             
        cv2.rectangle(input_image, (left, top), (left + width, top + height), BLUE, THICKNESS)
        # Class label.                      
        label = "{}:{:.2f}".format(classes[class_ids[i]], confidences[i])             
        # Draw label.             
        draw_label(input_image, label, left+width, top+height)
    return input_image

#net = cv2.dnn.readNet('last.onnx')
net = cv2.dnn.readNetFromONNX('last40000.onnx')
def cropAndSave(fname):
    img = Image.open(fname)
    #subimg = img.crop(screenToImgRect(yolo_up,yolo_down,img))
    subimg = img.crop(screenToImgRect(pa,pb,img))
    subimg.save('test1.png')

def predictFromFile(fname, use_mask = True):
    canvas = cv2.imread(fname)
    result = predict(canvas, use_mask)
    cv2.imwrite('predict1.png',result)

def inference(canvas):
    blob = cv2.dnn.blobFromImage(canvas, 1/255,(640,640),[0,0,0],1, crop=False)
    #blob = cv2.dnn.blobFromImage(canvas, 1/255,(480,480),[0,0,0],1, crop=False)
    net.setInput(blob)
    return net.forward(net.getUnconnectedOutLayersNames())


def predict(canvas, use_mask = True):
    '''
    blob = cv2.dnn.blobFromImage(canvas, 1/255,(640,640),[0,0,0],1, crop=False)
    #blob = cv2.dnn.blobFromImage(canvas, 1/255,(480,480),[0,0,0],1, crop=False)
    net.setInput(blob)
    outputs = net.forward(net.getUnconnectedOutLayersNames())
    r = post_process(canvas.copy(),outputs)
    '''
    #r = post_process(canvas.copy(),inference(canvas))
    r = post_process_mask(canvas.copy(),inference(canvas)) if use_mask else post_process(canvas.copy(),inference(canvas))
    return r

def cropAndPredict(fname, use_mask = True):
    cropAndSave(fname)
    predictFromFile('test1.png', use_mask)

def predictVideo(fname):
    vidcap = cv2.VideoCapture(fname)
    success, image = vidcap.read()
    count = 0
    dim_img = ImageGrab.grab()
    rect = [ int(i) for i in screenToImgRect(pa,pb,dim_img) ]
    w = int(rect[2] - rect[0])
    h = int(rect[3] - rect[1])
    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    vidwriter = cv2.VideoWriter('outvid.mp4', fourcc, 30.0, (w,h))
    while success:
        new_img = predict(image[rect[1]:rect[3],rect[0]:rect[2],:])
        vidwriter.write(new_img)
        success, image = vidcap.read()
    vidwriter.release()
    vidcap.release()
    os.system('shutdown /s /t 1')

def realtimePredict():
    
    pic_buff = []
    box_buff = []
    class_buff = []
    output_buf = []
    dim_img = ImageGrab.grab()
    rect = [ int(i) for i in screenToImgRect(pa,pb,dim_img) ]
    w = int(rect[2] - rect[0])
    h = int(rect[3] - rect[1])
    start_time = time.perf_counter()
    for i in range(100):
        fullframe = ImageGrab.grab()
        cropframe = fullframe.crop(screenToImgRect(pa,pb,fullframe))
        cvframe = cv2.cvtColor(np.array(cropframe),cv2.COLOR_BGR2RGB)
        # Predict
        blob = cv2.dnn.blobFromImage(cvframe, 1/255,(640,640),[0,0,0],1, crop=False)
        #blob = cv2.dnn.blobFromImage(cvframe, 1/255,(480,480 ),[0,0,0],1, crop=False)
        net.setInput(blob)
        outputs = net.forward(net.getUnconnectedOutLayersNames())
        boxes,classes = post_process_no_draw(cvframe,outputs)
        output_buf.append(outputs)
        pic_buff.append(cvframe)
        #box_buff.append(boxes)
        #class_buf.append(classes)
    end_time = time.perf_counter()
    print("FPS:",100/(end_time-start_time))
    # write to video
    #fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    #vidwriter = cv2.VideoWriter('realtime_capture.mp4', fourcc, 30.0, (w,h))
    for i in range(len(output_buf)):
        img = post_process(pic_buff[i].copy(),output_buf[i])
        cv2.imwrite("realtime_capture/img"+str(i)+".png",img)
    #vidwriter.release()
        
