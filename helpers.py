import socket
from uuid import getnode as get_mac


def get_local_ip():
    """Gets the local ip to reach the given ip.
    That can be influenced by the system's routing table.
    A socket is opened and closed immediately to achieve that."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.0.1", 80))
    except Exception as e:
        print("Cannot create socket to target " + targetHost + ":" + targetPort)
    else:
        ip = s.getsockname()[0]
        s.close()
    return ip



def get_local_mac():
    return get_mac()