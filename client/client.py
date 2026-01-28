# CSE 461: Lab 1 Part 1
# Group: Wuihee Yap, Kevin Nguyen

import socket
import struct

STEP = 1
STUDENT_ID = 147
HEADER_LEN = 12
BUFFER_LEN = 1024
ADDRESS = "attu2.cs.washington.edu"
PORT = 41201
UDP_TIMEOUT = 0.5
TCP_TIMEOUT = 5

# ==================
# Helper Functions:
# ==================

def make_header(payload_len, psecret, step, student_id):
    return struct.pack("!IIHH", payload_len, psecret, step, student_id)

def payload_padding(data):
    padding_needed = (4 - len(data) % 4) % 4
    return data + b'\x00' * padding_needed

def build_packet(payload_bytes, psecret, step, student_id):
    payload_content = payload_padding(payload_bytes)
    header_content = make_header(len(payload_bytes), psecret, step, student_id)
    return header_content + payload_content

# ==================
# Stage A:
# ==================
def stage_a():
    # Create UDP socket
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    try:
        # Build packet
        msg = "hello world\0"
        payload_bytes = msg.encode('utf-8')
        packet = build_packet(payload_bytes, 0, STEP, STUDENT_ID)

        sock.sendto(packet, (ADDRESS, PORT))
        sock.settimeout(UDP_TIMEOUT)
        data, addr = sock.recvfrom(BUFFER_LEN)

        payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:HEADER_LEN])
        payload = data[HEADER_LEN:HEADER_LEN + payload_len]

        num, length, udp_port, secretA = struct.unpack("!IIII", payload)
        print(f"A: {secretA}")

    except socket.timeout:
        pass
    finally:
        sock.close()

    return num, length, udp_port, secretA

# ==================
# Stage B:
# ==================
def stage_b(num, length, udp_port, secretA):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.settimeout(UDP_TIMEOUT)
    id = 0
  
    # Build num packets
    while id < num:
        try:
            packet_id = struct.pack("!I", id)
            zero_byte_padding = b'\x00' * length
            payload_bytes = packet_id + zero_byte_padding
            packet = build_packet(payload_bytes, secretA, STEP, STUDENT_ID)

            sock.sendto(packet, (ADDRESS, udp_port))
            data, addr = sock.recvfrom(BUFFER_LEN)

            # ACK has header (12 bytes) + payload (4 bytes)
            acked_id = struct.unpack("!I", data[HEADER_LEN:16])[0]
            # Check if ACKed id matches sent id, otherwise resend
            if acked_id == id:
                id += 1
    
        except socket.timeout:
            pass

    sock.settimeout(TCP_TIMEOUT)
    data, addr = sock.recvfrom(BUFFER_LEN)
    payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:HEADER_LEN])
    tcp_port, secretB = struct.unpack("!II", data[HEADER_LEN:HEADER_LEN + payload_len])
    sock.close()

    print(f"B: {secretB}")
    return tcp_port, secretB

# ==================
# Stage C:
# ==================
def stage_c(tcp_port, secretB):
    pass

# ==================
# Stage D:
# ==================
def stage_d():
    pass

def main():
    num, length, udp_port, secretA = stage_a()
    tcp_port, secretB = stage_b(num, length, udp_port, secretA)
    stage_c(tcp_port, secretB)
    stage_d()

if __name__ == "__main__":
    main()