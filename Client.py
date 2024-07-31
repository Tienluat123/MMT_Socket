import socket
import sys
import queue
import signal
import threading

# Để giữ trạng thái của chương trình khi nhận tín hiệu Ctrl+C
PORT = 5050
SERVER = '127.0.0.1' # Nhập địa chỉ client vào đây
ADDR = (SERVER, PORT)


running = True

def receive_file(conn, filename):
    try:
        total_size = int(conn.recv(1024).decode().strip())
        if total_size == 0:
            print(f"File {filename} không tồn tại trên server.")
            return
        
        conn.sendall(b'OK')

        received_size = 0
        with open(filename, 'wb') as f:
            while received_size < total_size:
                bytes_read = conn.recv(1024)
                if not bytes_read:
                    break
                f.write(bytes_read)
                received_size += len(bytes_read)
                
                percent_complete = (received_size / total_size) * 100
                sys.stdout.write(f"\rTiến độ nhận file {filename}: {percent_complete:.1f}%")
                sys.stdout.flush()
        
        sys.stdout.write(f"\rTiến độ nhận file {filename}: 100.0%")
        sys.stdout.flush()
        print(f" - File {filename} đã được nhận thành công!")
    except Exception as e:
        print(f"Lỗi khi nhận file {filename}: {e}")

def client_task(file_queue, downloaded_files):
    global running
    client_socket = None
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        
        file_list_server = client_socket.recv(2048).decode()
        print(file_list_server)
        
        while running:
            while not file_queue.empty():
                filename = file_queue.get()
                if filename not in downloaded_files:
                    client_socket.sendall(filename.encode())
                    receive_file(client_socket, 'file_da_nhan_' + filename)
                    downloaded_files.add(filename)
                file_queue.task_done()
            
            if running:
                file_list = read_file_list('input.txt')
                for file in file_list:
                    if file not in downloaded_files:
                        file_queue.put(file)
        
        client_socket.close()
    except Exception as e:
        print(f"Lỗi khi client xử lý các file: {e}")
    finally:
        if client_socket:
            client_socket.close()

def read_file_list(file_path):
    file_list = []
    try:
        with open(file_path, 'r') as file:
            file_list = file.read().splitlines()
    except Exception as e:
        print(f"Lỗi khi đọc danh sách file từ {file_path}: {e}")
    return file_list

def signal_handler(sig, frame):
    global running
    print("\nĐang ngắt kết nối...")
    running = False

# Đăng ký xử lý tín hiệu Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Đọc danh sách các tên file từ input.txt
file_list = read_file_list('input.txt')

# Tạo hàng đợi và thêm các file vào hàng đợi
file_queue = queue.Queue()
downloaded_files = set()

for file in file_list:
    file_queue.put(file)

# Tạo luồng để xử lý các file theo tuần tự
thread = threading.Thread(target=client_task, args=(file_queue, downloaded_files))
thread.start()

# Đợi luồng kết thúc
thread.join()
print("Đã ngắt kết nối.")

