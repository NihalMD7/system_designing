import socket ,logging ,threading,time,signal    #know what is signal 
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass ,field

HOST,PORT="127.0.0.1",8080
MAXHEADER,MAXBODY,TIMEOUT,WORKERS=8192,1 << 20 ,5,32

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(threadName)s %(message)s") #learn how to log
log=logging.getLogger("http")

store ,store_lock={},threading.Lock()
stats,stats_lock={"requests":0},threading.Lock()

REASONS = {200: "OK", 201: "Created", 204: "No Content", 400: "Bad Request",
           404: "Not Found", 405: "Method Not Allowed", 413: "Payload Too Large",
           500: "Internal Server Error"}

class BadRequest(Exception):
    def __init__(self,status,msg):
        super().__init__(msg)
        self.status=status

@dataclass
class Request:
    method:str
    path:str
    version:str
    header:dict[str,str]=field(default_factory=dict)
    body:bytes=b""

def read_request(f)-> Request:
    line=f.readline(MAXHEADER)
    if not line:
        return None
    parts=line.decode("latin-1").rstrip("\r\n").split(" ")
    if len(parts)!= 3:
        raise BadRequest(400, "bad Request")
    method,path,version=parts
    header={}
    size=len(line)
    while True:
        h=f.readline(MAXHEADER)
        size+=len(h)
        if size>MAXHEADER:raise BadRequest(400,"bad request")
        if h in (b"\r\n",b"\n",b""): 
            break
        name , sep ,val =h.decode("latin-1").partition(":")
        if not sep:
            raise BadRequest(400,"wrong header")
        header[name.strip().lower()]=val.strip()
    try:
        n=int(header.get("content-length",0))
    except ValueError:
        raise BadRequest(400,"bad content-length")
    if n<0:raise BadRequest(400,"bad contentlength ")
    if n>MAXBODY:raise BadRequest(400,"bad contnt length")
    body=f.read(n)
    return Request(method,path,version,header,body)

def send(conn,status,body=b"",keep=False):
    if isinstance(body,str):
        body=body.encode()
    head=(f"HTTP/1.1 {status} {REASONS[status]}\r\n"
          f"Content-Length: {len(body)}\r\n"
          f"Content-type: text/plain\r\n"
          f"Connection: {'keep-alive' if keep else 'close'}\r\n\r\n")
    conn.sendall(head.encode()+body)


def rout(method,path,body):
    if path=="/":
        return (200 ,"hello\n")if method=='GET' else (405,"method not allowed")
    if path=="/metrics":
        with stats_lock:
            return 200 ,f"request {stats['requests']}\n"
    if path.startswith("/kv/"):
        key=path[4:]
        if not key:
            return 400,"missing key\n"
        if method=="GET":
            with store_lock:
                v=store.get(key)
            return (200,v) if v is not None else (404,"not found ")
        if method=="PUT":
            with store_lock:
                store[key]=body
            return 201,"stored\n"
        if method=="DELETE":
            with store_lock:
                exiest=store.pop(key,None) is not None
            return (204,b"") if exiest else (404, "not found ")
        return 405, 'method not found'
    return 404 ,"not found"



def handle(conn,addr):
    conn.settimeout(TIMEOUT)
    f=conn.makefile("rb")
    try:
        while True:
            try:
                req=read_request(f)
            except BadRequest as e:
                send(conn,e.status,f"{e}\n")
                break
            if req is None:
                break
            keep=req.version="HTTP/1.1" and req.header.get("connection","").lower()!="close"
            start=time.perf_counter()
            try:
                status,out=rout(req.method,req.path,req.body)
            except Exception:
                log.exception("handler crash ")
                status,out ,keep = 500 ,"internal error\n",False
            with stats_lock:
                stats["requests"]+=1
            send(conn,status,out,keep)
            log.info("%s %s %s %d %.1fms",addr[0],req.method,req.path,status,(time.perf_counter()-start)*1000)
            if not keep:
                break
    except (TimeoutError,ConnectionError) as e:
        log.info("%s closed: %s",addr[0],type(e).__name__)
    finally:
        f.close()
        conn.close()

def main():
    srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    srv.bind((HOST,PORT))
    srv.listen(128)
    srv.settimeout(1.0)
    stop=threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    log.info("listening on %s:%d", HOST, PORT)
    with ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="w") as pool:
        while not stop.is_set():
            try:
                conn, addr = srv.accept()
            except TimeoutError:
                continue
            pool.submit(handle, conn, addr)
        log.info("shutting down, waiting for workers")
    srv.close() 


if __name__=="__main__":
    main()
import socket ,logging ,threading,time,signal    #know what is signal 
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass ,field

HOST,PORT="127.0.0.1",8080
MAXHEADER,MAXBODY,TIMEOUT,WORKERS=8192,1 << 20 ,5,32

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(threadName)s %(message)s") #learn how to log
log=logging.getLogger("http")

store ,store_lock={},threading.Lock()
stats,stats_lock={"requests":0},threading.Lock()

REASONS = {200: "OK", 201: "Created", 204: "No Content", 400: "Bad Request",
           404: "Not Found", 405: "Method Not Allowed", 413: "Payload Too Large",
           500: "Internal Server Error"}

class BadRequest(Exception):
    def __init__(self,status,msg):
        super().__init__(msg)
        self.status=status

@dataclass
class Request:
    method:str
    path:str
    version:str
    header:dict[str,str]=field(default_factory=dict)
    body:bytes=b""

def read_request(f)-> Request:
    line=f.readline(MAXHEADER)
    if not line:
        return None
    parts=line.decode("latin-1").rstrip("\r\n").split(" ")
    if len(parts)!= 3:
        raise BadRequest(400, "bad Request")
    method,path,version=parts
    header={}
    size=len(line)
    while True:
        h=f.readline(MAXHEADER)
        size+=len(h)
        if size>MAXHEADER:raise BadRequest(400,"bad request")
        if h in (b"\r\n",b"\n",b""): 
            break
        name , sep ,val =h.decode("latin-1").partition(":")
        if not sep:
            raise BadRequest(400,"wrong header")
        header[name.strip().lower()]=val.strip()
    try:
        n=int(header.get("content-length",0))
    except ValueError:
        raise BadRequest(400,"bad content-length")
    if n<0:raise BadRequest(400,"bad contentlength ")
    if n>MAXBODY:raise BadRequest(400,"bad contnt length")
    body=f.read(n)
    return Request(method,path,version,header,body)

def send(conn,status,body=b"",keep=False):
    if isinstance(body,str):
        body=body.encode()
    head=(f"HTTP/1.1 {status} {REASONS[status]}\r\n"
          f"Content-Length: {len(body)}\r\n"
          f"Content-type: text/plain\r\n"
          f"Connection: {'keep-alive' if keep else 'close'}\r\n\r\n")
    conn.sendall(head.encode()+body)


def rout(method,path,body):
    if path=="/":
        return (200 ,"hello\n")if method=='GET' else (405,"method not allowed")
    if path=="/metrics":
        with stats_lock:
            return 200 ,f"request {stats['requests']}\n"
    if path.startswith("/kv/"):
        key=path[4:]
        if not key:
            return 400,"missing key\n"
        if method=="GET":
            with store_lock:
                v=store.get(key)
            return (200,v) if v is not None else (404,"not found ")
        if method=="PUT":
            with store_lock:
                store[key]=body
            return 201,"stored\n"
        if method=="DELETE":
            with store_lock:
                exiest=store.pop(key,None) is not None
            return (204,b"") if exiest else (404, "not found ")
        return 405, 'method not found'
    return 404 ,"not found"



def handle(conn,addr):
    conn.settimeout(TIMEOUT)
    f=conn.makefile("rb")
    try:
        while True:
            try:
                req=read_request(f)
            except BadRequest as e:
                send(conn,e.status,f"{e}\n")
                break
            if req is None:
                break
            keep=req.version="HTTP/1.1" and req.header.get("connection","").lower()!="close"
            start=time.perf_counter()
            try:
                status,out=rout(req.method,req.path,req.body)
            except Exception:
                log.exception("handler crash ")
                status,out ,keep = 500 ,"internal error\n",False
            with stats_lock:
                stats["requests"]+=1
            send(conn,status,out,keep)
            log.info("%s %s %s %d %.1fms",addr[0],req.method,req.path,status,(time.perf_counter()-start)*1000)
            if not keep:
                break
    except (TimeoutError,ConnectionError) as e:
        log.info("%s closed: %s",addr[0],type(e).__name__)
    finally:
        f.close()
        conn.close()

def main():
    srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    srv.bind((HOST,PORT))
    srv.listen(128)
    srv.settimeout(1.0)
    stop=threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    log.info("listening on %s:%d", HOST, PORT)
    with ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="w") as pool:
        while not stop.is_set():
            try:
                conn, addr = srv.accept()
            except TimeoutError:
                continue
            pool.submit(handle, conn, addr)
        log.info("shutting down, waiting for workers")
    srv.close() 


if __name__=="__main__":
    main()




