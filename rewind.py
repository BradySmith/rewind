import cv2
import subprocess
import os, shutil

FRAMES_TO_KEEP = 10


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
                os.remove("frames/frame%d.jpg" % (index - FRAMES_TO_KEEP))
            except OSError:
                pass

            ret, frame = cap.read()
            name = "frames/frame%d.jpg" % index
            cv2.imwrite(name, frame)
            index += 1

            # Reset index when the number gets too big
            if (index == 100000000):
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
