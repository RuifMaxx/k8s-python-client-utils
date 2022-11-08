import subprocess
import time


from kubernetes import client, config
def deployment_exists(name, namespace):
    config.load_kube_config()
    v1 = client.AppsV1Api()
    resp = v1.list_namespaced_deployment(namespace=namespace)
    for i in resp.items:
        if i.metadata.name == name:
            return True
    return False

def service_exists(name, namespace):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    resp = v1.list_namespaced_service(namespace=namespace)
    for i in resp.items:
        if i.metadata.name == name:
            return True
    return False


# 能用就行
def check_pod_node(pod_str = "redis-deployment"):
    '''
    返回集群中相关pod对应node的数量
    '''
    par_dict = {}
    config.load_kube_config()
    api_read = client.CoreV1Api()
    ret = api_read.list_pod_for_all_namespaces(watch=False)
    replicas_137 = 0
    replicas_234 = 0
    replicas_192 = 0
    for itm in ret.items:
        if pod_str in itm.metadata.name:
            if "192.168.0.137" in itm.spec.node_name:
                replicas_137 += 1
            if "192.168.0.234" in itm.spec.node_name:
                replicas_234 += 1
            if "192.168.0.192" in itm.spec.node_name:
                replicas_192 += 1

    par_dict["192.168.0.137"] = replicas_137
    par_dict["192.168.0.234"] = replicas_234
    par_dict["192.168.0.192"] = replicas_192

    return par_dict

def wait_name_space_deployments_ready(namespace:str, args:list):
    # 是否所有的Pod都Ready
    # Deployment  ——> ReplicaSet ——> Pods
    api = client.AppsV1Api()
    if_ready = True
    while True:
        time.sleep(1)
        for itm in args:
            info = api.read_namespaced_deployment(itm, namespace=namespace)
            if info.status.ready_replicas != info.spec.replicas:
                if_ready = False
        if if_ready:
            break
