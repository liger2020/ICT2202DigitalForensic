# **ICT2202DigitalForensic**

A secure blockchain-based chain of custody framework alongside a case management system in which a private lightweight blockchain in a case management system that allows authenticated participants to access off-chain evidence stored on a credible storage medium. **(???)**

**\<Brief Introduction\>**

![Blockchain Image][blockchain]

## Table of Contents
--------------------
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [User Guide](#user-guide)
- [Documentation](#documentation)

## Getting Started
------------------
To clone the git, type:

`git clone https://github.com/liger2020/ICT2202DigitalForensic.git`

Navigate into the project folder:

`cd ICT2202DigitalForensic`

The project contains both "server" and "client" side codes.

##### Server
For server, you can navigate into the directory:

`cd ICT2202_Blockchain`

##### Client
For client, you can navigate into the directory:

`cd ICT2202_Blockchain_Client`

#### Virtual Environment
Virtual environment may be created to run if preferred:

`python3 -m venv .venv`

You may require python3.8-venv:

`sudo apt install python3.8-venv`

#### Installing Dependencies
Install dependencies using the requirements.txt:

`pip install -r requirements.txt`

#### Running
Run `python3 run.py` to start the server/client.

## Configuration
----------------

You should configure the IP addresses of the server and client for the script to communicate. In "app/\_\_init\_\_.py" the addresses can be edited as required. This must be edited **before running the script for the first time** or **creation of database "app.db"**. You may delete "app.db" and run again.

For example, the following configuration is with 1 server (*10.6.0.3*) and 2 clients (*10.6.0.4*, *10.6.0.5*):

```python
# Init the Peers Table db with values (hardcode)
@event.listens_for(Peers.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
    init_list = [
        ("10.6.0.3", 5000, "server"),
        ("10.6.0.4", 5000, "client"),
        ("10.6.0.5", 5000, "client"),
    ]
    for (ip_address, port, server_type) in init_list:
        db.session.add(Peers(ip_address=ip_address, port=port, server_type=server_type))
    db.session.commit()
```

## User Guide
-------------
**\<User guide\>**

## Documentation
----------------
The documentation is available in /docs directory.

The documentation is also available in [GitHub Pages][documentation].


[documentation]: https://liger2020.github.io/ICT2202DigitalForensic/

[blockchain]: https://liger2020.github.io/ICT2202DigitalForensic/images/blockchain.png
