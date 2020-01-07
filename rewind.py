import cv2
import subprocess
import os
import os.path
from PIL import Image
from shutil import copyfile


# With the current load ~18 frames a second.
FRAMES_TO_KEEP_BEFORE = 150
FRAMES_TO_KEEP_AFTER = 150
LOG_CHANNEL = "bot-log"
GIF_CHANNEL = "test-public"

FRAME_LOOP = True
FILE_LOCK = "/home/pi/rewind/loop.lock"
PREVIEW_FILE = "/home/pi/rewind/static/preview.jpg"
TEMP_PREVIEW_FILE = "/home/pi/rewind/static/tmp.jpg"


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

        if index % 500 == 0:
            makePreview(name)

        # Reset index when the number gets too big.
        if index == 100000000:
            index = 0

        if os.path.isfile(FILE_LOCK):
            FRAME_LOOP = False

    # Take a few more frames.
    broadcastToSlack("MP4 requested, building now - please hold.")
    for i in range(index, index + FRAMES_TO_KEEP_AFTER):
        getFrame(i, cap)


def getFrame(index, cap):
    ret, frame = cap.read()
    name = "/home/pi/rewind/frames/frame%d.jpg" % index
    cv2.imwrite(name, frame)
    return name


def makePreview(name):
    copyfile(name, TEMP_PREVIEW_FILE)

    # wrap in try catch
    image = Image.open(TEMP_PREVIEW_FILE)
    image = image.rotate(180)
    image.save(PREVIEW_FILE)


def logToSlack(message):
    sendToSlack(message, LOG_CHANNEL)


def broadcastToSlack(message):
    sendToSlack(message, GIF_CHANNEL)


def sendToSlack(message, channel):
    executePipedShellCommand("echo " + message, "slacker -c " + channel)

def makeMP4():
    try:
        os.remove("/home/pi/rewind/output.mp4")
    except OSError:
        pass

    try:
        command = "/usr/local/bin/ffmpeg -framerate 18 -pattern_type glob -i '/home/pi/rewind/frames/*.jpg' -c:v libx264 -r 30 -pix_fmt yuv420p -vf 'transpose=2,transpose=2' /home/pi/rewind/output.mp4"
        output,error  = subprocess.Popen(
                                    command, universal_newlines=True, shell=True,
                                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print(error)
        logToSlack("Finished making MP4")
        return True

    except KeyboardInterrupt:
        print "Interrupt detected. Exiting"
        return False

def postFileToSlack():
    executePipedShellCommand("echo Almost done! Uploading MP4.", "slacker -c " + GIF_CHANNEL + " -f /home/pi/rewind/output.mp4")

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
        makeMP4()
        postFileToSlack()
        removeLock()
