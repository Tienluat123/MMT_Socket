import socket
import sys
import queue
import signal
import threading

PORT = 5050
SERVER = '127.0.0.1'
ADDR = (SERVER, PORT)
CHUNK_SIZE = 1024
running = True

def receive_chunk(conn, start, downloaded_file, filename, chunk_size):
    try:
        message = f"{start},{filename}"
        conn.sendall(message.encode())

        bytes_read = b''
        while len(bytes_read) < chunk_size:
            chunk = conn.recv(chunk_size - len(bytes_read))
            if not chunk:
                break
            bytes_read += chunk
        
        if not bytes_read:
            return False  # EOF
        
        with open(downloaded_file, 'ab') as f:
            f.write(bytes_read)
            
        return True
    except Exception as e:
        print(f"Lỗi khi nhận chunk của file {downloaded_file}: {e}")
        return False

def client_task(file_queue, downloaded_files):
    global running
    client_socket = None
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        
        file_list_server = client_socket.recv(2048).decode(errors='ignore')
        print(file_list_server)
        
        total_size_map = {}
        received_size_map = {}
        
        line = {}
        priority = 1

        while running:
            files_remaining = []


            while not file_queue.empty():
                filename = file_queue.get()
                line[filename] = priority  # Đặt dòng hiển thị cho file
                priority += 1
                
                if filename not in downloaded_files:
                    client_socket.sendall(filename.encode())
                    total_size_str = client_socket.recv(1024).decode().strip()
                    print(f"Received size for {filename}: '{total_size_str}'")
                    
                    try:
                        total_size = int(total_size_str)
                    except ValueError:
                        print(f"Lỗi khi nhận kích thước file {filename} từ server. Giá trị nhận được: {total_size_str}")
                        continue

                    total_size_map[filename] = total_size
                    received_size_map[filename] = 0
                    
                    if total_size == 0:
                        print(f"File {filename} không tồn tại trên server.")
                        continue
                    
                    files_remaining.append(filename)
                    
                file_queue.task_done()
            
            # Gửi tín hiệu cho server khi file_queue rỗng và không còn file nào để xử lý
            if file_queue.empty():
                client_socket.sendall(b"DONE")
                print("Đã gửi tín hiệu DONE cho server.")
            
            if running:
                # Download chunks in round-robin fashion
                while files_remaining:
                    for filename in files_remaining[:]:
                        start = received_size_map.get(filename, 0)
                        if start < total_size_map.get(filename, 0):
                            success = receive_chunk(client_socket, start, 'file_da_nhan_' + filename, filename, CHUNK_SIZE)
                            if success:
                                received_size_map[filename] += CHUNK_SIZE
                                percent_complete = (received_size_map[filename] / total_size_map[filename]) * 100
                                sys.stdout.write(f"\033[{line[filename]};0H")  # Di chuyển con trỏ đến dòng line
                                sys.stdout.write(f"Tiến độ nhận file {filename}: {percent_complete:.1f}%")
                                sys.stdout.flush()
                            else:
                                files_remaining.remove(filename)
                        else:
                            files_remaining.remove(filename)
                            downloaded_files.add(filename)
                            sys.stdout.write(f"\033[{line[filename]};0H")  # Di chuyển con trỏ đến dòng line
                            sys.stdout.write(f"Tiến độ nhận file {filename}: 100.0% - File đã được nhận thành công!\n")
                            sys.stdout.flush()
                    
                    if not files_remaining:
                        break
                
                # Refill the queue if more files are in the input list
                file_list = read_file_list('input.txt')
                for file in file_list:
                    if file not in downloaded_files and file not in files_remaining:
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

signal.signal(signal.SIGINT, signal_handler)

file_list = read_file_list('input.txt')

file_queue = queue.Queue()
downloaded_files = set()

for file in file_list:
    file_queue.put(file)

thread = threading.Thread(target=client_task, args=(file_queue, downloaded_files))
thread.start()

thread.join()
