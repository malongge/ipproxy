ssh ip_address -p port_num -l root

输入密码


ping -c3 www.baidu.com 测试可以访问外网

curl icanhazip.com 查看出口 ip


adsl-stop， adsl-start 重拨号

curl icanhazip.com 查看出口 ip 是否有变化

# 首先安装EPEL源
yum install -y epel-release

解决yum源 https 连接问题：
sudo sed -i "s/metalink=https/metalink=http/" /etc/yum.repos.d/epel.repo

更新 yum:
yum update -y

安装代理服务器
yum install -y tinyproxy

配置 tinyproxy:
vi /etc/tinyproxy/tinyproxy.conf

端口配置
Port 9999
Allow company_ip # 只允许公司爬虫使用代理

配置完重启 tinyproxy
systemctl enable tinyproxy.service
systemctl restart tinyproxy.service

配置防火墙
iptables -I INPUT -p tcp --dport 9999 -j ACCEPT

测试代理服务器:
curl icanhazip.com 获得出口 ip

在本地终端输入：
curl -x 27.156.119.48:9999 httpbin.org/get
能通过代理获取到网站信息，说明代理服务器生效了

安装 python 依赖环境
sudo yum install yum-utils
sudo yum-builddep python
curl -O https://www.python.org/ftp/python/3.6.8/Python-3.6.8.tgz
tar xf Python-3.6.8.tgz
cd Python-3.6.8
./configure
make
sudo make install

配置和测试 python 3 环境
python3 -V
将 python 3 作为默认的环境
vi /etc/profile.d/python.sh
alias python='/usr/local/bin/python3.6'
source /etc/profile.d/python.sh

pip3 install virtualenv


部署：
mkdir ~/venvs
cd ~/venvs
virtualenv ipproxy
source ipproxy/bin/activate

git clone source_code_address

cd source_code_project
pip install -r requrements.txt

安装配置 redis 服务
yum install redis

vi /etc/redis.conf
去掉行前的注释，并修改密码为所需的密码
requirepass 123456
maxclients 100
maxmemory 268435456

systemctl restart redis
增加开机启动
systemctl enable redis

测试 redis
redis-cli -h 0.0.0.0 -p 6379
0.0.0.0:6379> auth 123456
OK

拨号脚本运行
python adsl.py client1 # 一个 client 对应一个代理 ip 服务器，名字随意取，但必需不同

获取代理ip
http://127.0.0.1:9000/random

```json
{
"errcode": 0,
"proxy": "10.40.33.246:9999"
}

```


