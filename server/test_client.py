import socket
import struct

HOST = "127.0.0.1"
PORT = 50008
HEADER_FORMAT = "!IIHH"


def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.bind((HOST, PORT))

        payload = b"hello world\0"
        header = struct.pack(HEADER_FORMAT, len(payload), 0, 8, 100)

        client_socket.sendto(header + payload, ("127.0.0.1", 50007))

        message, _ = client_socket.recvfrom(1024)

        print(message)


if __name__ == "__main__":
    run_client()
