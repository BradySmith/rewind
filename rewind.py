import cv2
import subprocess
import os
import os.path

# With the current load ~7 frames a second.
FRAMES_TO_KEEP_BEFORE = 50
FRAMES_TO_KEEP_AFTER = 20

FRAME_LOOP = True
FILE_LOCK = "/home/pi/rewind/loop.lock"


def removeAllFilesInFolder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)

        except Exception as e:
            print(e)


def getFramesLoop():
    removeAllFilesInFolder("/home/pi/rewind/frames")
    cap = cv2.VideoCapture(0)
    index = 0
    FRAME_LOOP = True

    while FRAME_LOOP:
        try:
            os.remove("/home/pi/rewind/frames/frame%d.jpg" % (index - FRAMES_TO_KEEP_BEFORE))
        except OSError:
            pass

        getFrame(index, cap)
        index += 1

        # Reset index when the number gets too big.
        if index == 100000000:
            index = 0

        if os.path.isfile(FILE_LOCK):
            FRAME_LOOP = False

    # Take a few more frames.
    print "Interrupt detected, taking the after frames."
    for i in range(index, index + FRAMES_TO_KEEP_AFTER):
        getFrame(i, cap)


def getFrame(index, cap):
    ret, frame = cap.read()
    name = "/home/pi/rewind/frames/frame%d.jpg" % index
    cv2.imwrite(name, frame)


def makeGif():
    print "Making gif"

    try:
        executeShellCommand(
            "convert -delay 15x100 /home/pi/rewind/frames/frame*.jpg -rotate 180 -loop 0 /home/pi/rewind/output.gif")
        print "Finished making gif"
        return True

    except KeyboardInterrupt:
        print "Interrupt detected. Exiting"
        return False


def postGifToSlack():
    executePipedShellCommand("echo 'Uploading gif. Please hold.'", "slacker -c intersection-gifs -f /home/pi/rewind/output.gif")


def executeShellCommand(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]


def executePipedShellCommand(command1, command2):
    p1 = subprocess.Popen(command1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(command2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output, err = p2.communicate()

def removeLock():
    try:
        os.remove(FILE_LOCK)
    except OSError:
        pass

if __name__ == '__main__':
    removeLock()
    while True:
        getFramesLoop()
        makeGif()
        postGifToSlack()
        removeLock()
