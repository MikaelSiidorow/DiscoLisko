## Finding bridge IP

1. `sudo apt install nmap`
2. `ifconfig` --> find your local IP ie. `inet 192.168.1.10  netmask 255.255.255.0`
3. `sudo nmap -sn 192.168.1.0/24` or corresponding ip if different in step 2

## Running the script

1. `sudo apt install libportaudio2` (required for sounddevice)
2. `python -m venv env`
3. `pip install -r requirements.txt`
4. `./main.py` or `python main.py`
