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
    secret: int
    step: int
    student_id: int


def run_server() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    while True:
        message, client_address = server_socket.recvfrom(FIRST_MESSAGE_SIZE)

        # Create a new thread to handle incoming clients.
        thread = threading.Thread(
            target=handle_connection, args=(message, server_socket, client_address)
        )
        thread.start()


def handle_connection(
    message: bytes, server_socket: socket.socket, client_address: socket._RetAddress
):
    session_state, num_packets, packet_length, udp_port = step_a(
        message, server_socket, client_address
    )


def step_a(
    message: bytes,
    server_socket: socket.socket,
    client_address: socket._RetAddress,
) -> tuple[SessionState, int, int, int]:
    # Parse header.
    header = message[:HEADER_SIZE]
    payload_length, incoming_secret, step, student_id = struct.unpack(
        HEADER_FORMAT, header
    )

    # Verify header.
    if len(message) < HEADER_SIZE + payload_length:
        raise Exception("Incomplete payload")

    if incoming_secret != 0:
        raise Exception("Stage a requires psecret = 0")

    if step != 1:
        raise Exception("Invalid step for stage a")

    # Verify payload.
    payload = message[HEADER_SIZE : HEADER_SIZE + payload_length]

    if payload != b"hello world\0":
        raise Exception("Invalid payload")

    # Update session state to step a1.
    session_state = SessionState(
        secret=incoming_secret,
        step=step,
        student_id=student_id,
    )

    # Generate response values.
    num_packets = random.randint(1, 10)
    packet_length = random.randint(1, 10)
    udp_port = random.randint(30000, 65535)
    secret_a = random.randint(0, 1000)

    # Build response.
    response_payload = struct.pack(
        "!IIII", num_packets, packet_length, udp_port, secret_a
    )
    response_header = struct.pack(
        HEADER_FORMAT,
        len(response_payload),
        session_state.secret,
        session_state.step,
        session_state.student_id,
    )

    # Send response.
    server_socket.sendto(response_header + response_payload, client_address)

    # Update session state from a1 to b1.
    session_state.step = 1
    session_state.secret = secret_a

    return session_state, num_packets, packet_length, udp_port


if __name__ == "__main__":
    run_server()
