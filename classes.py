from kubernetes import client
import util, time, subprocess 
import numpy as np

class Deployment:
    def __init__(self, replicas_:int, cpu: str, mem: str,  name_:str, 
            containers_name = 'redis', image = 'redis',app = 'redis', 
            image_pull_policy='IfNotPresent' ,container_port=6379,
            node = None, namespace='default'):
        self.name = name_
        self.cpu = cpu
        self.mem = mem
        self.replicas = replicas_
        self.containers_name = containers_name
        self.image = image
        self.app = app
        self.image_pull_policy = image_pull_policy
        self.container_port = container_port
        self.node = node
        self.resp = None
        self.deployment_obj = None
        self.namespace = namespace
        self.create_deployment()

    def create_deployment(self):
        api = client.AppsV1Api()
        if_exists = util.deployment_exists(name=self.name,namespace = self.namespace)
        if if_exists:
            api.delete_namespaced_deployment(name=self.name,namespace = self.namespace)
        # Configureate Pod template container
        container = client.V1Container(
            name = self.containers_name,
            image = self.image,
            image_pull_policy = self.image_pull_policy,
            ports=[client.V1ContainerPort(container_port = self.container_port)],
            resources=client.V1ResourceRequirements(
                requests={"cpu": self.cpu, "memory": self.mem},
                limits={"cpu": self.cpu, "memory": self.mem},
            ),
        )

        # Create and configure a spec section
        if self.node:
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": self.app}),
                spec=client.V1PodSpec(containers=[container], node_name=self.node),
            )
        else:
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": self.app}),
                spec=client.V1PodSpec(containers=[container]),
            )

        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=self.replicas, template=template, selector={
                "matchLabels":
                {"app": self.app}})

        # Instantiate the deployment object
        self.deployment_obj = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=self.name),
            spec=spec,
        )


        # Create deployement
        self.resp = api.create_namespaced_deployment(
            body=self.deployment_obj, namespace=self.namespace
        )
        
    def update_deployment(self, cpu:str, num:int ,mem:str):
        api = client.AppsV1Api()
        deployment_name = self.deployment_obj.metadata.name
        # Update container image
        self.deployment_obj.spec.template.spec.containers[0].resources = \
        client.V1ResourceRequirements(
                requests={"cpu": cpu, "memory": mem},
                limits={"cpu": cpu, "memory": mem},
            )
        # 这里必须是integer
        self.deployment_obj.spec.replicas = num

        # patch the deployment
        api.patch_namespaced_deployment(
            name=deployment_name, namespace=self.namespace, body=self.deployment_obj
        )
        self.resp = api.read_namespaced_deployment(name=deployment_name,namespace=self.namespace)
        cpu_ = self.resp.spec.template.spec.containers[0].resources.requests["cpu"]
        mem_ = self.resp.spec.template.spec.containers[0].resources.requests["memory"]
        replicas = self.resp.spec.replicas
        self.cpu = cpu_
        self.mem = mem_
        self.replicas = replicas

    def restart_deployment(self):
        api = client.AppsV1Api()
        api.delete_namespaced_deployment(self.name, namespace=self.namespace)
        time.sleep(5)
        api.create_namespaced_deployment(namespace=self.namespace, body=self.deployment_obj)
        time.sleep(5)
        subprocess.run("kubectl delete pods --field-selector status.phase=Failed",
            shell=True,stdout=subprocess.PIPE)
        time.sleep(5)


class Service:

    def __init__(self, name_:str, app = 'redis', port=6379, target_port=6379,
             type_ = "NodePort",node_port=None, namespace='default'):
        self.name = name_
        self.port = port
        self.target_port = target_port
        self.node_port = node_port
        self.app = app
        self.type = type_
        self.resp = None
        self.namespace = namespace
        self.service_obj = None
        self.create_svc()

    def create_svc(self):
        api = client.CoreV1Api()
        if_exists = util.service_exists(name=self.name,namespace=self.namespace)
        if if_exists:
            api.delete_namespaced_service(name=self.name,namespace=self.namespace)
        service = client.V1Service()
        service.api_version = "v1"
        service.kind = "Service"
        service.metadata = client.V1ObjectMeta(name=self.name)
        spec = client.V1ServiceSpec()
        spec.selector = {"app": self.app}
        spec.ports = [client.V1ServicePort(protocol="TCP", port=self.port, target_port=self.target_port)]
        spec.type = self.type
        service.spec = spec
        self.service_obj = service
        self.resp = api.create_namespaced_service(namespace=self.namespace, body=self.service_obj)
        

class Filter:
    def __init__(self,dim,lens:int):
        self.lens = lens
        self.array = np.zeros((dim,1))
        self.flag = 0
        self.avg_out = np.zeros((dim,1))

    def update(self,input_:np.ndarray):
        dims = self.array.shape[0]
        if self.flag == 0:
            self.flag =1
            self.array = input_
        else:
            self.array = np.hstack((self.array,input_))
        if self.array.shape[1] > self.lens:
            self.array = np.delete(self.array,0,1)
        
        for i in range(dims):
            self.avg_out[i] = np.mean(self.array[i])
        
        return self.avg_out
