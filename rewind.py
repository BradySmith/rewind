import cv2
import subprocess


def getFramesLoop():
    cap = cv2.VideoCapture(0)
    index = 0
    while True:
        try:
            ret, frame = cap.read()
            name = "frames/frame%d.jpg" % index
            cv2.imwrite(name, frame)
            index += 1

            # Limit to 10 frame gifs
            if (index > 10):
                index = 0

        except KeyboardInterrupt:
            break

    return True


def makeGif():
    print "Making gif"
    try:
        bashCommand = "convert -background white -alpha remove -layers OptimizePlus -delay 25x100 /home/pi/rewind/frames/frame*.jpg -loop 0 output.gif"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print "Finished making gif"
        return True
    except KeyboardInterrupt:
        print "Interrupt dectected. Exiting"
        return False


if __name__ == '__main__':
    loop = True
    while loop:
        getFramesLoop()
        loop = makeGif()
