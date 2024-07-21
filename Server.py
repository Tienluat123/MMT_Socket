import socket
import threading
import os

#socket.gethostname()  # get the name of the host
#socket.gethostbyname(socket.gethostname())  # get the ip address of the host


# Khởi tạo
HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
LIST_FILE_PATH = "listFile.txt"

socket.AF_INET  # ipv4
socket.AF_INET6  # ipv6

socket.SOCK_STREAM
socket.SOCK_DGRAM


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR) #binds the socket to a specific address

# Đọc danh sách file từ file_list
def sent_list_file(conn):
    try: 
        with open(LIST_FILE_PATH, 'r') as file:
            file_list = file.read()
        
        conn.sendall(file_list.encode(FORMAT))
        print("Send list file successfully")
        
    except Exception as e:
        print(f"Error: {e}")    

# Các chức năng xử lí với Client:
# TODO: Gửi thông danh sách đến client [Hoàn thành]
# TODO: Thực hiện gửi file cần download cho client [Hoàn thành]

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected") 
    
    # Gửi danh sách File cho Client
    try:
        sent_list_file(conn)
    except Exception as e:
        print(f"Error: {e}")
    
    # Gửi file client yêu cầu
    while True:
        file_name = conn.recv(HEADER).decode(FORMAT)
        if file_name == DISCONNECT_MESSAGE:
            print(f"[DISCONNECT] {addr}")
            break
        
        if os.path.exists(file_name):
            # Lấy độ lớn file -> Tiến độ tải
            file_size = os.path.getsize(file_name)
            conn.send(f"{file_size}".encode(FORMAT))
            
            # Đọc và gửi file đến Client
            with open(file_name, 'rb') as file:
                file_data = file.read(1024) 
                while file_data: # Vì file có thể lớn nó sẽ không đọc hết file
                    conn.sendall(file_data)
                    file_data = file.read(1024)
                    
            conn.send(b'EOF')
        else:
            print(f"File {file_name} not found")
            conn.send(b'ERROR')
                

    conn.close()
    
    
def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target = handle_client, args = (conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}") # Number of thread
        
        

print("[STARTING] server is starting..")
start()


