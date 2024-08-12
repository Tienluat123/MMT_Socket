import socket
import os
import concurrent.futures
import threading
import time
import sys

class DownloadProgress:
    def __init__(self):
        self.progress_dict = {}
        self.total_chunks_dict = {}
        self.lock = threading.Lock()

    def update_progress(self, filename, downloaded_chunks):
        with self.lock:
            self.progress_dict[filename] = downloaded_chunks

    def set_total_chunks(self, filename, total_chunks):
        with self.lock:
            self.total_chunks_dict[filename] = total_chunks
            if filename not in self.progress_dict:
                self.progress_dict[filename] = 0

    def get_progress(self, filename):
        with self.lock:
            total_chunks = self.total_chunks_dict.get(filename, 1)
            downloaded_chunks = self.progress_dict.get(filename, 0)
            return (downloaded_chunks / total_chunks) * 100

    def all_done(self):
        with self.lock:
            return all(self.progress_dict.get(filename, 0) >= self.total_chunks_dict.get(filename, 0)
                       for filename in self.total_chunks_dict)

def receive_chunk(sock, filename, chunk_index, chunk_size=1024):
    try:
        with open(filename, 'r+b') as f:
            f.seek(chunk_index * chunk_size)
            chunk = sock.recv(chunk_size)
            f.write(chunk)
    except Exception as e:
        print(f"Error receiving chunk {chunk_index} for file {filename}: {e}")

def request_chunk(server_address, filename, chunk_index, chunk_size=1024, progress: DownloadProgress = None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(server_address)
            request = f"{filename} {chunk_index} {chunk_size}".encode()
            s.sendall(request)

            response = s.recv(1024)
            if response == b'OK':
                receive_chunk(s, f'downloaded_{filename}', chunk_index, chunk_size)
                if progress:
                    progress.update_progress(filename, progress.progress_dict[filename] + 1)
            else:
                print(response.decode())
    except Exception as e:
        print(f"Error requesting chunk {chunk_index} for file {filename}: {e}")

def print_progress(progress: DownloadProgress):
    while not progress.all_done():
        sys.stdout.write("\033[H\033[J")  # Clear screen
        sys.stdout.write("Download Progress:\n")
        for filename in progress.total_chunks_dict:
            progress_percentage = progress.get_progress(filename)
            sys.stdout.write(f"{filename}: {progress_percentage:.2f}%\n")
        sys.stdout.flush()
        time.sleep(1)

def download_file(server_address, filename, file_size, chunk_size=1024, max_workers=5, progress: DownloadProgress = None):
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    progress.set_total_chunks(filename, total_chunks)
    output_file = f'downloaded_{filename}'

    try:
        with open(output_file, 'wb') as f:
            f.truncate(file_size)
    except Exception as e:
        print(f"Error preparing file {output_file}: {e}")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(request_chunk, server_address, filename, chunk_index, chunk_size, progress)
                   for chunk_index in range(total_chunks)]
        
        for future in concurrent.futures.as_completed(futures):
            future.result()

if __name__ == '__main__':
    server_address = ('127.0.0.1', 65432)
    files_info = [('20MB.zip', 20 * 1024 * 1024), ('10MB.zip', 10 * 1024 * 1024)]
    
    progress = DownloadProgress()
    
    # Start progress printing in a separate thread
    progress_thread = threading.Thread(target=print_progress, args=(progress,), daemon=True)
    progress_thread.start()

    # Start downloading files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_file, server_address, filename, file_size, 1024, 5, progress)
                   for filename, file_size in files_info]
        
        for future in concurrent.futures.as_completed(futures):
            future.result()

    # Wait for the progress thread to complete
    progress_thread.join()
