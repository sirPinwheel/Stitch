#!/usr/bin/env python3

from threading import Thread, Lock
from datetime import datetime
import socket
import ssl
import sys
import os.path
try: import certifi
except ImportError: sys.exit('[ERROR] "certifi" module is required')

HOST = 'irc.twitch.tv' # default Twitch hostname
PORT = 6697 # default Twitch port with SSL support
NAME = ''
OAUTH = ''
CHANNEL = ''
INPUT_ENABLE = True
TIMESTAMPS_ENABLE = False

def display_help():
    print("""tccli.py needs username, name of the channel and oauth token of that user
You can mix and match what's in the configuration file and what's
passed as the argument to the program, arguments will override data
from the configuration file.

usage:
    python3 tccli.py [option 1] <arg 1> [option 2] <arg 2>...
    ./tccli.py [option 1] <arg 1> [option 2] <arg 2>...

    If "--config <file>" is not provided the script will look for configuration
    file in this order in following locations:

    UNIX:                       WINDOWS:
    1) ~/.config/tccli/config   1) ./config.ini ("." meaning the folder containing tccli.py)
    2) ~/.tcclirc

    Those will also be overridden by arguments passed while launching the script
    To quit chat simply type in !exit or !quit

options:
    -n <name>        name of the account to use
    -c <channel>     name of the cahnnel to connect to (including "#" at the beginning)
    -o <oauth>       oauth string (including "oauth:" at the beginning)
    --config <path>  path to configuration file
    --spectate       disable sending messages to the server
    --timestamps     use [h:m:s] timestamps

examples:
    python3 tccli.py -n 'my_bot_account' -c 'my_epic_channel' -o 'oauth:abcdefghijkl...'
    python3 tccli.py --config './conf.cfg'
    python3 tccli.py --config './conf.cfg' -c 'my_epic_channel'
    python3 tccli.py --config './conf.cfg' --spectate

configuration file format:
    name=name_of_user
    channel=name_of_channel
    oauth=oauth:abcdefghijkl""")

class IrcClient():
    """
    Class for connecting to Twitch's IRC chat server. Uses socket with SSL functionality
    """
    def __init__(self):
        self._host = ''
        self._port = 0
        self._user = ''
        self._oauth = ''
        self._channel = ''
        self._connection = None
        self._connection_lock = Lock()
        self._send_lock = Lock()
        self._message_handlers = []

    def __del__(self):
        if self._connection is not None:
            self.disconnect()

    def connect(self, host, port, user, oauth, channel):
        """
        Connects to the IRC chat using socket, saves socket object to self._connection
        SSL certificated provided by certifi module
        """
        self._connection_lock.acquire()

        try:
            if self._connection is None:
                self._connection = socket.socket()
                self._connection = ssl.wrap_socket(self._connection,
                    ca_certs=certifi.where(),
                    server_side=False)

                try:
                    self._connection.connect((host, port))
                except socket.gaierror:
                    raise RuntimeError("Connection attempt failed")

                self._connection.send(f'PASS {oauth}\r\n'.encode('utf-8'))
                self._connection.send(f'NICK {user}\r\n'.encode('utf-8'))
                self._connection.send(f'USER {user} {host} : {user}\r\n'.encode('utf-8'))
                self._connection.send(f'JOIN {channel}\r\n'.encode('utf-8'))

                self._host = host
                self._port = port
                self._user = user
                self._oauth = oauth
                self._channel = channel

                self._message_thread = Thread(target=self._message_loop, name="IrcMessageThread")
                self._message_thread.start()

            else:
                raise RuntimeError('The client is already connected')
        finally:
            self._connection_lock.release()

    def disconnect(self):
        """
        Performs safe disconnect informing host about it
        _connection should be None after that
        """
        self._connection_lock.acquire()

        connection = self._connection
        self._connection = None

        self._connection_lock.release()

        if connection is not None:
            connection.send(f'PART {self._channel}\r\n'.encode('utf-8'))
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
        else:
            raise RuntimeError('The client is not connected')

        if self._message_thread is not None:
            self._message_thread.join()
        else:
            raise RuntimeError('The message thread is not running')

    def is_connected(self):
        """
        Checks if connection is established, returns boolean
        """
        if self._connection is None:
            return False
        else:
            return True

    def _send_data(self, data):
        """
        Sends raw data taking into account connection/packet limitations
        """
        self._send_lock.acquire()

        try:
            data_sent = 0
            while data_sent < len(data):
                data_sent += self._connection.send(data[data_sent:])
        finally:
            self._send_lock.release()

    def _message_loop(self):
        """
        Waits for message data to be recieved, after that
        calls _process_message
        """
        buffer = ""
        while self._connection is not None:
            message_end = buffer.find('\r\n')
            if message_end == -1:
                try: buffer += self._connection.recv(1024).decode('utf-8')
                except OSError: return
            else:
                message = buffer[:message_end]
                buffer = buffer[message_end + 2:]
                self._process_message(message)

    def send_message(self, message):
        """
        Wraps a string in IRC specific stuff, also encodes to UTF-8 to
        be sent using _send_raw
        """
        if self._connection is None:
            raise RuntimeError('The client is not connected')

        self._send_data(f'PRIVMSG {self._channel} :{message}\r\n'.encode('utf-8'))

    def _process_message(self, message):
        if message[:4] == "PING":
            self._send_data(f'PONG {message[4:]}\r\n'.encode('utf-8'))
            return
        if message.split()[0] == ":tmi.twitch.tv": return
        if message.split()[0] == ":" + self._user.lower() + ".tmi.twitch.tv".format(): return
        if message.split("!")[0] == ":" + self._user.lower(): return

        for message_handler in self._message_handlers:
            message_handler(message)

    def add_handler(self, handler):
        """
        """
        if callable(handler):
            self._message_handlers.append(handler)
        else:
            raise RuntimeError('Handler must be callable')

def parse_cfg(filename):
    """
    Simple parser for config file
    """
    if not os.path.exists(filename):
        sys.exit('[ERROR] Configuration file does not exist (-h or --help for help)')

    _name = ''
    _channel = ''
    _oauth = ''

    f = open(filename, 'r')
    content = f.readlines()
    f.close()

    for line in content:
        if line[0] == '#': continue
        if line == os.linesep: continue
        line = line.strip(' \n\r')
        line = line.split('=')
        if line[0] == 'name': _name = line[1]
        if line[0] == 'channel': _channel = line[1]
        if line[0] == 'oauth': _oauth = line[1]

    return _name, _channel, _oauth

def get_config():
    """
    Collects variables used to connect to the chat
    """
    global NAME
    global CHANNEL
    global OAUTH
    global INPUT_ENABLE
    global TIMESTAMPS_ENABLE

    _cli_var = sys.argv[1:]
    _name = ''
    _channel = ''
    _oauth = ''
    _config = ''

    if '-h' in _cli_var or '--help' in _cli_var:
        display_help()
        sys.exit()

    if '--config' in _cli_var:
        ind = _cli_var.index('--config')
        _config = _cli_var[ind + 1]
    else:
        if os.name == 'posix':
            _usr_dir = os.path.expanduser("~")
            if os.path.exists(_usr_dir + '/.config/tccli/config'):
                _config = _usr_dir + '/.config/tccli/config'
            elif os.path.exists(_usr_dir + '/.tcclirc'):
                _config = _usr_dir + '/.tcclirc'
        elif os.name == 'nt':
            _config = os.getcwd() + '\\config.ini'

    if '--spectate' in _cli_var:
        ind = _cli_var.index('--spectate')
        INPUT_ENABLE = False

    if '--timestamps' in _cli_var:
        ind = _cli_var.index('--timestamps')
        TIMESTAMPS_ENABLE = True

    if _config != '':
        _name, _channel, _oauth = parse_cfg(_config)

    if '-n' in _cli_var:
        ind = _cli_var.index('-n')
        _name = _cli_var[ind + 1]

    if '-c' in _cli_var:
        ind = _cli_var.index('-c')
        arg = _cli_var[ind + 1]
        if arg[0] == '#':
            _channel = arg
        else: _channel = '#' + arg

    if '-o' in _cli_var:
        ind = _cli_var.index('-o')
        _oauth = _cli_var[ind + 1]

    if _name == '' or _channel == '' or _oauth == '':
        sys.exit('[ERROR] Wrong configuration data (-h or --help for help)')
    else:
        NAME = _name
        CHANNEL = _channel
        OAUTH = _oauth

def check_config(H, P, N, O, C):
    """
    Quick check if the config data makes sense
    """
    if H != 'irc.twitch.tv': return False
    if not isinstance(P, int): return False
    if P != 6697: return False
    if not isinstance(N, str): return False
    if not isinstance(O, str): return False
    if O[:6] != 'oauth:': return False
    if C[0] != '#': return False
    return True

def get_usr(msg):
    """
    Gets user from message string
    """
    end = msg.find('!')
    return msg[1:end]

def get_msg(msg):
    """
    Gets message from message string
    """
    index = msg.find(CHANNEL) + len(CHANNEL) + 2
    return msg[index:]

def display_message(msg_str):
    """
    Handler for outputting messages
    """
    global TIMESTAMPS_ENABLE
    message = get_usr(msg_str) + ": " + get_msg(msg_str)

    if TIMESTAMPS_ENABLE:
        print('[{}] {}'.format(datetime.now().strftime('%H:%M:%S'), message))
    else: print(message)


def main():
    get_config()
    _running = True
    _connection = None

    if check_config(HOST, PORT, NAME, OAUTH, CHANNEL):
        _connection = IrcClient()
        _connection.add_handler(display_message)
        _connection.connect(HOST, PORT, NAME, OAUTH, CHANNEL)
    else:
        sys.exit('[ERROR] Wrong format of configuration data (-h or --help for help)')

    while _running:
        command: str = input()
        if command == '!quit' or command == '!exit':
            _connection.disconnect()
            _running = False
        else:
            if INPUT_ENABLE: _connection.send_message(command)

if __name__ == "__main__":
    main()
