import random
import socket
import struct
import threading

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

        thread = threading.Thread(
            target=handle_connection, args=(message, client_address)
        )

        # Verify
        #   1. Unexpected payload.
        #   2. Fails to receive packet for 3s.
        #   3. Bad step, secret, or student number.
        #
        # TODO
        #   - What is an unexpected number of buffers received?
        #   - How to do multi-threading?


def handle_connection(message: bytes, client_address):
    header = message[:HEADER_SIZE]
    payload_length, secret, step, student_id = struct.unpack(HEADER_FORMAT, header)

    payload = message[HEADER_SIZE : HEADER_SIZE + payload_length]

    if payload.decode() == "hello world\0":
        number = random.randint(1, 10)
        length = random.randint(1, 10)
        udp_port = random.randint(30000, 80000)
        secret_a = random.randint(0, 1000)

        response_payload = struct.pack(
            RESPONSE_FORMAT, number, length, udp_port, secret_a
        )
        response_header = struct.pack(
            HEADER_FORMAT, len(payload), secret, step, student_id
        )

        # TODO?
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((HOST, PORT))

        server_socket.sendto(response_header + response_payload, client_address)


if __name__ == "__main__":
    run_server()
