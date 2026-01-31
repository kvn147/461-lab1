import socket
import struct

HOST = "127.0.0.1"
PORT = 50008
HEADER_FORMAT = "!IIHH"


def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((HOST, PORT))

    header = struct.pack(HEADER_FORMAT, 12, 42, 1, 123)
    payload = b"hello world\0"
    frame = header + payload

    address = (HOST, 50007)
    client_socket.sendto(frame, address)

    message, _ = client_socket.recvfrom(1024)
    print(message.decode())


if __name__ == "__main__":
    run_client()
