# CSE 461: Lab 1 Part 1
# Group: Wuihee Yap, Kevin Nguyen

import socket
import struct

STUDENT_ID = 147
BUFFER_LEN = 1024
ADDRESS = "attu2.cs.washington.edu"
PORT = 41201

# ==================
# Helper Functions:
# ==================

def make_header(payload_len, psecret, step, student_id):
    return struct.pack("!IIHH", payload_len, psecret, step, student_id)

def payload_padding(data):
    padding_needed = (4 - len(data) % 4) % 4
    return data + b'\x00' * padding_needed

# ==================
# Stage A:
# ==================

# Create UDP socket
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Build packet -> header + "hello world\0"
msg = "hello world\0"
payload_bytes = msg.encode('utf-8')
payload_content = payload_padding(payload_bytes)
header_content = make_header(len(payload_bytes), 0, 1, STUDENT_ID)
packet = header_content + payload_content

# Send to attu2 at port 41201
sock.sendto(packet, (ADDRESS, PORT))

# Receive response
sock.settimeout(5)
data, addr = sock.recvfrom(BUFFER_LEN)

# Parse the header
payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:12])

# Parse the payload
payload = data[12:12 + payload_len]

# Unpack the payload for Stage A
num, length, udp_port, secretA = struct.unpack("!IIII", payload)

# Print the secret
print(f"A: {secretA}")

# Close the socket
sock.close()

# ==================
# Stage B:
# ==================
