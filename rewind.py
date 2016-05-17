from multiprocessing import Process, Value
import subprocess
import cv2


def getFramesLoop(count, loopBool):
    while loopBool:
        # Capture frame-by-frame
        ret, frame = cap.read()
        count.value = count.value + 1
        index = count.value

        name = "frames/frame%d.jpg" % index
        cv2.imwrite(name, frame)
        print index

        if (index > 10):
            loopBool = False


def makeGif():
    bashCommand = "convert -background white -alpha remove -layers OptimizePlus -delay 25x100 /home/pi/rewind/frames/frame*.jpg -loop 0 output.gif"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output


if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    loopBool = Value('b', True)
    count = Value('d', 0.0)

    p = Process(target=getFramesLoop, args=(count, loopBool))
    p.start()
    p.join()

    makeGif()
