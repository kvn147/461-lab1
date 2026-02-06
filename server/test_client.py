import socket
import struct

HOST = "127.0.0.1"
PORT = 50008
HEADER_FORMAT = "!IIHH"
HEADER_LENGTH = 12
STUDENT_ID = 100


def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        # Step a1
        client_socket.bind((HOST, PORT))

        payload = b"hello world\0"
        header = struct.pack(HEADER_FORMAT, len(payload), 0, 1, STUDENT_ID)

        client_socket.sendto(header + payload, (HOST, 50007))

        message, _ = client_socket.recvfrom(1024)
        header, payload = message[:HEADER_LENGTH], message[HEADER_LENGTH:]

        # Step b1
        num_packets, data_length, udp_port, secret = struct.unpack("!IIII", payload)

        step_b1(client_socket, num_packets, data_length, udp_port, secret)


def step_b1(
    client_socket: socket.socket,
    num_packets: int,
    data_length: int,
    udp_port: int,
    secret: int,
):
    client_socket.settimeout(1)

    packet_id = 0
    payload_length_no_padding = HEADER_LENGTH + data_length
    padding = (-payload_length_no_padding) % 4

    while packet_id < num_packets:
        payload = struct.pack("!I", packet_id) + b"\x00" * (data_length + padding)
        header = struct.pack(HEADER_FORMAT, len(payload), secret, 1, STUDENT_ID)

        client_socket.sendto(header + payload, (HOST, udp_port))

        try:
            _ = client_socket.recvfrom(1024)
            packet_id += 1
            print(f"ACK received for packet {packet_id} (I think)")
        except TimeoutError:
            continue

    print("YEAH")


if __name__ == "__main__":
    run_client()
