# Album Maker

Create a HTML album and upload via SFTP to make available on hosting - used during lockdown home schooling to share the kids 
work with the teachers

# Installation

Something like this for Windows

```
  python -m venv venv
  venv\Scripts\activate.bat
  pip install -r requirements.txt
```

This for Linux
```
  python -m venv venv
  venv/bin/activate
  pip install -r requirements.txt
```

## maker.py

Command line script

## gmaker.py

Simple GUI

## Configuration

Defaults to a file called `~/.amaker/config.yml` but provide a different one.

