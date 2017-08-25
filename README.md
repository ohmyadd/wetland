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
* requests

## Setup and Configuration
1. Copy wetland.cfg.default to wetland.cfg
2. Generate keys used by ssh server
  * run `mkdir keys; cd keys`
  * run `ssh-keygen -t rsa`, and put them in `./`
  * run `ssh-keygen -t dsa`, and put them in `./`
  * Remember that Wetland and sshd container should use the same keys.
3. Configure the output plugins
  * enable or disable in [output] section
  * Edit the url of incoming robots when using bearychat
  * Edit user、pwd... when using email
4. Configure the banner of ssh server
  * Edit banner in wetland.cfg
  * It should be same with the ssh banner of sshd contaniner
5. Install python requirements
  * run `pip install -r requirements`
6. Install p0f if you want
  * run `git clone https://github.com/p0f/p0f`
  * run `cd p0f`
  * run `./build.sh`
  * Edit [p0fp0f] section in wetland.cfg
  * if you dont need p0f, just disable p0f in [output] section
7. Install docker
  * install docker with docs in [www.docker.com](www.docker.com)
  * run `docker search sshd`, then choose a image running sshd
  * run `docker run -d --name sshd sshd_image_name`
  * run `docker inspect sshd`, then edit docker ip address and port in wetland.cfg
  * sshd's ssh port should be same with wetland's
  * delete and replace sshd container sometimes if you want

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
  * finally clean up the nat table of iptables or just reboot
4. View logs
  * run `python util/clearlog.py -p log` will clear logs that only have pwd.log, and pwds will write into -l file, default ./pwd.txt 
  * just use playlog.py in util

## TODO
* wetland dockerize
* create sshd docker image realistic
* automate create sshd docker


* add watchdog
* take use of bearychat incoming outgoing
* distribute log system & support hpfeeds
