# Wetland
Wetland is a high interaction SSH honeypot，designed to log brute force attacks.What's more, wetland will log shell、scp、sftp、exec-command、direct-forward、reverse-forward interation performded by the attacker.

Wetland is based on python ssh module [paramiko](https://github.com/paramiko/paramiko/). And wetland runs as a multi-threading tcp server using SocketServer.

## Features
* Use docker to provide a real linux environment.
* All the password auth will redirect to docker.
* All the command will execute on docker.
* Save a copy of file when hacker uploads some files with SFTP.
* Extract and Save files from exec-log when hacker uoloads some files with SCP.
* Providing a playlog script to replay the [shell | exec | direct-forward | reverse-forward] kind of log.
* Advanced networking feature to spoof attackers IP address between wetland and docker(thanks to [honssh](https://github.com/tnich/honssh))
* Kinds of ways to report to you when wetland is touching by hacker, but now only email and bearychat.

## Requirements
* A linux system (tested on ubuntu)
* sshd images in docker (e.g rastasheep/ubuntu-sshd)
* python2.7
* paramiko
* yagmail
* IPy
* pygeoip
* requests

## Setup and Configuration
1. Copy wetland.cfg.default to wetland.cfg
2. Generate keys used by ssh server
  * cd into folder keys
  * run `ssh-keygen -t rsa`, and put them in `./`
  * run `ssh-keygen -t dsa`, and put them in `./`
  * Remember that Wetland and sshd container should use the same keys.
3. Download a geoip database used by pygeoip
  * [GeoLiteCity.dat.gz](http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz)
  * [GeoIP.dat.gz]( http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz)
  * Edit path to the db in wetland.cfg
4. Configure the output plugins
  * enable or disable in [output] section
  * Edit the url of incoming robots when using bearychat
  * Edit user、pwd... when using email
5. Configure the banner of ssh server
  * Edit banner in wetland.cfg
  * It should be same with that in sshd contaniner
6. Install python requirements
  * run `pip install -r requirements`

## Running
1. Run
  * run `nohup python main.py &`
2. Stop
  * run `netstat -autpn | grep 22`
  * then `kill pid_number`
  * ahaha
3. Clean
  * Maybe you should delete some iface created by networking module by hand.
  * run `ip link list`
  * then `ip link del dev wdxxxxxx`
  * finally clean up the nat table of iptables
4. Replay logs
  * just use playlog.py in util