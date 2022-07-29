def test_data(tf):
    token = tf.data("aws_ssm_parameter", "token", name="workspace-token", path="/keys/")
    assert str(token) == "data.aws_ssm_parameter.token"
    assert (
        token._write()
        == 'data "aws_ssm_parameter" "token" {\n    name = "workspace-token"\n    path = "/keys/"\n}'
    )
    assert tf.data.group == "data"
    assert (
        str(tf.data.blocks)
        == "{'data.aws_ssm_parameter.token': data.aws_ssm_parameter.token}"
    )
    host = tf.data("aws_ssm_parameter", "host", name="workspace-host")
    assert str(host) == "data.aws_ssm_parameter.host"
    assert (
        host._write()
        == 'data "aws_ssm_parameter" "host" {\n    name = "workspace-host"\n}'
    )
    assert (
        str(tf.data.blocks)
        == "{'data.aws_ssm_parameter.token': data.aws_ssm_parameter.token, 'data.aws_ssm_parameter.host': data.aws_ssm_parameter.host}"
    )


def test_resources(tf):
    token = tf.resource(
        "aws_ssm_parameter", "token", name="workspace-token", path="/keys/"
    )
    assert str(token) == "resource.aws_ssm_parameter.token"
    assert (
        token._write()
        == 'resource "aws_ssm_parameter" "token" {\n    name = "workspace-token"\n    path = "/keys/"\n}'
    )
    assert tf.resource.group == "resource"
    assert (
        str(tf.resource.blocks)
        == "{'resource.aws_ssm_parameter.token': resource.aws_ssm_parameter.token}"
    )
    host = tf.resource("aws_ssm_parameter", "host", name="workspace-host")
    assert str(host) == "resource.aws_ssm_parameter.host"
    assert (
        host._write()
        == 'resource "aws_ssm_parameter" "host" {\n    name = "workspace-host"\n}'
    )
    assert (
        str(tf.resource.blocks)
        == "{'resource.aws_ssm_parameter.token': resource.aws_ssm_parameter.token, 'resource.aws_ssm_parameter.host': resource.aws_ssm_parameter.host}"
    )


def test_module(tf):
    test = tf.module("generic_resources", source="./generic_module")
    assert (
        test._write()
        == 'module "generic_resources" {\n    source = "./generic_module"\n}'
    )
    assert str(test) == "generic_resources"


def test_stacking_blocks(tf):
    host = tf.data("aws_ssm_parameter", "dbrx_host", name="dbrx_host")
    token = tf.data(
        "aws_ssm_parameter", "dbrx_token", name="dbrx_token", path=host["name"]
    )
    libs = tf.property("library", location="s3://bucket", entry_point="src.main")
    job = tf.resource(
        "databricks_job",
        "dbrx_job",
        library=libs,
        name="dbrx_job",
        host=host["name"],
        token=token["name"],
    )
    assert str(job) == "resource.databricks_job.dbrx_job"
    assert (
        job._write()
        == """resource "databricks_job" "dbrx_job" {\n    name    = "dbrx_job"\n    host    = data.aws_ssm_parameter.dbrx_host.name\n    token   = data.aws_ssm_parameter.dbrx_token.name\n    library {\n        location    = "s3://bucket"\n        entry_point = "src.main"\n    }\n}"""
    )


def test_meta_former_registry(tf):
    host = tf.data("aws_ssm_parameter", "dbrx_host", name="dbrx_host")
    token = tf.data(
        "aws_ssm_parameter", "dbrx_token", name="dbrx_token", path=host["name"]
    )
    libs = tf.property("library", location="s3://bucket", entry_point="src.main")
    job = tf.resource(
        "databricks_job",
        "dbrx_job",
        library=libs,
        name="dbrx_job",
        host=host["name"],
        token=token["name"],
    )
    assert set(tf.registry) == {
        "data.aws_ssm_parameter.dbrx_host",
        "data.aws_ssm_parameter.dbrx_token",
        "library",
        "resource.databricks_job.dbrx_job",
    }
