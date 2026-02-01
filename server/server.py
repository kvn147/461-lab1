import math
import random
import socket
import struct
import threading

HOST = "127.0.0.1"
PORT = 50007
HEADER_SIZE = 12
HEADER_FORMAT = "!IIHH"
FIRST_MESSAGE_SIZE = 24

RESPONSE_FORMAT_A1 = "!IIII"

PACKET_ID_SIZE = 4
MESSAGE_FORMAT_B1 = "!"


def run_server() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    while True:
        message, client_address = server_socket.recvfrom(FIRST_MESSAGE_SIZE)

        thread = threading.Thread(
            target=handle_connection, args=(message, client_address)
        )

        # Verify
        #   1. Unexpected payload.
        #   2. Fails to receive packet for 3s. recvfrom timeout?
        #   3. Bad step, secret, or student number.
        #   4. Packets are 4 byte aligned.
        #
        # TODO
        #   - What is an unexpected number of buffers received?


def handle_connection(message: bytes, client_address: socket._RetAddress):
    header = message[:HEADER_SIZE]
    payload_length, secret, step, student_id = struct.unpack(HEADER_FORMAT, header)

    payload = message[HEADER_SIZE : HEADER_SIZE + payload_length]

    # Stage a
    assert payload.decode() == "hello world\0"

    number = random.randint(1, 10)
    length = random.randint(1, 10)
    udp_port = random.randint(30000, 80000)
    secret_a = random.randint(0, 1000)

    response_payload = struct.pack(
        RESPONSE_FORMAT_A1, number, length, udp_port, secret_a
    )
    response_header = struct.pack(HEADER_FORMAT, len(payload), secret, step, student_id)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, udp_port))

    server_socket.sendto(response_header + response_payload, client_address)

    # Step b1
    for packet_number in range(number):
        padding = math.ceil(length / 4) - length
        message_size = length + padding

        message, client_address = server_socket.recvfrom(message_size)

        header = message[:HEADER_SIZE]
        payload_length, secret, step, student_id = struct.unpack(HEADER_FORMAT, header)

        packet = message[HEADER_SIZE:]
        packet_id = packet[:PACKET_ID_SIZE]
        payload = packet[PACKET_ID_SIZE : PACKET_ID_SIZE + length]

        assert packet_id == packet_number
        assert payload == 0

        # Send ACK?


if __name__ == "__main__":
    run_server()
