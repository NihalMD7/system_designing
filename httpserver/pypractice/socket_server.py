import socket 
import sys

def simple_server():
    ser=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ser.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    ser.bind(("127.0.0.1",8000))
    ser.listen()
    print("listening 8000")

    while True:
        conn,adde = ser.accept()
        conn.recv(4096)
        body=b"hello"
        head=(
            b" HTTP/1.1 200 OK\r\n"
            b" Content-Length: %d \r\n"
            b"Connections : close \r\n"
            b"\r\n")%len(body)
        conn.sendall(head+body)
        conn.close()

command= {"simple_server": simple_server}
if __name__ == "__main__":
    if len(sys.argv)<2 or sys.argv[1] not in command:
        print(f"usage: {sys.argv[0]} {{{'|'.join(command)}}}", file=sys.stderr)
        sys.exit(2)
    try:
        command[sys.argv[1]](*sys.argv[2:])
    except KeyboardInterrupt:
        print("\nshutdown")


