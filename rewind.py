from multiprocessing import Process, Value, Array

import numpy as np
import cv2

def getFramesLoop(count, loopBool):
	while loopBool:
	   # Capture frame-by-frame
	   ret, frame = cap.read()
	   count.value = count.value + 1 
	   index = count.value

	   name = "frames/frame%d.jpg"%index
	   cv2.imwrite(name, frame)  
	   print index 

	   if (index > 10):
	   		loopBool = False

if __name__ == '__main__':
	cap = cv2.VideoCapture(0)
	loopBool = Value('b', True)
	count = Value('d', 0.0)
    # arr = Array('i', range(10))

	p = Process(target=getFramesLoop, args=(count, loopBool))
	p.start()
	p.join()
