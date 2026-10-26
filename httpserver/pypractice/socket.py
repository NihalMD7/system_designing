import socket 

def simple_server():
    ser=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ser.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    ser.bind("127.0.0.1",8000)
    ser.listen()
    print("listening 8000")

    while True:
        conn,adde=