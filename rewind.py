import cv2
import subprocess
import os
import os.path
from PIL import Image
from shutil import copyfile


# With the current load ~7 frames a second.
FRAMES_TO_KEEP_BEFORE = 50
FRAMES_TO_KEEP_AFTER = 20
LOG_CHANNEL = "bot-log"
GIF_CHANNEL = "intersection-gifs"

FRAME_LOOP = True
FILE_LOCK = "/home/pi/rewind/loop.lock"
PREVIEW_FILE = "/tmp/preview.jpg"
TEMP_PREVIEW_FILE = "/tmp/tmp.jpg"


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

        name = getFrame(index, cap)
        index += 1

        if index % 10 == 0:
            makePreview(name)

        # Reset index when the number gets too big.
        if index == 100000000:
            index = 0

        if os.path.isfile(FILE_LOCK):
            FRAME_LOOP = False

    # Take a few more frames.
    broadcastToSlack("Gif requested, building now - please hold.")
    for i in range(index, index + FRAMES_TO_KEEP_AFTER):
        getFrame(i, cap)


def getFrame(index, cap):
    ret, frame = cap.read()
    name = "/home/pi/rewind/frames/frame%d.jpg" % index
    cv2.imwrite(name, frame)
    return name


def makePreview(name):
    copyfile(name, TEMP_PREVIEW_FILE)

    image = Image.open(TEMP_PREVIEW_FILE)
    image = image.rotate(180)
    image.save(PREVIEW_FILE)


def logToSlack(message):
    sendToSlack(message, LOG_CHANNEL)


def broadcastToSlack(message):
    sendToSlack(message, GIF_CHANNEL)


def sendToSlack(message, channel):
    executePipedShellCommand("echo " + message, "slacker -c " + channel)


def makeGif():
    try:
        executeShellCommand(
            "convert -delay 15x100 /home/pi/rewind/frames/frame*.jpg -rotate 180 -loop 0 /home/pi/rewind/output.gif")
        logToSlack("Finished making gif")
        return True

    except KeyboardInterrupt:
        print "Interrupt detected. Exiting"
        return False


def postGifToSlack():
    executePipedShellCommand("echo Almost done! Uploading gif.", "slacker -c " + GIF_CHANNEL + " -f /home/pi/rewind/output.gif")


def executeShellCommand(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]


def executePipedShellCommand(command1, command2):
    p1 = subprocess.Popen(command1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(command2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output, err = p2.communicate()


def removeLock():
    logToSlack("Removing lock file")
    try:
        os.remove(FILE_LOCK)
    except OSError:
        pass


if __name__ == '__main__':
    removeLock()
    logToSlack("Starting up")
    while True:
        getFramesLoop()
        makeGif()
        postGifToSlack()
        removeLock()
