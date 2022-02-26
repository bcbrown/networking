import os
import select
import signal
import socket
import struct
import sys
import time

# inspired by https://github.com/toxinu/pyping/blob/main/pyping/core.py

# ICMP parameters
ICMP_ECHOREPLY = 0 # Echo reply (per RFC792)
ICMP_ECHO = 8 # Echo request (per RFC792)
ICMP_MAX_RECV = 2048 # Max size of incoming buffer

def calculate_checksum(source_string):
    """
    A port of the functionality of in_cksum() from ping.c
    Ideally this would act on the string as a series of 16-bit ints (host
    packed), but this works.
    Network data is big-endian, hosts are typically little-endian
    """
    countTo = (int(len(source_string) / 2)) * 2
    sum = 0
    count = 0

    # Handle bytes in pairs (decoding as short ints)
    loByte = 0
    hiByte = 0
    while count < countTo:
        if (sys.byteorder == "little"):
            loByte = source_string[count]
            hiByte = source_string[count + 1]
        else:
            loByte = source_string[count + 1]
            hiByte = source_string[count]
        sum = sum + (hiByte * 256 + loByte)
        count += 2

    sum &= 0xffffffff # Truncate sum to 32 bits (a variance from ping.c, which
                      # uses signed ints, but overflow is unlikely in ping)

    sum = (sum >> 16) + (sum & 0xffff)  # Add high 16 bits to low 16 bits
    sum += (sum >> 16)                  # Add carry from above (if any)
    answer = ~sum & 0xffff              # Invert and truncate to 16 bits
    answer = socket.htons(answer)

    return answer

current_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))

if True:
    current_socket.bind(('', 0))

# Header is type (8), code (8), checksum (16), id (16), sequence (16)
checksum = 0
own_id = os.getpid() & 0xFFFF
seq_number = 0
# Make a dummy header with a 0 checksum.
header = struct.pack("!BBHHH", ICMP_ECHO, 0, checksum, own_id, seq_number)
padBytes = []
startVal = 0x42
packet_size = 55

for i in range(startVal, startVal + (packet_size)):
    padBytes += [(i & 0xff)]  # Keep chars in the 0-255 range
data = bytes(padBytes)

checksum = calculate_checksum(header + data)
# Now that we have the right checksum, we put that in. It's just easier
# to make up a new header than to stuff it into the dummy.
header = struct.pack("!BBHHH", ICMP_ECHO, 0, checksum, own_id, seq_number)
packet = header + data
print(header)
print(data)

destination = 'www.google.com'
destination = '142.250.69.196'
current_socket.sendto(packet, (destination, 1))



while True: # Loop while waiting for packet or timeout
    timeout = 10 # in seconds
    print('select')
    select_start = time.time()
    inputready, outputready, exceptready = select.select([current_socket], [], [], timeout)
    print('selected')
    select_duration = (time.time() - select_start)
    if inputready == []: # timeout
        print('timeout')
        exit()
    packet_data, address = current_socket.recvfrom(ICMP_MAX_RECV)
    print(packet_data)
    print(address)
    

if __name__ == '__main__':
    print('running')
