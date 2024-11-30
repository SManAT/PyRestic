# PyRestic

A python Wrapper for Restic Backup

## Prepare

First, load from [https://restic.net/](https://restic.net/) the binary for yout OS. I've been tested it only on WIN!  
Copy it to the _/src/bin/_ folder.

After that, run pip to get all required modules for python.

## Usage

```
python src\restic.py
```

You can use different profiles to do different backups. Manage your profiles with

```
python src\restic.py --profiles
```

What to include or exclude from backups and the important password for encryption (DON'T lose it!)  
is stored in config.yml after it was initialized. It will look like this

```yml
default:
  snapshots: 4
  password: hdf5rvg3rvgfe563gr765gc376zzgrg3r
  storage: \\192.168.1.10\BACKUP_Restic\
  include:
    - C:\Users\goofy\Pictures
  exclude:
    - Thumbs.db
    - "*.iso"
    - AI\**
```
