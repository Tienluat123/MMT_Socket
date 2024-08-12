import socket
import sys
import queue
import signal
import threading
import time

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
        
        sys.stdout.write("\n")
        sys.stdout.flush()
        
        total_size_map = {}
        received_size_map = {}
        
        line = {}
        high = 5
        priority_map = {'CRITICAL': 10, 'HIGH': 4, 'NORMAL': 1}
        priority_files = {'CRITICAL': [], 'HIGH': [], 'NORMAL': []}

        while running:
            files_remaining = []

            while not file_queue.empty():
                
                filename, priority = file_queue.get()
                line[filename] = high  # Đặt dòng hiển thị cho file
                high += 1
                
                if filename not in downloaded_files:
                    client_socket.sendall(filename.encode())
                    total_size_str = client_socket.recv(1024).decode().strip()
                    
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
                    
                    # Phân loại các file vào từng nhóm độ ưu tiên
                    if priority == 'CRITICAL':
                        priority_files['CRITICAL'].append(filename)
                    elif priority == 'HIGH':
                        priority_files['HIGH'].append(filename)
                    else:
                        priority_files['NORMAL'].append(filename)
                    
                    files_remaining.append(filename)
                    
                file_queue.task_done()

            # Gửi tín hiệu cho server khi file_queue rỗng và không còn file nào để xử lý
            if file_queue.empty():
                client_socket.sendall(b"DONE")
                
            
            if running:
                last_update_time = time.time()
                need_to_update_files = False
                # Download chunks in round-robin fashion with priority
                while True:
                    
                    current_time = time.time()
                    
            # Cập nhật danh sách tệp mới mỗi 2 giây
                    if current_time - last_update_time >= 2:
                        last_update_time = current_time
                        new_files = read_file_list('input.txt')
                        for entry in new_files:
                            filename, priority = entry.split(' ')
                            if filename not in [f for f, _ in file_queue.queue] and \
                       filename not in sum(priority_files.values(), []):
                                file_queue.put((filename, priority))
                        # Đặt cờ cho vòng lặp tải xuống để dừng lại
                                need_to_update_files = True
                            else:
                                need_to_update_files = False
                        
                    if need_to_update_files == True:
                        client_socket.sendall(b"NEW_FILES")
                        break

                    all_files_downloaded = True
                    
                    for priority in ['CRITICAL', 'HIGH', 'NORMAL']:
                        if priority_files[priority]:  # Kiểm tra nếu còn tệp trong mức độ ưu tiên này
                            all_files_downloaded = False

                            for filename in priority_files[priority]:
                                start = received_size_map.get(filename, 0)
                                chunks_to_download = priority_map[priority]

                                for _ in range(chunks_to_download):
                                    if start < total_size_map.get(filename, 0):
                                        success = receive_chunk(client_socket, start, 'file_da_nhan_' + filename, filename, CHUNK_SIZE)
                                        if success:
                                            received_size_map[filename] += CHUNK_SIZE
                                            percent_complete = (received_size_map[filename] / total_size_map[filename]) * 100
                                            sys.stdout.write(f"\033[{line[filename]};0H")  # Di chuyển con trỏ đến dòng `line`
                                            sys.stdout.write(f"Tiến độ nhận file {filename}: {percent_complete:.1f}%")
                                            sys.stdout.flush()
                                        else:
                                            priority_files[priority].remove(filename)
                                            break
                                    else:
                                        priority_files[priority].remove(filename)
                                        downloaded_files.add(filename)
                                        sys.stdout.write(f"\033[{line[filename]};0H")  # Di chuyển con trỏ đến dòng `line`
                                        sys.stdout.write(f"Tiến độ nhận file {filename}: 100.0% - File đã được nhận thành công!\n")
                                        sys.stdout.flush()
                                        break
                    
                    if all_files_downloaded:
                        continue
                
                # Refill the queue if more files are in the input list
                # file_list = read_file_list('input.txt')
                # for file in file_list:
                #     if file not in downloaded_files and file not in files_remaining:
                #         file_queue.put(file)
        
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

for entry in file_list:
    filename, priority = entry.split(' ')
    file_queue.put((filename, priority))

thread = threading.Thread(target=client_task, args=(file_queue, downloaded_files))
thread.start()

thread.join()
