def make_header(payload_len, psecret, step, student_id):
    return struct.pack("!I I H H", payload_len, psecret, step, len(student_id), student_id)

