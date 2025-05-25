import logging
from libs.configuration import *
import paramiko

logger = logging.getLogger(__name__)

def ssh_execute_command():
    COMMAND = "/sbin/rebootfromnand && /sbin/reboot"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=coreelec_host, username=coreelec_user, password=coreelec_password, timeout=10)
        stdin, stdout, stderr = client.exec_command(COMMAND)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return output, error
    finally:
        client.close()