import errno
import random
import socket
import string
import struct
import sys
import threading
from dataclasses import dataclass

HEADER_LENGTH = 12
HEADER_FORMAT = "!IIHH"

@dataclass
class SessionState:
    secret: int
    step: int
    student_id: int


def run_server() -> None:
    host = sys.argv[1]
    port = int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        try:
            server_socket.bind((host, port))
        except socket.error as error:
            if error.errno == errno.EADDRINUSE:
                print("Port already in use")
                return
            else:
                raise
        except KeyboardInterrupt:
            print("Client interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Server will wait for an incoming UDP message.
        while True:
            message, client_address = server_socket.recvfrom(1024)

            # Create a new thread to handle incoming clients.
            thread = threading.Thread(
                target=handle_connection,
                args=(message, server_socket, client_address, host),
            )
            thread.start()


def handle_connection(
    message: bytes, server_socket: socket.socket, client_address: tuple[str, int], host: str
):
    try:
        session_state, num_packets_1, data_length_1, udp_port_1 = stage_a(
            message, server_socket, client_address
        )

        tcp_port = stage_b(session_state, num_packets_1, data_length_1, udp_port_1, host)

        connection, num_packets_2, data_length_2, character = stage_c(
            session_state, tcp_port, host
        )

        stage_d(session_state, connection, num_packets_2, data_length_2, character)

    except Exception:
        return


def stage_a(
    message: bytes,
    server_socket: socket.socket,
    client_address: tuple[str, int],
) -> tuple[SessionState, int, int, int]:
    # Parse header.
    header = message[:HEADER_LENGTH]
    payload_length, incoming_secret, step, student_id = struct.unpack(
        HEADER_FORMAT, header
    )

    # Verify header.
    padding = (-payload_length) % 4
    if len(message) != HEADER_LENGTH + payload_length + padding:
        raise Exception("Message not padded to 4 bytes")

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
        2,
        session_state.student_id,
    )

    # Send response.
    server_socket.sendto(response_header + response_payload, client_address)

    # Update session state from a1 to b1.
    session_state.step = 1
    session_state.secret = secret_a

    return session_state, num_packets, data_length, udp_port


def stage_b(
    session_state: SessionState, num_packets: int, data_length: int, udp_port: int, host: str
) -> int:
    server_socket, client_address = step_b1(
        session_state, num_packets, data_length, udp_port, host
    )

    tcp_port = step_b2(session_state, server_socket, client_address)

    return tcp_port


def step_b1(
    session_state: SessionState, num_packets: int, data_length: int, udp_port: int, host: str
) -> tuple[socket.socket, tuple[str, int]]:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        server_socket.bind((host, udp_port))
    except socket.error as error:
        if error.errno == errno.EADDRINUSE:
            print("Port already in use")
        raise

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
    client_address: tuple[str, int],
) -> int:

    # Generate payload values.
    tcp_port = random.randint(30000, 65535)
    secret_b = random.randint(0, 1000)

    # Build payload for b2. Should already be 4B aligned so no need padding.
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


def stage_c(
    session_state: SessionState, tcp_port: int, host: str
) -> tuple[socket.socket, int, int, int]:
    connection = step_c1(session_state, tcp_port, host)

    num_packets, data_length, character = step_c2(session_state, connection)

    return connection, num_packets, data_length, character


def step_c1(session_state: SessionState, tcp_port: int, host: str) -> socket.socket:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.settimeout(3)

    try:
        listener.bind((host, tcp_port))
    except socket.error as error:
        if error.errno == errno.EADDRINUSE:
            print("Port already in use")
        raise

    listener.listen()
    connection, _ = listener.accept()
    listener.close()

    session_state.step = 2

    return connection


def step_c2(
    session_state: SessionState, connection: socket.socket
) -> tuple[int, int, int]:
    num_packets = random.randint(1, 10)
    data_length = random.randint(1, 10)
    secret_c = random.randint(0, 1000)
    character = ord(random.choice(string.ascii_lowercase))

    payload_format = "!IIIB"
    payload = struct.pack(payload_format, num_packets, data_length, secret_c, character)
    header = struct.pack(
        HEADER_FORMAT,
        len(payload),
        session_state.secret,
        session_state.step,
        session_state.student_id,
    )

    padding_length = (-len(payload)) % 4
    padding = b"\x00" * padding_length

    connection.sendall(header + payload + padding)

    # Update state to d1.
    session_state.secret = secret_c
    session_state.step = 1

    return num_packets, data_length, character


def stage_d(
    session_state: SessionState,
    connection: socket.socket,
    num_packets: int,
    packet_length: int,
    character: int,
):
    step_d1(session_state, connection, num_packets, packet_length, character)

    step_d2(session_state, connection)


def step_d1(
    session_state: SessionState,
    connection: socket.socket,
    num_packets: int,
    packet_length: int,
    character: int,
):
    connection.settimeout(3)

    padding_length = (-packet_length) % 4
    message_length = HEADER_LENGTH + packet_length + padding_length

    buffer = b""

    for _ in range(num_packets):
        # Receive until we have the full message.
        while len(buffer) < message_length:
            data = connection.recv(1024)

            if not data:
                raise Exception("Client disconnected")

            buffer += data

        # Verify the message.
        header = buffer[:HEADER_LENGTH]
        payload_length, incoming_secret, step, student_id = struct.unpack(
            HEADER_FORMAT, header
        )
        payload = buffer[HEADER_LENGTH : HEADER_LENGTH + payload_length]

        if payload_length != packet_length:
            raise Exception("Incorrect payload length")

        if incoming_secret != session_state.secret:
            raise Exception("Incorrect secret")

        if step != session_state.step:
            raise Exception("Incorrect step")

        if student_id != session_state.student_id:
            raise Exception("Incorrect student ID")

        if payload != bytes([character]) * packet_length:
            raise Exception("Incorrect payload data")

        # Consume packet.
        buffer = buffer[message_length:]

    session_state.step = 2


def step_d2(session_state: SessionState, connection: socket.socket):
    secret_d = random.randint(0, 1000)

    payload = struct.pack("!I", secret_d)
    header = struct.pack(
        HEADER_FORMAT,
        len(payload),
        session_state.secret,
        session_state.step,
        session_state.student_id,
    )

    connection.sendall(header + payload)
    connection.close()


if __name__ == "__main__":
    run_server()
