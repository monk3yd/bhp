import paramiko
import getpass


def main():
    # user = getpass.getuser()
    user = input("Username: ")
    password = getpass.getpass()

    ip = input("Enter server IP: ") or "192.168.1.174"
    port = input("Enter port or <CR>: ") or 22
    cmd = input("Enter command or <CR>: ") or "id"
    ssh_command(ip, port, user, password, cmd)


def ssh_command(ip, port, user, passwd, cmd):
    '''
    Makes connection to ssh server and runs a single command.
    '''
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # For real engagement we should use SSH key authentication instead
    client.connect(
        ip,
        port=port,
        username=user,
        password=passwd,
    )

    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()
    if output:
        print("---Output---")
        for line in output:
            print(line.strip())


if __name__ == "__main__":
    main()
