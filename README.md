# 内网Ubuntu集群如何配置K8S集群环境和VSCode的远程SSH

背景：内网Ubuntu 20.04 集群可以访问百度，但几乎无法访问docker hub和清华的docker源。希望配置VSCode的远程SSH和K8S集群。

## VSCode的远程SSH

### SSH隧道

我们有一台公网服务器，ip为ip-a，内网Ubuntu 20.04 服务器的ip分别是：192.168.0.1，192.168.0.2，192.168.0.3。Master节点我们选择为192.168.0.1。Node节点为192.168.0.2，192.168.0.3。
假设ip-a安全组已开放的端口号为12222。那么在192.168.0.1服务器上运行下面的命令，即可打开持久的SSH隧道。

```
ssh -f -N -R <12222>:localhost:22 root@ip-a -o ServerAliveInterval=60 -o ServerAliveCountMax=3
```

则在ip-a服务器上运行
```
ssh -p 12222 localhost
```

即可访问内网服务器。

对于VSCode的远程SSH，在windows的C:\Users\<用户名>\.ssh\config中编辑：

```
Host Jumpsvc
  HostName ip-a
  User root

Host Jumpk8s
  HostName localhost
  Port 12222
  User root
  ProxyCommand ssh.exe -W %h:%p Jumpsvc
```

然后直接点击Remote中的Jumpk8s即可。如果连不上记得运行ssh-keygen.exe并且清理known_hosts中过期的指纹信息。如果需要免密登录，需要把id_rsa.pub中的公钥添加到被访问的服务器的.ssh/authorized_keys文件中。

### 卡在下载Vscode server

内网连接Vscode server缓慢。最方便的办法是找一个已经装好Vscode server的Ubuntu服务器（需要对应windows笔记本电脑的vscode版本）。把其中的~/.vscode-server/文件夹SCP到192.168.0.1的~/目录即可。由于我的电脑装了Ubuntu双系统，创建一个本地的Vscode server非常方便。

## K8S集群搭建
如果是公有云服务器，需要在节点之间放通内网的ICMP协议，保证用内网IP能互相PING通。

### SSH免密登陆
配置从部署节点能够ssh免密登陆所有节点，并且设置python软连接

```
cd  ~/.ssh

ssh-keygen -t rsa

#$IP为所有节点地址包括自身，按照提示输入yes 和root密码，ip地址为内网ip
ssh-copy-id $IP 

# 为每个节点设置python软链接
ssh $IP ln -s /usr/bin/python3 /usr/bin/python
```

### 下载安装脚本和镜像文件

安装脚本我在 [github.com/easzlab/kubeasz/](github.com/easzlab/kubeasz/)的基础上修改。 版本为kubeasz 3.3.1，k8s为1.24。安装脚本的下载地址为：

[]()

