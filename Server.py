import socket
import threading
import os


PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
LIST_FILE_PATH = "listFile.txt"

def sent_list_file(client_socket):
    try: 
        with open(LIST_FILE_PATH, 'r') as file:
            file_list = file.read()
        
        client_socket.sendall(file_list.encode())
        print("Send list file successfully")
        
    except Exception as e:
        print(f"Error: {e}")   

 

def send_file(filename, conn):
    try:
        if not os.path.isfile(filename):
            conn.sendall(b"0")
            print(f"File {filename} không tồn tại")
            return
        
        total_size = os.path.getsize(filename)
        conn.sendall(str(total_size).encode())  # Gửi tổng kích thước file
        
        # Đợi xác nhận từ client
        ack = conn.recv(1024).decode()
        if ack != 'OK':
            print(f"Client không nhận được kích thước file của {filename}")
            return
        
        sent_size = 0
        with open(filename, 'rb') as f:
            while True:
                bytes_read = f.read(1024)
                if not bytes_read:
                    break
                conn.sendall(bytes_read)
                sent_size += len(bytes_read)
                print(f"\rTiến độ gửi file {filename}: {(sent_size / total_size) * 100:.1f}%", end="")
        
        print(f" - File {filename} đã được gửi thành công!")
    except Exception as e:
        print(f"Lỗi khi gửi file {filename}: {e}")
        conn.sendall(b"ERROR")

def handle_client(client_socket, addr):
    try:
        print(f"Đã kết nối từ {addr}")
        
        #Gửi list file
        try:
            sent_list_file(client_socket)
        except Exception as e:
            print(f"Error: {e}")
        
        while True:
            # Nhận tên file từ client
            filename = client_socket.recv(1024).decode().strip()
            if not filename:
                print(f"Client từ {addr} đã ngắt kết nối")
                break
            
            send_file(filename, client_socket)
        
    except Exception as e:
        print(f"Lỗi khi xử lý kết nối từ {addr}: {e}")
    
    finally:
        # Đóng kết nối với client
        client_socket.close()
        print(f"Đã đóng kết nối với client từ {addr}")

# Khởi tạo socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lắng nghe các kết nối tới cổng 12345
server_socket.bind(ADDR)
server_socket.listen(5)

print("Server đang lắng nghe tại cổng 12345...")

while True:
    try:
        # Chấp nhận kết nối từ client
        client_socket, addr = server_socket.accept()
        
        # Tạo một thread mới để xử lý client này
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()
        
    except Exception as e:
        print(f"Lỗi khi xử lý kết nối từ client: {e}")


