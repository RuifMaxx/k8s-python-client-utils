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

**搭建k8s集群的服务器需要没有被使用过，是刚刚装好Ubuntu 20.04 server版本系统的纯净服务器**

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

安装脚本我在 [github.com/easzlab/kubeasz/](github.com/easzlab/kubeasz/)的基础上修改。 版本为kubeasz 3.3.1，k8s为1.24。安装脚本和镜像文件下载地址为：

[https://pan.baidu.com/s/1NGm1tE7ffVWEKQ3gE0Ergg?pwd=kwkx](https://pan.baidu.com/s/1NGm1tE7ffVWEKQ3gE0Ergg?pwd=kwkx)

将 ezdown 文件和 cache文件下的文件，放在根目录或者其他你便于操作的地方。将文件夹根目录下的其他文件，包括：

```
calico_v3.19.4.tar  dashboard_v2.5.1.tar  k8s-dns-node-cache_1.21.1.tar  metrics-scraper_v1.0.8.tar  pause_3.7.tar
coredns_1.9.3.tar   docker-20.10.16.tgz   kubeasz_3.3.1.tar              metrics-server_v0.5.2.tar   registry-2.tar
```

放到/etc/kubeasz/down下，并在其他位置进行备份。由于此时没有这个目录，需要运行

```
mkdir -p /etc/kubeasz/down
```

### 提取cache文件夹中的镜像

采用如下命令提取cache文件夹中的镜像。如有必要，则按照ezdown脚本中的规则进行docker tag 镜像重命名打标签

```
docker load -i "<镜像名>.tar"
```

如果需要保存镜像则

```
docker save -o "/root/cache/easzlab_kubeasz-ext-bin_1.2.0" "easzlab/kubeasz-ext-bin:1.2.0"
```

处理容器镜像（更多关于ezdown的参数，运行./ezdown 查看）

```
# 国内环境
./ezdown -D
# 海外环境
#./ezdown -D -m standard
```

这个命令运行到一半可能会清空/etc/kubeasz/down中的文件，提示在下载镜像，那么需要把备份的

```
calico_v3.19.4.tar  dashboard_v2.5.1.tar  k8s-dns-node-cache_1.21.1.tar  metrics-scraper_v1.0.8.tar  pause_3.7.tar
coredns_1.9.3.tar   docker-20.10.16.tgz   kubeasz_3.3.1.tar              metrics-server_v0.5.2.tar   registry-2.tar
```

复制到/etc/kubeasz/down下。

创建集群配置实例

```
# 容器化运行kubeasz
./ezdown -S

# 创建新集群 k8s-01
docker exec -it kubeasz ezctl new k8s-01
2021-01-19 10:48:23 DEBUG generate custom cluster files in /etc/kubeasz/clusters/k8s-01
2021-01-19 10:48:23 DEBUG set version of common plugins
2021-01-19 10:48:23 DEBUG cluster k8s-01: files successfully created.
2021-01-19 10:48:23 INFO next steps 1: to config '/etc/kubeasz/clusters/k8s-01/hosts'
2021-01-19 10:48:23 INFO next steps 2: to config '/etc/kubeasz/clusters/k8s-01/config.yml'
```

修改'/etc/kubeasz/clusters/k8s-01/hosts'

```
vim /etc/kubeasz/clusters/k8s-01/hosts

# 修改为
# 'etcd' cluster should have odd member(s) (1,3,5,...)
[etcd]
192.168.0.1
192.168.0.2
192.168.0.3

# master node(s)
[kube_master]
192.168.0.1

# work node(s)
[kube_node]
192.168.0.2
192.168.0.3

```

开始安装

```
#建议配置命令alias，方便执行
echo "alias dk='docker exec -it kubeasz'" >> /root/.bashrc
source /root/.bashrc

# 一键安装，等价于执行docker exec -it kubeasz ezctl setup k8s-01 all
dk ezctl setup k8s-01 all

# 或者分步安装，具体使用 dk ezctl help setup 查看分步安装帮助信息
# dk ezctl setup k8s-01 01
# dk ezctl setup k8s-01 02
# dk ezctl setup k8s-01 03
# dk ezctl setup k8s-01 04
...

```
断开SSH连接再重新连接，可以发现安装成功

```
$ kubectl version         # 验证集群版本     
$ kubectl get node        # 验证节点就绪 (Ready) 状态
$ kubectl get pod -A      # 验证集群pod状态，默认已安装网络插件、coredns、metrics-server等
$ kubectl get svc -A      # 验证集群服务状态
```

```
root@hecs:~# kubectl get node
NAME            STATUS                     ROLES    AGE     VERSION
192.168.0.1   Ready,SchedulingDisabled   master   10m     v1.24.2
192.168.0.2   Ready                      node     9m45s   v1.24.2
192.168.0.3   Ready                      node     9m45s   v1.24.2
```
