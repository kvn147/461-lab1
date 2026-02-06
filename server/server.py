import math
import random
import socket
import struct
import threading
from dataclasses import dataclass

HOST = "127.0.0.1"
PORT = 50007
HEADER_SIZE = 12
HEADER_FORMAT = "!IIHH"
FIRST_MESSAGE_SIZE = 24


@dataclass
class SessionState:
    secret: int = 0
    step: int = 1
    student_id: int = -1

    def is_valid_state(self, secret: int, step: bytes, student_id: bytes) -> bool:
        return (
            secret == self.secret
            and step == self.step
            and student_id == self.student_id
        )


def run_server() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    while True:
        message, client_address = server_socket.recvfrom(FIRST_MESSAGE_SIZE)

        session_state = SessionState()

        # Create a new thread to handle incoming clients.
        thread = threading.Thread(
            target=handle_connection, args=(message, client_address, session_state)
        )
        thread.start()


def handle_connection(
    message: bytes, client_address: socket._RetAddress, session_state: SessionState
):
    num_packets, packet_length, udp_port = step_a(
        message, client_address, session_state
    )

    # step_b1(num_packets, packet_length, udp_port, session_state)


def step_a(
    message: bytes, client_address: socket._RetAddress, session_state: SessionState
) -> tuple[int, int, int]:
    # Parse header.
    header = message[:HEADER_SIZE]
    payload_length, secret, step, student_id = struct.unpack(HEADER_FORMAT, header)
    payload = message[HEADER_SIZE : HEADER_SIZE + payload_length]

    # Update state
    session_state.student_id = student_id

    # Verify header
    if not session_state.is_valid_state(secret, step, student_id):
        raise Exception("Invalid header")

    # Verify payload.
    if payload != b"hello world\0":
        raise Exception("Invalid payload")

    num_packets = random.randint(1, 10)
    packet_length = random.randint(1, 10)
    udp_port = random.randint(30000, 65535)
    next_secret = random.randint(0, 1000)

    response_format = "!IIII"
    response_payload = struct.pack(
        response_format, num_packets, packet_length, udp_port, secret
    )
    response_header = struct.pack(
        HEADER_FORMAT,
        len(response_payload),
        secret,
        session_state.step,
        session_state.student_id,
    )
    response_packet = response_header + response_payload

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((HOST, udp_port))
        server_socket.sendto(response_packet, client_address)

    # Update state for stage b1.
    session_state.step = 1
    session_state.secret = next_secret

    return num_packets, packet_length, udp_port


def step_b1(
    num_packets: int, packet_length: int, udp_port: int, session_state: SessionState
):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((HOST, udp_port))
        server_socket.settimeout(3)

        padding_length = math.ceil(packet_length / 4) - packet_length
        packet_id_length = 4
        packet_count = 0

        ack_not_sent = False

        while packet_count < num_packets:
            message, client_address = server_socket.recvfrom(1024)

            header = message[:HEADER_SIZE]
            payload_length, secret, step, student_id = struct.unpack(
                HEADER_FORMAT, header
            )

            if (
                not session_state.is_valid_state(secret, step, student_id)
                or packet_length + padding_length != payload_length
            ):
                raise Exception("Invalid header")

            payload = message[HEADER_SIZE : HEADER_SIZE + payload_length]
            packet_id = payload[:packet_id_length]
            remaining_payload = payload[
                packet_id_length : packet_id_length + packet_length
            ]

            if packet_id != packet_count:
                raise Exception("Invalid packet ID")

            if remaining_payload != 0:
                raise Exception("Invalid payload")

            # Send ACK
            if ack_not_sent and random.choice([True, False]):
                ack_format = "!I"
                ack_payload = struct.pack(ack_format, packet_id)
                ack_header = struct.pack(
                    HEADER_FORMAT, len(ack_payload), secret, step, student_id
                )
                ack_packet = ack_header + ack_payload

                server_socket.sendto(ack_packet, client_address)

                packet_count += 1

                continue

            ack_not_sent = True


if __name__ == "__main__":
    run_server()
