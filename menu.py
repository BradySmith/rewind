from flask import Flask, redirect
import cv2
import subprocess

FILE_LOCK = "loop.lock"

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello World!"


@app.route("/gif")
def takeGif():
    open(FILE_LOCK, 'w')
    return redirect("/", code=302)


@app.route("/test")
def testImage():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cv2.imwrite("test.jpg", frame)

    executePipedShellCommand("echo 'Uploading test image. Please hold.'", "slacker -c smashcam -f test.jpg")

    return redirect("/", code=302)

def executePipedShellCommand(command1, command2):
    p1 = subprocess.Popen(command1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(command2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output, err = p2.communicate()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    testImage()