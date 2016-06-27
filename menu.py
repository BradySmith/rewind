from flask import Flask, redirect, render_template
import cv2
import subprocess

FILE_LOCK = "/home/pi/rewind/loop.lock"

app = Flask(__name__, static_url_path = "/home/pi/rewind/static", static_folder = "/home/pi/rewind/static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gif")
def takeGif():
    open(FILE_LOCK, 'w')
    return redirect("/", code=302)


def executePipedShellCommand(command1, command2):
    p1 = subprocess.Popen(command1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(command2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output, err = p2.communicate()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    # testImage()
