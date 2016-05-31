package main

import (
	"fmt"
	"github.com/blackjack/webcam"
	"os"
	"reflect"
	"sort"
	"strconv"
	"os/exec"
	"bytes"
	"io"
	"net/http"
	"log"
	"sync"
)

var (
	frameLoopMutex = &sync.Mutex{}
)

type FrameSizes []webcam.FrameSize

//const FRAMES_TO_KEEP_BEFORE = 50
const FRAMES_TO_KEEP_BEFORE = 20
const FRAMES_TO_KEEP_AFTER = 20

func (slice FrameSizes) Len() int {
	return len(slice)
}

func (slice FrameSizes) Less(i, j int) bool {
	ls := slice[i].MaxWidth * slice[i].MaxHeight
	rs := slice[j].MaxWidth * slice[j].MaxHeight
	return ls < rs
}

func (slice FrameSizes) Swap(i, j int) {
	slice[i], slice[j] = slice[j], slice[i]
}

func AddHuffmanTable(filename string) {
	cmd := exec.Command("/usr/bin/python", "/home/pi/rewind/mjpeg.py", filename)
	cmd.Run()
}

func MakeGif() {
	cmd := exec.Command("/usr/bin/convert", "-delay", "15x100", "/home/pi/rewind/frames/frame*.jpg", "-loop", "0", "/home/pi/rewind/output.gif")
	cmd.Run()
}

func UploadToSlack() {
	c1 := exec.Command("echo 'Uploading gif. Please hold.'")
	c2 := exec.Command("/usr/local/bin/slacker", "-c", "intersection-gifs", "-f", "/home/pi/rewind/output.gif")

	r, w := io.Pipe()
	c1.Stdout = w
	c2.Stdin = r

	var b2 bytes.Buffer
	c2.Stdout = &b2

	c1.Start()
	c2.Start()
	c1.Wait()
	w.Close()
	c2.Wait()
	io.Copy(os.Stdout, &b2)
}

func CaptureLoop() {
	cam, err := webcam.Open("/dev/video0")
	if err != nil {
		panic(err.Error())
	}
	defer cam.Close()

	format_desc := cam.GetSupportedFormats()
	var formats []webcam.PixelFormat
	for f := range format_desc {
		formats = append(formats, f)
	}

	// Get Motion-JPEG if it exists.
	var formatIndex = -1;
	for i, value := range formats {
		if (format_desc[value] == "Motion-JPEG") {
			formatIndex = i
		}
	}
	format := formats[formatIndex]
	frames := FrameSizes(cam.GetSupportedFrameSizes(format))
	sort.Sort(frames)
	size := frames[0]

	f, w, h, err := cam.SetImageFormat(format, uint32(size.MaxWidth), uint32(size.MaxHeight))

	if err != nil {
		panic(err.Error())
	} else {
		fmt.Fprintf(os.Stderr, "Resulting image format: %s (%dx%d)\n", format_desc[f], w, h)
	}

	err = cam.StartStreaming()
	if err != nil {
		panic(err.Error())
	}

	timeout := uint32(5) //5 seconds

	var i = 0
	for {
		err = cam.WaitForFrame(timeout)

		switch err.(type) {
		case nil:
		case *webcam.Timeout:
			fmt.Fprint(os.Stderr, err.Error())
			continue
		default:
			panic(err.Error())
		}

		frame, err := cam.ReadFrame()
		if len(frame) != 0 {
			frameLoopMutex.Lock()

			var newFileName = "/home/pi/rewind/frames/frame" + strconv.Itoa(i) + ".jpg"
			var fileNameToRemove = "/home/pi/rewind/frames/frame" + strconv.Itoa(i - FRAMES_TO_KEEP_BEFORE) + ".jpg"

			fmt.Println(reflect.TypeOf(frame))
			fo, err := os.Create(newFileName)
			if err != nil {
				panic(err)
			}

			if _, err := fo.Write(frame); err != nil {
				panic(err)
			}

			defer func() {
				if err := fo.Close(); err != nil {
					panic(err)
				}
			}()

			os.Remove(fileNameToRemove)
			frameLoopMutex.Unlock()

			AddHuffmanTable(newFileName)
			i++

			// Reset number when it gets too big.
			if i > 100000000 {
				i = 0
			}

		} else if err != nil {
			panic(err.Error())
		}
	}
}

func interruptHandler(w http.ResponseWriter, r *http.Request) {
	frameLoopMutex.Lock()
	MakeGif()
	UploadToSlack()
	frameLoopMutex.Unlock()

	http.Redirect(w, r, "/", 301)
}

func main() {
	// Start taking frames.
	go CaptureLoop()

	http.HandleFunc("/gif/", interruptHandler)
	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		log.Fatal("ListenAndServe:", err)
	}
}
