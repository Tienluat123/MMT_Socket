import socket
import threading


HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = '127.0.0.1' # Nhập địa chỉ client vào đây
ADDR = (SERVER, PORT)
FILE_PATH = 'input.txt' # File để chạy liên tục
FILE_PATH_DOWNLOAD = 'Download_MMT'

socket.AF_INET  # ipv4
socket.AF_INET6  # ipv6
socket.AF_INET6

socket.SOCK_STREAM
socket.SOCK_DGRAM

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(ADDR)

#Tải file [OKE]
def receive_file(filename, conn):
    try:
        total_size = int(conn.recv(1024).decode())  # Nhận tổng kích thước file từ server
        print(total_size)
        received_size = 0

        with open(filename, 'wb') as f:
            while True:
                bytes_read = conn.recv(1024)
                if not bytes_read:
                    break
                f.write(bytes_read)
                received_size += len(bytes_read)
                print(f"\rTiến độ nhận file: {(received_size / total_size) * 100:.1f}%", end="")
                
        print(f" File {filename} đã được nhận thành công!")
    except Exception as e:
        print(f"Lỗi khi nhận file: {e}")
        
        

def client_task(filename):
    client_socket.sendall(filename.encode())
        # Nhận file từ server
    receive_file('file_da_nhan_' + filename, client_socket)
    

# Danh sách các tên file mà các client sẽ yêu cầu
file_list = ['100MB.zip', '20MB.zip', '50MB.zip']

def main():
    try:
        for file in file_list:
            client_task(file)
        client_socket.close()
    except Exception as e:
        print(f"Lỗi khi nhận file: {e}")
    


