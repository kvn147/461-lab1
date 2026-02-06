import random
import socket
import struct
import threading
from dataclasses import dataclass

HOST = "127.0.0.1"
PORT = 50007
HEADER_LENGTH = 12
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
    session_state, num_packets, data_length, udp_port = stage_a(
        message, server_socket, client_address
    )

    tcp_port = stage_b(session_state, num_packets, data_length, udp_port)


def stage_a(
    message: bytes,
    server_socket: socket.socket,
    client_address: socket._RetAddress,
) -> tuple[SessionState, int, int, int]:
    # Parse header.
    header = message[:HEADER_LENGTH]
    payload_length, incoming_secret, step, student_id = struct.unpack(
        HEADER_FORMAT, header
    )

    # Verify header.
    if len(message) < HEADER_LENGTH + payload_length:
        raise Exception("Incomplete message size")

    if incoming_secret != 0:
        raise Exception("Incorrect secret")

    if step != 1:
        raise Exception("Incorrect step")

    # Verify payload.
    payload = message[HEADER_LENGTH : HEADER_LENGTH + payload_length]

    if payload != b"hello world\0":
        raise Exception("Incorrect payload")

    # Update session state to step a1.
    session_state = SessionState(
        secret=incoming_secret,
        step=step,
        student_id=student_id,
    )

    # Generate response values.
    num_packets = random.randint(1, 10)
    data_length = random.randint(1, 10)
    udp_port = random.randint(30000, 65535)
    secret_a = random.randint(0, 1000)

    # Build response.
    response_payload = struct.pack(
        "!IIII", num_packets, data_length, udp_port, secret_a
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

    return session_state, num_packets, data_length, udp_port


def stage_b(
    session_state: SessionState, num_packets: int, data_length: int, udp_port: int
) -> int:
    server_socket, client_address = step_b1(
        session_state, num_packets, data_length, udp_port
    )

    tcp_port = step_b2(session_state, server_socket, client_address)

    return tcp_port


def step_b1(
    session_state: SessionState, num_packets: int, data_length: int, udp_port: int
) -> tuple[socket.socket, socket._RetAddress]:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, udp_port))
    server_socket.settimeout(3)

    client_address = ()

    packet_id_length = 4
    payload_length_no_padding = packet_id_length + data_length
    padding = (-payload_length_no_padding) % 4

    expected_packet = 0
    skipped_ack = False

    while expected_packet < num_packets:
        message, client_address = server_socket.recvfrom(1024)

        # Parse header.
        header = message[:HEADER_LENGTH]
        payload_length, incoming_secret, step, student_id = struct.unpack(
            HEADER_FORMAT, header
        )

        # Verify header.
        if payload_length != packet_id_length + data_length:
            raise Exception("Incorrect payload length")

        if len(message) != HEADER_LENGTH + payload_length + padding:
            raise Exception("Message not padded to 4 bytes")

        if incoming_secret != session_state.secret:
            raise Exception("Incorrect secret")

        if step != session_state.step:
            raise Exception("Incorrect step")

        if student_id != session_state.student_id:
            raise Exception("Incorrect student ID")

        # Verify packet ID.
        payload = message[HEADER_LENGTH : HEADER_LENGTH + payload_length]
        (packet_id,) = struct.unpack("!I", payload[:packet_id_length])

        if packet_id != expected_packet:
            raise Exception("Incorrect packet ID")

        # Verify data.
        data = payload[packet_id_length : packet_id_length + data_length]

        if data != b"\x00" * data_length:
            raise Exception("Incorrect data")

        # ACK logic.
        should_ack = random.choice([True, False])

        if not skipped_ack and should_ack:
            should_ack = False
            skipped_ack = True

        if should_ack:
            ack_payload = struct.pack("!I", packet_id)
            ack_header = struct.pack(
                HEADER_FORMAT,
                len(ack_payload),
                session_state.secret,
                session_state.step,
                session_state.student_id,
            )

            server_socket.sendto(ack_header + ack_payload, client_address)

            expected_packet += 1

    # Update session state to b2.
    session_state.step = 2

    return server_socket, client_address


def step_b2(
    session_state: SessionState,
    server_socket: socket.socket,
    client_address: socket._RetAddress,
) -> int:

    # Generate payload values.
    tcp_port = random.randint(30000, 65535)
    secret_b = random.randint(0, 1000)

    # Build payload for b2.
    payload_format = "!II"
    payload = struct.pack(payload_format, tcp_port, secret_b)
    header = struct.pack(
        HEADER_FORMAT,
        len(payload),
        session_state.secret,
        session_state.step,
        session_state.student_id,
    )

    server_socket.sendto(header + payload, client_address)
    server_socket.close()

    # Update session to stage c1.
    session_state.secret = secret_b
    session_state.step = 1

    return tcp_port


if __name__ == "__main__":
    run_server()
