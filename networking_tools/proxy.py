import sys
import socket
import threading

# Create HEX_FILTER string that contains ASCII printable characters if exists,
# else print a dot (.)
HEX_FILTER = "".join(
    [(len(repr(chr(i))) == 3) and chr(i) or "." for i in range(256)]
)


def main():
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end="")
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)

    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


def hexdump(src, length=16, show=True):
    '''
    Provides with a way to watch the communication going through a proxy in real time.
    '''
    # Decode byte string if passed in
    if isinstance(src, bytes):
        src = src.decode()

    results = list()
    for i in range(0, len(src), length):
        # Grab piece of string
        word = str(src[i:i+length])

        # Substitute representetation of each chracter for corresponding character in raw string.
        printable = word.translate(HEX_FILTER)
        # Substitute the hex representation of the integer value of every character in the raw string.
        hexa = " ".join([f"{ord(c):02X}" for c in word])
        hexwidth = length * 3
        # index hex value of the fisrt byte of word, hex value of the word, and printable representation
        results.append(f"{i:04x} {hexa:<{hexwidth}} {printable}")
    if show:
        for line in results:
            print(line)
        else:
            return results


def receive_from(connection):
    '''
    Two ends of the proxy will use this function to receive data.
    For receiving both local and remote data, we pass in the socket object to be used (connection).
    '''
    # Create byte string buffer that will accumulate responses from socket
    buffer = b""
    # default 5 seconds timeout (increase as necessary)
    connection.settimeout(5)
    try:
        # Read response data into buffer until no more data or timeout
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception:
        pass
    # return buffer byte string to the caller (local or remote machine)
    return buffer


def request_handler(buffer):
    # perform packet modifications
    return buffer


def response_handler(buffer):
    # perform packet modifications
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    '''Logic for proxy'''
    # Instantiate socket object
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to remote host
    remote_socket.connect((remote_host, remote_port))

    # Check if inititate a connection to remote side and request data before main
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        # Dumps content of package so that we can inspect it
        hexdump(remote_buffer)

    remote_buffer = response_handler(remote_buffer)
    if len(remote_buffer):
        # Send received buffer to local client
        print(f"[<==] Sending {len(remote_buffer)} bytes to localhost.")
        client_socket.send(remote_buffer)

    while True:
        # Continually read from local client, process the data and send it to remote client
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            line = f"[==>]Received {len(local_buffer)} bytes from localhost."
            print(line)
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        # Read from remote client, process the data and send it to the local client
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print(f"[<==] Received {len(remote_buffer)} bytes from remote.")
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")

        # until we no longer detect any data on either side of proxy
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    # Create socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Bind to local host
        server.bind((local_host, local_port))
    except Exception as error:
        print(f"problem on bind: {error}")

        print(f"[!!] Failed to listen on {local_host}:{local_port}")
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    # Listen to local host
    print(f"[*] Listening on {local_host}{local_port}")
    server.listen(5)
    # Main loop handles new connection request by passing it into proxy_handler
    # in new thread
    while True:
        client_socket, addr = server.accept()
        # print out the local connection informatin
        line = f"> Received incoming connection from {addr[0]}:{addr[1]}"
        print(line)
        # start a thread to talk (send/receive) to the remote host
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first)
        )
        proxy_thread.start()


if __name__ == "__main__":
    main()
