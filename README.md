# **ICT2202 Digital Forensic**

A private blockchain-based chain of custody framework and case management web portal designed to reduce the likelihood of an insider attack within the system.

![Case Management][case-management]

![Block Content][blockchain-content]

## Table of Contents
--------------------
- [Getting Started](#getting-started)
  - [Virtual Environment](#virtual-environment)
  - [Installing Dependencies](#installing-dependencies)
  - [Running](#running)
- [Configuration](#configuration)
- [User Guide](#user-guide)
- [Documentation](#documentation)

## Getting Started
------------------
To clone the git, type:

```bash
git clone https://github.com/liger2020/ICT2202DigitalForensic.git
```

Navigate into the project folder:

```bash
cd ICT2202DigitalForensic
```

The project contains both "server" and "client" side codes.

<br>

##### **Server**
For server, you can navigate into the directory:

```bash
cd ICT2202_Blockchain
```

##### **Client**
For client, you can navigate into the directory:

```bash
cd ICT2202_Blockchain_Client
```

#### Virtual Environment
Virtual environment may be created to run if preferred:

```bash
python3 -m venv .venv
```

You may require python3.8-venv:

```bash
sudo apt install python3.8-venv
```

#### Installing Dependencies
Install dependencies using the requirements.txt:

```bash
pip3 install -r requirements.txt
```

#### Running
To start the server/client:
```bash
python3 run.py
```

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
**\<Type User guide\>**

```json
{
    "case_id": "1",
    "meta_data": {
        "File_Hash": "F8659EDDABAA5675263BC9D11924B291A3F8AA6F6F9FC62513EAA11EF05262A4",
        "File_Name": "TestFile",
        "Modified_Date": "3/11/2021 11:30:20 pm",
        "Creation_Date": "3/11/2021 11:30:20 pm"
    },
    "log": {
        "Action": "Upload",
        "Username": [
            "TestUser"
        ]
    }
}
```

Block

| id  | block_number | previous_block_hash | meta_data | log | timestamp | block_hash | status |
| :-: | :----------: | :-----------------: | :-------: | :-: | :-------: | :--------: | :----: |
| 1 | 0 |   | {"File_Hash": "F8659EDDABAA5675263BC9D11924B291A3F8AA6F6F9FC62513EAA11EF05262A4", "File_Name": "TestFile", "Modified_Date": "3/11/2021 11:30:20 pm", "Creation_Date": "3/11/2021 11:30:20 pm"}  | {"Action": "Upload", "Username": \["TestUser"\]}  | 2021-11-04 17:08:18.430813  | 7db76249a6170b519fad6e5735d97cc5748b14fe14cebd883e72a404c9a05f47  | 1  |

## Documentation
----------------
The documentation is available in /docs directory.

The documentation is also available in [GitHub Pages][documentation].


[documentation]: https://liger2020.github.io/ICT2202DigitalForensic/

[case-management]: https://liger2020.github.io/ICT2202DigitalForensic/images/blockchain-case-management-server.png

[blockchain-content]: https://liger2020.github.io/ICT2202DigitalForensic/images/block-content.png

[^note]: This is an assignment for ICT2202.
