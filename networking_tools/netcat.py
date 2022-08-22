import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading


class NetCat:
    # Init object with CLI arguments and buffer
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # Create socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        # Delegate execution to listen method
        if self.args.listen:
            self.listen()
        # Deletegate execution to send method
        else:
            self.send()

    def send(self):
        # Connect to target & port
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)

        # Implement manual connection close with CTRL + C (try/except handle)
        try:
            # Start receiving data from target
            while True:
                recv_len = 1
                response = ""
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    # if there is no more data, break
                    if recv_len < 4096:
                        break
                # Print response data, pause to get interactive input & send input
                if response:
                    print(response)
                    buffer = input("> ")
                    buffer += "\n"
                    self.socket.send(buffer.encode())
        # Loop will continue until close connection with CTRL + C
        except KeyboardInterrupt:
            print("User terminated.")
            self.socket.close()
            sys.exit()

    def listen(self):
        # Binds to target & port
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        # starts listening
        while True:
            client_socket, _ = self.socket.accept()
            # Passing connected socket to the handle method
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

    def handle(self, client_socket):
        '''
        Executes task corresponding to given command-line argument it receives.
        '''
        # Execute command
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        # Upload file
        elif self.args.upload:
            file_buffer = b""
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break

            with open(self.args.upload, "wb") as file:
                file.write(file_buffer)
            message = f"Saved file {self.args.upload}"
            client_socket.send(message.encode())

        # Start shell
        elif self.args.command:
            cmd_buffer = b""
            while True:
                try:
                    client_socket.send(b"BHP: #> ")
                    while "\n" not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b""
                except Exception as error:
                    print(f"server killed {error}")
                    self.socket.close()
                    sys.exit()


def main():
    # Create CLI with argparse module
    parser = argparse.ArgumentParser(
        description="BHP Net Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Example usage for --help
        epilog=textwrap.dedent('''Example:
            netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
            netcat.py -t 192.168.1.108 -p 5555 -l -e="cat /etc/passwd" # execute command
            echo "ABC" | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
            netcat.py -t 192.168.1.108 -p 5555 # connect to server
        '''))
    # Add arguments
    parser.add_argument("-c", "--command", action="store_true", help="command shell")
    parser.add_argument("-e", "--execute", help="execute specified command")
    parser.add_argument("-l", "--listen", action="store_true", help="listen")
    parser.add_argument("-p", "--port", type=int, default=5555, help="specified port")
    parser.add_argument("-t", "--target", default="192.168.1.203", help="specified IP")
    parser.add_argument("-u", "--upload", help="upload file")
    args = parser.parse_args()
    # Set netcat as listener (-c, -e, -u arguments imply the -l)
    if args.listen:
        buffer = ""
    # Set netcat as sender (-t and -p)
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args, buffer.encode())
    nc.run()


def execute(cmd):
    '''
    Receives command, runs it in local OS, and returns the output as a string
    '''
    cmd = cmd.strip()
    if not cmd:
        return

    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()


if __name__ == "__main__":
    main()
