from flask import Flask, redirect

FILE_LOCK = "loop.lock"

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello World!"


@app.route("/gif")
def takeGif():
    open(FILE_LOCK, 'w')
    return redirect("/", code=302)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
