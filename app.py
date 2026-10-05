#!/usr/bin/env python3
import aws_cdk as cdk

from infra.stack import Part0Stack

app = cdk.App()
Part0Stack(app, "MechGovPart0", env=cdk.Environment(region="eu-west-2"))
app.synth()
