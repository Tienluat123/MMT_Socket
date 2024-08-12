import socket
import threading
import os

PORT = 5050
SERVER = '127.0.0.1'
ADDR = (SERVER, PORT)
CHUNK_SIZE = 1024
LIST_FILE_PATH = "listFile.txt"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)


def sent_list_file(client_socket):
    try: 
        with open(LIST_FILE_PATH, 'r') as file:
            file_list = file.read()
        
        client_socket.sendall(file_list.encode())
        print("Send list file successfully")
        
    except Exception as e:
        print(f"Error: {e}")   


def handle_client(conn, addr):
    try:
        print(f"Kết nối từ {addr} đã được chấp nhận")
        # Gửi list file
        try:
            sent_list_file(conn)
        except Exception as e:
            print(f"Error: {e}")

        update_file = True
        
        while update_file:
            while True:
                # Nhận yêu cầu tệp từ client
                filename = conn.recv(1024).decode(errors='ignore').strip()
                if not filename:
                    break

                if filename == "DONE":
                    update_file = False
                    # Xử lý sau khi nhận tín hiệu DONE nếu cần
                    break

                # Kiểm tra tệp có tồn tại không
                if os.path.isfile(filename):
                    # Gửi kích thước tệp đến client
                    file_size = os.path.getsize(filename)
                    conn.sendall(str(file_size).encode())
                    
                else:
                    conn.sendall(b"0")  # Gửi kích thước 0 nếu tệp không tồn tại
                    continue

                # Xử lý việc gửi các khối dữ liệu khi nhận được yêu cầu từ client
            while True:
                try:
                    # Nhận yêu cầu gửi khối dữ liệu từ client
                    request = conn.recv(1024).decode(errors='ignore').strip()

                    if not request:
                        # Nếu không nhận được yêu cầu nào, tiếp tục chờ
                        continue
                    
                    if request == "NEW_FILES":
                        update_file = True
                        break
                    
                    # Tách thông tin start và filename từ thông điệp nhận được
                    start_str, filename = request.split(',')
                    start = int(start_str)

                    if os.path.isfile(filename):
                        with open(filename, 'rb') as f:
                            f.seek(start)
                            bytes_to_send = f.read(CHUNK_SIZE)
                            conn.sendall(bytes_to_send)
                    else:
                        conn.sendall(b'')  # Gửi EOF nếu tệp không tồn tại hoặc không còn dữ liệu

                except ConnectionResetError:
                    print("Kết nối bị đóng bởi client.")
                    break
                except Exception as e:
                    print(f"Lỗi trong xử lý yêu cầu từ client: {e}")
                    break

    except Exception as e:
        print(f"Lỗi trong xử lý client: {e}")
    finally:
        conn.close()


def start_server():
    server_socket.listen()
    print(f"Server đang lắng nghe trên {SERVER}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Số lượng kết nối đang hoạt động: {threading.active_count() - 1}")

# Chạy server
print("Server đang khởi động...")
start_server()
