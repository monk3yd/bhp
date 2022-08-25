import getpass
import paramiko
import shlex
import subprocess


def main():
    user = getpass.getuser()
    password = getpass.getpass()

    ip = input("Enter server IP: ")
    port = input("Enter port: ")
    ssh_command(ip, port, user, password, "ClientConnected")
    ...


def ssh_command(ip, port, user, passwd, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command)
        print(ssh_session.recv(1024).decode())
        while True:
            # Take command from connection
            command = ssh_session.recv(1024)
            try:
                cmd = command.decode()
                if cmd == "exit":
                    client.close()
                    break
                # Execute the command
                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True)
                # Send output back to caller
                ssh_session.send(cmd_output or "okay")
            except Exception as error:
                ssh_session.send(str(error))
        client.close()
    return


if __name__ == "__main__":
    main()
