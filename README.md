# 内网集群如何配置K8S集群环境

背景：内网集群可以访问百度，但几乎无法访问docker hub和清华的docker源。希望配置VSCode的远程SSH和K8S集群。

## VSCode的远程SSH

我们有一台公网服务器，ip为ip-a，内网ip分别是：192.168.0.1，192.168.0.2，192.168.0.3。Master节点我们选择为192.168.0.1。Node节点为192.168.0.2，192.168.0.3。
假设ip-a安全组已开放的端口号为12222。那么在192.168.0.1服务器上运行即可打开持久的SSH隧道。

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

然后直接点击Remote中的Jumpk8s即可。如果连不上记得运行ssh-keygen.exe并且清理known_hosts中过期的指纹信息。如果需要免密登录，需要把id_rsa.pub中的公钥添加到被访问的服务器的.ssh/authorized_keys文件中
