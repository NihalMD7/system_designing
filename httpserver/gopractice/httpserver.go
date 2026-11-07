package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

var reasons = map[int]string{200: "OK", 201: "Created", 204: "No Content", 400: "Bad Request",
	404: "Not Found", 405: "Method Not Allowed", 413: "Payload Too Large", 500: "Internal Server Error"}

const (
	addr      = "127.0.0.1:8080"
	maxheader = 8192
	maxbody   = 1 << 20
	timeout   = 5 * time.Second
	maxconns  = 32
)

type httpError struct {
	status int
	msg    string
}

func (e *httpError) Error() string { return e.msg }

type request struct {
	method, path, version string
	header                map[string]string
	body                  []byte
}

var (
	mu       sync.RWMutex
	kv       = map[string][]byte{}
	requests atomic.Int64
)

func read_request(r *bufio.Reader) (*request, error) {
	line, err := r.ReadString('\n')
	if err != nil {
		return nil, err // io.EOF = client.closed
	}
	parts := strings.Split(strings.TrimRight(line, "\r\n"), " ")
	if len(parts) != 3 {
		return nil, &httpError{400, "bad request"}
	}
	req := &request{method: parts[0], path: parts[1], version: parts[2], header: map[string]string{}}
	size := len(line)
	for {
		h, err := r.ReadString('\n')
		if err != nil {
			return nil, err
		}
		size += len(h)
		if size > maxheader {
			return nil, &httpError{400, "bad request "}
		}
		h = strings.TrimRight(h, "\r\n")
		if h == "" {
			break
		}
		name, value, ok := strings.Cut(h, ":")
		if !ok {
			return nil, &httpError{400, "bad request "}
		}
		req.header[strings.ToLower(strings.TrimSpace(name))] = strings.TrimSpace(value)

	}
	if cl := req.header["content-length"]; cl != "" {
		n, err := strconv.Atoi(cl)
		if err != nil || n < 0 {
			return nil, &httpError{400, "bad request"}
		}
		if n > maxbody {
			return nil, &httpError{413, "too big body"}

		}
		req.body = make([]byte, n)
		if _, err := io.ReadFull(r, req.body); err != nil {
			return nil, err
		}
	}
	return req, err
}

func send(conn net.Conn, status int, body []byte, keep bool) error {
	c := "close"
	if keep {
		c = "keep-alive"
	}
	_, err := fmt.Fprintf(conn, "HTTP/1.1 %d %s\r\nContent-type:text/plain\r\nContent-length:%d\r\nConnection:%s\r\n\r\n%s",
		status, reasons[status], len(body), c, body)
	return err

}
func rout(req *request) (int, []byte) {
	switch {
	case req.path == "/":
		if req.method != "GET" {
			return 405, []byte("method not found ")
		}
		return 200, []byte("hello\n")
	case req.path == "/metrics" && req.method == "GET":
		return 200, []byte(fmt.Sprintf("requests: %d \n", requests.Load()))
	case strings.HasPrefix(req.path, "/kv/"):
		key := strings.TrimPrefix(req.path, "/kv/")
		if key == "" {
			return 400, []byte("missing key ")
		}
		switch req.method {
		case "GET":
			mu.Lock()
			v, ok := kv[key]
			mu.Unlock()
			if !ok {
				return 404, []byte("not found \n")
			}
			return 200, v
		case "PUT":
			mu.Lock()
			kv[key] = req.body
			mu.Unlock()
			return 201, []byte("stored\n")
		case "DELETE":
			mu.Lock()
			_, ok := kv[key]
			delete(kv, key)
			mu.Unlock()
			if !ok {
				return 404, []byte("not found\n")
			}
			return 200, []byte("deleted\n")
		}
		return 405, []byte("method not allowed\n")
	}
	return 404, []byte("not found\n")

}

func safeRout(req *request) (status int, body []byte) {
	defer func() {
		if p := recover(); p != nil {
			log.Printf("handler panic: %v", p)
			status, body = 500, []byte("internal error")

		}
	}()
	return rout(req)
}

func handle(conn net.Conn) {
	defer conn.Close()
	peer := conn.RemoteAddr().String()
	r := bufio.NewReader(conn)
	for {
		conn.SetDeadline(time.Now().Add(timeout))
		req, err := read_request(r)
		if err != nil {
			var he *httpError
			if errors.As(err, &he) {
				send(conn, he.status, []byte(he.msg+"\n"), false)
			} else if !errors.Is(err, io.EOF) {
				log.Printf("%s closed:%v", peer, err)
			}
			return
		}
		keep := req.version == "HTTP/1.1" && !strings.EqualFold(req.header["connection"], "close")
		start := time.Now()
		status, body := safeRout(req)
		if status == 500 {
			keep = false
		}
		requests.Add(1)
		if err := send(conn, status, body, keep); err != nil {
			return
		}
		log.Printf("%s %s %s %d %v", peer, req.method, req.path, status, time.Since(start))
		if !keep {
			return
		}
	}

}

func main() {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatal(err)

	}
	log.Printf("listening on %s ", addr)
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-stop
		log.Printf("shutting down")
		ln.Close()
	}()
	sem := make(chan struct{}, maxconns)
	var wg sync.WaitGroup
	for {
		conn, err := ln.Accept()
		if err != nil {
			if errors.Is(err, net.ErrClosed) {
				break
			}
			log.Print(err)
			continue
		}
		sem <- struct{}{}
		wg.Add(1)
		go func() {
			defer func() {
				<-sem
				wg.Done()
			}()
			handle(conn)

		}()
	}
	wg.Wait()
	log.Print("bye")

}
