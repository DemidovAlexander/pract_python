__author__ = 'Demidov'

import threading
import sys


def abort_prg(error):
    print(error + '\ncorrect parameters: filename ip [ip2 [ip3 ...]] ')
    sys.exit(1)


def check_parameters():
    if (len(sys.argv) < 3):
        abort_prg('too few parameters')

    for current_ip in sys.argv[2::]:
        import re
        ip_expression = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')
        if not(ip_expression.match(current_ip)):
            abort_prg('wrong ip: ' + current_ip)


def ping_ip(ip, file_lock, file):
        import subprocess
        result = subprocess.call(["ping", '-n', '1', ip], stdout = subprocess.PIPE)

        file_lock.acquire()
        try:
            if result == 0:
                file.write(ip + '\n')
        finally:
            file_lock.release()


def pinger(file):
    file_lock = threading.Lock()
    threads = []
    for current_ip in sys.argv[2::]:
        threads.append(threading.Thread(target = ping_ip, args = (current_ip, file_lock, file)))
        threads[-1].start()

    for current_ip in threads:
        current_ip.join()


check_parameters()

try:
    file = open(sys.argv[1], 'w')
except IOError:
    abort_prg('wrong filename: ' + sys.argv[1])

pinger(file)
file.close()













