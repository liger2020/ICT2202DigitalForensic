# **ICT2202 Digital Forensic**

A private blockchain-based chain of custody framework and case management web portal designed to reduce the likelihood of an insider attack within the system.

This blockchain works together with the [case management webserver][case-mamangement-link].

![Case Management][case-management]

![Block Content][blockchain-content]

## Table of Contents
--------------------
- [Getting Started](#getting-started)
  - [Virtual Environment](#virtual-environment)
  - [Installing Dependencies](#installing-dependencies)
  - [Running](#running)
  - [Distribution](#distribution)
    - [Windows](#windows)
    - [Linux](#linux)
- [Configuration](#configuration)
  - [Init File](#init-file)
  - [Nodes File](#nodes-file)
- [User Guide](#user-guide)
  - [Adding Blocks](#adding-blocks)
  - [User's Assigned Case](#users-assigned-case)
  - [Case Information](#case-information)
  - [Filename and Hash Information](#filename-and-hash-information)
- [Docudwadmentation](#documentation)

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

### Virtual Environment
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

### Distribution
The runnable program is located at dist folder.

#### Windows

```bash
cd dist/windows
./run.exe
```

#### Linux

```bash
cd dist/linux
chmod +x ./run
./run
```

## Configuration
----------------
You should configure the IP addresses of the server and client for the script to communicate. This must be edited **before running the script for the first time** or **creation of database "app.db"**. You may delete "app.db" and run again.

### Init File
 In "app/\_\_init\_\_.py" the addresses can be edited as required.

For example, the following configuration is with 1 server (*10.6.0.3*) and 2 clients (*10.6.0.4*, *10.6.0.5*):

```python
# Init the Peers Table db with values (hardcode)
@event.listens_for(Peers.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
    init_list = []
    try:
        with open(os.path.join(BASE_DIR, 'nodes.txt'), "r") as f:
            lines = f.readlines()

            for line in lines:
                (ip, port, servertype) = line.strip().split(sep=',')
                init_list.append((ip, int(port), servertype))
    except FileNotFoundError:
        init_list = [
            ("10.6.0.2", 5000, "server"),
            ("10.6.0.3", 5000, "server"),
            ("10.6.0.4", 5000, "client"),
        ]

    for (ip_address, port, server_type) in init_list:
        db.session.add(Peers(ip_address=ip_address, port=port, server_type=server_type))
    db.session.commit()
```

### Nodes File
Add/Edit text file **"nodes.txt"** with **run** executable:

```
10.6.0.2,5000,server
10.6.0.3,5000,server
10.6.0.4,5000,client
```


## User Guide
-------------
After the case management webserver, which is interfacing with the blockchain, and nodes are installed and running, you are able to perform functions such as adding new case and evidence.

The following are the interactions with the web case management system.

### Adding Blocks
POST
/receiveblock

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

Block Table

| id  | block_number | previous_block_hash | meta_data | log | timestamp | block_hash | status |
| :-: | :----------: | :-----------------: | :-------: | :-: | :-------: | :--------: | :----: |
| 1 | 0 |   | {"File_Hash": "F8659EDDABAA5675263BC9D11924B291A3F8AA6F6F9FC62513EAA11EF05262A4", "File_Name": "TestFile", "Modified_Date": "3/11/2021 11:30:20 pm", "Creation_Date": "3/11/2021 11:30:20 pm"}  | {"Action": "Upload", "Username": \["TestUser"\]}  | 2021-11-04 17:08:18.430813  | 7db76249a6170b519fad6e5735d97cc5748b14fe14cebd883e72a404c9a05f47  | 1  |

### User's Assigned Case
POST
/usercase

```json
{
    "Username": "TestUser"
}
```

Output
```json
{
    "Cases": [
        "CaseID1",
        "CaseID2"
    ]
}
```

### Case Information
POST
/caseinfo

```json
{
    "case_id": "CaseID1"
}
```

Output
```json
{
    "Blocks": [
        {
            "block_hash": "63b6a68b0cfbd619bb4ebce846d07e584c545b228381047e4664f532732cfc81",
            "block_number": 0,
            "id": "CaseID1",
            "log": "{\"Action\": \"Upload\", \"Username\": [\"TestUser\"]}",
            "meta_data": "{\"File_Hash\": \"94635EBE6D95A4E97806C684F66C0C63E8A8FA0C22CF4817EB3A593F5B285ACC\", \"File_Name\": \"TestFile2\", \"Modified_Date\": \"2021-10-22 12:38:39.614467\", \"Creation_Date\": \"2021-10-22 12:38:39.614467\"}",
            "previous_block_hash": "",
            "status": true,
            "timestamp": "2021-11-05 20:11:52.673395"
        },
        {
            "block_hash": "346359dc0f769b7e8eeaf9981ea70e89d726b37e48e1cf79fdd802f9f7becf59",
            "block_number": 1,
            "id": "CaseID1",
            "log": "{\"Action\": \"Upload\", \"Username\": [\"TestUser\"]}",
            "meta_data": "{\"File_Hash\": \"F8659EDDABAA5675263BC9D11924B291A3F8AA6F6F9FC62513EAA11EF05262A4\", \"File_Name\": \"TestFile\", \"Modified_Date\": \"2021-10-22 12:38:39.614467\", \"Creation_Date\": \"2021-10-22 12:38:39.614467\"}",
            "previous_block_hash": "63b6a68b0cfbd619bb4ebce846d07e584c545b228381047e4664f532732cfc81",
            "status": true,
            "timestamp": "2021-11-05 20:13:04.264045"
        }
    ]
}
```

### Filename and Hash Information
POST
/filenameAndHash

```json
{
    "case_id": "CaseID1"
}
```

Output
```json
{
    "Files": [
        {
            "File_Hash": "F8659EDDABAA5675263BC9D11924B291A3F8AA6F6F9FC62513EAA11EF05262A4",
            "File_Name": "TestFile"
        },
        {
            "File_Hash": "94635EBE6D95A4E97806C684F66C0C63E8A8FA0C22CF4817EB3A593F5B285ACC",
            "File_Name": "TestFile2"
        }
    ]
}
```

## Documentation
----------------
The documentation is available in /docs directory.

The documentation is also available in [GitHub Pages][documentation].


[case-mamangement-link]: https://github.com/liger2020/ICT2202DigitalForensic_Duplicate_Local

[case-management]: https://liger2020.github.io/ICT2202DigitalForensic/images/blockchain-case-management-server.png "Case Management System"

[blockchain-content]: https://liger2020.github.io/ICT2202DigitalForensic/images/block-content.png "Contents of Blockchain"

[documentation]: https://liger2020.github.io/ICT2202DigitalForensic/

[^note]: This is an assignment for ICT2202.
