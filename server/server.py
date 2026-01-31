import socket
import struct

HOST = "127.0.0.1"
PORT = 50007
MESSAGE_SIZE = 1024
HEADER_SIZE = 12
HEADER_FORMAT = "!IIHH"
RESPONSE_FORMAT = "!IIII"


def run_server() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    while True:
        message, client_address = server_socket.recvfrom(MESSAGE_SIZE)

        header = message[:HEADER_SIZE]
        payload_length, secret, step, student_id = struct.unpack(HEADER_FORMAT, header)

        payload = message[HEADER_SIZE : HEADER_SIZE + payload_length]

        if payload.decode() == "hello world\0":
            response_payload = struct.pack(RESPONSE_FORMAT, 1, 2, 3, 4)
            response_header = struct.pack(
                HEADER_FORMAT, len(payload), secret, step, student_id
            )

            server_socket.sendto(response_header + response_payload, client_address)


if __name__ == "__main__":
    run_server()
