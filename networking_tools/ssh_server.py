import os
import paramiko
import socket
import sys
import threading


# Paramiko demo SSH key
CWD = os.path.dirname(os.path.realpath(__file__))
HOSTKEY = paramiko.RSAKey(filename=os.path.join(CWD, "test_rsa.key"))


# SSH-inize request
class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if (username == "tim") and (password == "sekret"):
            return paramiko.AUTH_SUCCESSFUL


def main():
    server = "192.168.1.144"
    ssh_port = 2222
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Start socket listener
        sock.bind((server, ssh_port))
        sock.listen(100)
        print("[+] Listening for connection ...")
        client, addr = sock.accept()
    except Exception as error:
        print(f"[-] Listen failed: {str(error)}")
        sys.exit(1)
    else:
        print("[+] Got a connection!", client, addr)

    # Configure authentication method
    bhSession = paramiko.Transport(client)
    bhSession.add_server_key(HOSTKEY)
    server = Server()
    bhSession.start_server(server=server)

    chan = bhSession.accept(20)
    if chan is None:
        print("*** No channel.")
        sys.exit(1)

    # 200OK Authenticated
    print("[+] Authenticated!")
    # ClientConnected message.
    print(chan.recv(1024))
    chan.send("Welcome to bh_ssh")
    try:
        while True:
            command = input("Enter command: ")
            if command != "exit":
                chan.send(command)
                r = chan.recv(8192)
                print(r.decode())
            else:
                chan.sent("exit")
                print("exiting")
                bhSession.close()
                break
    except KeyboardInterrupt:
        bhSession.close()


if __name__ == "__main__":
    main()
