import cv2
import subprocess
import os

FRAMES_TO_KEEP_BEFORE = 10
FRAMES_TO_KEEP_AFTER = 10


def removeAllFilesInFolder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)

        except Exception as e:
            print(e)


def getFramesLoop():
    removeAllFilesInFolder("frames")
    cap = cv2.VideoCapture(0)
    index = 0
    while True:
        try:
            try:
                os.remove("frames/frame%d.jpg" % (index - FRAMES_TO_KEEP_BEFORE))
            except OSError:
                pass

            getFrame(index, cap)
            index += 1

            # Reset index when the number gets too big.
            if index == 100000000:
                index = 0

        except KeyboardInterrupt:
            # Take a few more frames.
            print "Interrupt detected, taking the after frames."
            for i in range(index, index + FRAMES_TO_KEEP_AFTER):
                getFrame(i, cap)

            break

    return True


def getFrame(index, cap):
    ret, frame = cap.read()
    name = "frames/frame%d.jpg" % index
    cv2.imwrite(name, frame)


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
