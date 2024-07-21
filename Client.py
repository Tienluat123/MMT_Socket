import socket
import time
import os
import signal
import sys

# Khởi tạo
HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = '127.0.0.1' # Nhập địa chỉ client vào đây
ADDR = (SERVER, PORT)
FILE_PATH = 'input.txt' # File để chạy liên tục
FILE_PATH_DOWNLOAD = 'Download_MMT'
CHECK_INTERVAL = 20



socket.AF_INET  # ipv4
socket.AF_INET6  # ipv6
socket.AF_INET6

socket.SOCK_STREAM
socket.SOCK_DGRAM


# TODO: Nhận file có thể tải từ server [Hoàn Thành]
# TODO: Đọc danh sách liên kết liên tục sau 20 giây và cập nhật (Không bao gồm các file đã tải) [Hoàn Thành]
# TODO: Tiến hành tải các File đó từ file Input() [Hoàn Thành]
# TODO: Chạy tiến trình tải [Hoàn thành]

   
# Đọc danh sách File cần tải và gửi đến Server  
def read_file_list(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def send_file_list(client, file_list):
    client.sendall(file_list.encode(FORMAT))


# Đọc lại sau mỗi giây        
def signal_handler(sig, frame):
    print("\nClient is shutting down...")
    sys.exit(0)

# Tích hợp vừa tải vừa chạy tiến trình
def download_file(client, file_name):
    client.sendall(file_name.encode(FORMAT))
    
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(FILE_PATH_DOWNLOAD):
        os.makedirs(FILE_PATH_DOWNLOAD)
        
    file_path = os.path.join(FILE_PATH_DOWNLOAD, file_name)
    
    file_size_str = client.recv(1024).decode(FORMAT)
    file_size = int(file_size_str)
    
    with open(file_path, 'wb') as file:
        received = 0
        while True:
            data = client.recv(1024)
            if data.endswith(b'EOF'):
                data = data[:-3]  # Remove 'EOF' marker
                file.write(data)
                received += len(data)
                break
            file.write(data)
            received += len(data)
            progress = (received / file_size) * 100
            
            # Chạy tiến trình tải
            print(f"Downloading {file_path}: {progress:.2f}% complete")
    
    print(f"Downloaded {file_name} to {file_path}")


def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    previous_file_list = set()
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(ADDR)
        
        file_list_server = client.recv(2048).decode(FORMAT)
        print(file_list_server)
        
        while True:
            try:
                file_list_client = set(read_file_list(FILE_PATH))
                
                if file_list_client != previous_file_list:
                    new_file = file_list_client - previous_file_list
                    
                    list_new_file = list(new_file)
                    for file in list_new_file:
                        download_file(client, file)
                    print("File list updated and sent to server.")
                
                previous_file_list = file_list_client
                
                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                print(f"An error occurred: {e}")

    finally:
        client.close()
        print("Client socket closed.")
            

    
if __name__ == "__main__":
    main()
    


