from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from constructs import Construct


class Part0Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        retention_days = int(self.node.try_get_context("retention_days") or 1)
        model_id = self.node.try_get_context("model_id") or "REPLACE_WITH_INFERENCE_PROFILE_ID"

        # WORM audit bucket. Object Lock can only be enabled at creation; versioning is required.
        bucket = s3.Bucket(
            self,
            "AuditWorm",
            object_lock_enabled=True,
            object_lock_default_retention=s3.ObjectLockRetention.compliance(Duration.days(retention_days)),
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        env = {"AUDIT_BUCKET": bucket.bucket_name, "RETENTION_DAYS": str(retention_days), "MODEL_ID": model_id}
        code = lambda_.Code.from_asset("src")  # stdlib + boto3 only, so no bundling or arch issues

        commit_fn = lambda_.Function(
            self, "CommitFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="mechgov.handler.commit_handler",
            code=code, timeout=Duration.seconds(60), memory_size=512, environment=env,
        )
        reveal_fn = lambda_.Function(
            self, "RevealFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="mechgov.handler.reveal_handler",
            code=code, timeout=Duration.seconds(30), memory_size=256, environment=env,
        )

        # Least privilege: write-only to its own prefix. No delete, no retention bypass.
        commit_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:PutObject", "s3:PutObjectRetention"],
            resources=[bucket.arn_for_objects("commits/*")],
        ))
        reveal_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:PutObject", "s3:PutObjectRetention"],
            resources=[bucket.arn_for_objects("reveals/*")],
        ))
        reveal_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[bucket.arn_for_objects("commits/*")],
        ))
        commit_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                f"arn:aws:bedrock:*:{self.account}:inference-profile/*",
            ],
        ))

        CfnOutput(self, "AuditBucketName", value=bucket.bucket_name)
        CfnOutput(self, "CommitFunctionName", value=commit_fn.function_name)
        CfnOutput(self, "RevealFunctionName", value=reveal_fn.function_name)
