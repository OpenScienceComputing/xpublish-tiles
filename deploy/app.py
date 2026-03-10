import os

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct


class FluxTilesStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=0)

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        image = ecr_assets.DockerImageAsset(
            self, "Image", directory=os.path.dirname(__file__)
        )

        # DNS validation: CDK will pause and display the CNAME record to add in Cloudflare
        cert = acm.Certificate(
            self,
            "Cert",
            domain_name="tiles.openscicomp.io",
            validation=acm.CertificateValidation.from_dns(),
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "Service",
            cluster=cluster,
            cpu=4096,
            memory_limit_mib=16384,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(image),
                container_port=8080,
            ),
            certificate=cert,
            redirect_http=True,
            public_load_balancer=True,
            assign_public_ip=True,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        service.target_group.configure_health_check(path="/health")

        CfnOutput(
            self,
            "AlbDns",
            value=service.load_balancer.load_balancer_dns_name,
            description="Add a CNAME record in Cloudflare: tiles.openscicomp.io -> this value",
        )


app = cdk.App()
FluxTilesStack(
    app,
    "FluxTilesStack",
    env=cdk.Environment(account="153379367922", region="us-west-2"),
)
app.synth()
