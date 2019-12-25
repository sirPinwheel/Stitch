# STITCH
Simple
Text
Interface
    for
Twitch
CHat

## Description
Stitch is a simple Python script that will connect to any Twitch channel, the idea behind it was to have an alternative to the in-browser chat. I admit it's a solution to the problem not many people have, but at the end of the day the more options the better.

## Installation
#### Requirements
``python3`` python interpreter<br>
``certifi`` python SSL module<br>

#### On Windows
- Clone the repo or download and unpack the zip<br>
- Get Python 3 from official website ``python.org``<br>
- Install python and pip3<br>
- Open command line and run ``pip3 install certifi``<br>

#### On Linux
- Clone the repo or download and unpack the zip<br>
- Get Python 3:
- For Ubuntu:<br>
``sudo apt update: sudo apt install python3 pip3``<br>
- For Arch/Manjaro:<br>
``sudo pacman -Syu python3 pip3``<br>
- Run``sudo pip3 install certifi``<br>
- Done, remember to add -x flag to the script:<br>
``sudo chmod +x stitch.py``<br>

## Usage
Now you can launch the script, it's supposed to be run from the command line (duh).<br>
Run it with ``-h`` for the following help message:<br>

```
stitch.py needs username, name of the channel and oauth token of that user
You can mix and match what's in the configuration file and what's
passed as the argument to the program, arguments will override data
from the configuration file.

usage:
    python3 stitch.py [option 1] <arg 1> [option 2] <arg 2>...
    ./stitch.py [option 1] <arg 1> [option 2] <arg 2>...

    If "--config <file>" is not provided the script will look for configuration
    file in this order in following locations:

    UNIX:                       WINDOWS:
    1) ~/.config/stitch/config   1) ./config.ini ("." meaning the folder containing stitch.py)
    2) ~/.stitchrc

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
    python3 stitch.py -n 'my_bot_account' -c 'my_epic_channel' -o 'oauth:abcdefghijkl...'
    python3 stitch.py --config './conf.cfg'
    python3 stitch.py --config './conf.cfg' -c 'my_epic_channel'
    python3 stitch.py --config './conf.cfg' --spectate

configuration file format:
    name=name_of_user
    channel=name_of_channel
    oauth=oauth:abcdefghijkl
```
