import socket
import threading
import os


# Khởi tạo
HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
LIST_FILE_PATH = "listFile.txt"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)

def send_file(filename, conn):
    try:
        total_size = os.path.getsize(filename)
        conn.sendall(str(total_size).encode())  # Gửi tổng kích thước file
        
              
        #Tải file [OK]
        with open(filename, 'rb') as f:
            while True:
                bytes_read = f.read(1024)
                if not bytes_read:
                    break
                conn.sendall(bytes_read)
                
        print("File đã được gửi thành công!")
    except Exception as e:
        print(f"Lỗi khi gửi file: {e}")
        conn.sendall(b"ERROR")

def handle_client(client_socket, addr):
    try:
        print(f"[NEW CONNECTION] {addr} connected") 
        
        # Nhận tên file từ client
        while True:
            filename = client_socket.recv(1024).decode()
            if not filename: 
                break
            send_file(filename, client_socket)
            
        
    except Exception as e:
        print(f"Lỗi khi xử lý kết nối từ {addr}: {e}")
    
    finally:
        # Đóng kết nối với client
        client_socket.close()
       
        
def start():
    server_socket.listen(5)
    print(f"[LISTENING] Server is listening on {SERVER}")
    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target = handle_client, args = (conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}") # Number of thread
            
    except Exception as e:
        print(f"Lỗi khi xử lý kết nối từ {addr}: {e}")



