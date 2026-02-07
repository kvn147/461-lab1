# CSE 461: Lab 1 Part 1
# Group: Wuihee Yap, Kevin Nguyen

import socket
import struct
import sys
import time

STEP = 1
STUDENT_ID = 147
HEADER_LEN = 12
BUFFER_LEN = 1024
UDP_TIMEOUT = 1
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
def stage_a(server_address, server_port):
    num, length, udp_port, secretA = None, None, None, None

    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    try:
        # Build packet with "hello world" message
        msg = "hello world\0"
        payload_bytes = msg.encode('utf-8')
        packet = build_packet(payload_bytes, 0, STEP, STUDENT_ID)

        sock.sendto(packet, (server_address, server_port))
        sock.settimeout(UDP_TIMEOUT)
        data, addr = sock.recvfrom(BUFFER_LEN)
        
        payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:HEADER_LEN])
        payload = data[HEADER_LEN:HEADER_LEN + payload_len]

        num, length, udp_port, secretA = struct.unpack("!IIII", payload)
        print(f"A: {secretA}")

    except socket.timeout:
        raise RuntimeError("Stage A timed out")
    except struct.error:
        raise RuntimeError("Stage A received malformed packet")
    except Exception as e:
        raise RuntimeError(f"Stage A error: {e}")
    finally:
        sock.close()

    return num, length, udp_port, secretA

# ==================
# Stage B:
# ==================
def stage_b(num, length, udp_port, secretA, server_address):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.settimeout(UDP_TIMEOUT)
    id = 0
    
    try:
        # Build num packets
        while id < num:
            try:
                # Create packet with current id and zero byte padding
                packet_id = struct.pack("!I", id)
                zero_byte_padding = b'\x00' * length
                payload_bytes = packet_id + zero_byte_padding
                packet = build_packet(payload_bytes, secretA, STEP, STUDENT_ID)

                sock.sendto(packet, (server_address, udp_port))
                data, addr = sock.recvfrom(BUFFER_LEN)

                # ACK has header (12 bytes) + payload (4 bytes)
                acked_id = struct.unpack("!I", data[HEADER_LEN:16])[0]
                # Only increment id if the correct ACK is received
                if acked_id == id:
                    id += 1
        
            except socket.timeout:
                # Resend packet if timeout occurs
                time.sleep(0.5)

        # After all packets are sent and ACKed, wait for final response
        sock.settimeout(TCP_TIMEOUT)
        data, addr = sock.recvfrom(BUFFER_LEN)
        payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:HEADER_LEN])
        tcp_port, secretB = struct.unpack("!II", data[HEADER_LEN:HEADER_LEN + payload_len])

        print(f"B: {secretB}")
        return tcp_port, secretB
    
    except socket.timeout:
        raise RuntimeError("Stage B timed out")
    except Exception as e:
        raise RuntimeError(f"Stage B error: {e}")
    finally:
        sock.close()

# ==================
# Stage C:
# ==================
def stage_c(tcp_port, secretB, server_address):
    sock = None
    try:
        # create tcp socket
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.settimeout(TCP_TIMEOUT)
        sock.connect((server_address, tcp_port))
        # get data and separate into values
        data = sock.recv(BUFFER_LEN)
        payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:HEADER_LEN])
        num2, len2, secretC, c = struct.unpack("!IIIc", data[HEADER_LEN:HEADER_LEN + payload_len])

        print(f"C: {secretC}")
        return sock, num2, len2, c, secretC
    
    except socket.timeout:
        if sock:
            sock.close()
        raise RuntimeError("Stage C timed out")
    except struct.error:
        if sock:
            sock.close()
        raise RuntimeError("Stage C received malformed packet")
    except Exception as e:
        if sock:
            sock.close()
        raise RuntimeError(f"Stage C error: {e}")


# ==================
# Stage D:
# ==================
def stage_d(sock, num2, len2, c, secretC):
    try:
        # generate packet to send
        payload_bytes = c * len2
        packet = build_packet(payload_bytes, secretC, STEP, STUDENT_ID)
        # send num2 packets
        for i in range(num2):
            sock.send(packet)
        # get response
        data = sock.recv(BUFFER_LEN)
        payload_len, psecret, step, sid = struct.unpack("!IIHH", data[:HEADER_LEN])
        secretD = int.from_bytes(data[HEADER_LEN:HEADER_LEN + payload_len], "big")

        print(f"D: {secretD}")
        return secretD
    
    except socket.timeout:
        raise RuntimeError("Stage D timed out")
    except Exception as e:
        raise RuntimeError(f"Stage D error: {e}")
    finally:
        sock.close()


def main():
    try:
        # Ensure correct arguments are provided
        if len(sys.argv) != 3:
            print("Usage: python client.py <server_address> <server_port>")
            sys.exit(1)
        
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])

        # Execute stages A through D
        num, length, udp_port, secretA = stage_a(server_address, server_port)
        tcp_port, secretB = stage_b(num, length, udp_port, secretA, server_address)
        sock, num2, len2, c, secretC = stage_c(tcp_port, secretB, server_address)
        secretD = stage_d(sock, num2, len2, c, secretC)

    except KeyboardInterrupt:
        print("Client interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()