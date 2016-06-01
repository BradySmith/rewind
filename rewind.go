package main

import (
	"fmt"
	"github.com/blackjack/webcam"
	"os"
	"sort"
	"strconv"
	"os/exec"
	"bytes"
	"io"
	"net/http"
	"log"
	"sync"
	"path/filepath"
	"time"
)

var (
	frameLoopMutex = &sync.Mutex{}
)

type FrameSizes []webcam.FrameSize

const FRAMES_TO_KEEP = 100
const ROTATE_IMAGE = false

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

func timeTrack(start time.Time, name string) {
	elapsed := time.Since(start)
	var message = name + " took " + elapsed.String()
	log.Printf("%s", message)
	SendToSlack(message)
}

func AddHuffmanTable(filename string) {
	cmd := exec.Command("/usr/bin/python", "/home/pi/rewind/mjpeg.py", filename)
	cmd.Run()
}

func MakeGif() {
	defer timeTrack(time.Now(), "makeGif")
	cmd := exec.Command("/usr/bin/convert", "-delay", "15x100", "-layers", "optimize", "/home/pi/rewind/frames/frame*.jpg", "-loop", "0", "/home/pi/rewind/output.gif")
	cmd.Run()
}

func SendToSlack(message string) {
	c1 := exec.Command("/bin/echo", message)
	c2 := exec.Command("/usr/local/bin/slacker", "-c", "bot-log")

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

func UploadToSlack() {
	defer timeTrack(time.Now(), "uploadToSlack")
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

func RemoveAllFrames() error {
	var dir = "/home/pi/rewind/frames/"
	d, err := os.Open(dir)
	if err != nil {
		return err
	}
	defer d.Close()
	names, err := d.Readdirnames(-1)
	if err != nil {
		return err
	}
	for _, name := range names {
		err = os.RemoveAll(filepath.Join(dir, name))
		if err != nil {
			return err
		}
	}

	return nil
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
	for i, value := range frames {
		fmt.Fprintf(os.Stderr, "[%d] %s\n", i+1, value.GetString())
	}
	size := frames[4]

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
			var fileNameToRemove = "/home/pi/rewind/frames/frame" + strconv.Itoa(i - FRAMES_TO_KEEP) + ".jpg"

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
	time.Sleep(time.Second * 3)

	fmt.Println("/gif")
	frameLoopMutex.Lock()
	MakeGif()
	UploadToSlack()
	RemoveAllFrames()
	frameLoopMutex.Unlock()

	http.Redirect(w, r, "/", 200)
}

func main() {
	SendToSlack("Starting Up.")
	RemoveAllFrames()

	// Start taking frames.
	go CaptureLoop()

	http.HandleFunc("/gif/", interruptHandler)
	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		log.Fatal("ListenAndServe:", err)
	}
}
