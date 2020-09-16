Can Control Center
======================
The CCCenter is a console based ui for sending and receiving can messages on raspberry pi or similar.
It enables you to define, send and read can messages in one view.
Known can messages are parsed into human readable format.

needed libraries:
- urwid
- python-can

These can be installed automatically via cccenter.sh

run with 

```bash
# ./cccenter.sh 
```

This will create a virtual python environment and install the libraries- if not already existent.
After, it will start the Can Control Center.

For testing, you can use vsocketcan.sh to create a virtual can. You may need can-utils package.

```bash
# ./vsocketcan.sh
# ./cccenter.sh vcan0
```


Adding Message Types
--------------------
for sending messages you will need to define a message type. This is done by using the order add

usage: add messagename messageid parameter parameter
 Parameters are defined as \[name\]:\[type\]  
 Possible types are
    - c for char
    - i8 for 8 bit integer
    - i16 for 16 bit integer
    - i32 for 32 bit integer

Hint: All numbers are written decimal!

Example:

```
 add move 32 destination:i32 speed:i16 acceleration:i16
```

New message types are automatically stored in the file canorders.json and will be usable for later can sessions.


Sending Messages
----------------
Sending messages can now be done with the order send.

```
 send move 1000000 300 200
```


Logging externally
------------------
Since it is currently not possible to scroll through the log, I decided to enable the cccenter to write logs into a file.
Therefore just type

```
file logout.txt
```

or any filename/path you want to log to. To disable logging, type

```
file off
```

Help
----
More info on existing orders can be found by typing

```
help
```

or for more specific help by appending the order which you need help for.

```
help send
```



