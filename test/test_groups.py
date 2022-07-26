from groups import Data, Resource, Module, Config


def test_data():
    token = Data("aws_ssm_parameter", "token", name="workspace-token", path="/keys/")
    assert str(token) == "%%data.aws_ssm_parameter.token"
    assert token._write() == 'data "aws_ssm_parameter" "token" {\n    name = "workspace-token"\n    path = "/keys/"\n}'
    assert Data.group == "data"
    assert str(Data.blocks) == "{'aws_ssm_parameter.token': data.aws_ssm_parameter.token}"
    host = Data("aws_ssm_parameter", "host", name="workspace-host")
    assert str(host) == "%%data.aws_ssm_parameter.host"
    assert host._write() == 'data "aws_ssm_parameter" "host" {\n    name = "workspace-host"\n}'
    assert str(Data.blocks) == "{'aws_ssm_parameter.token': data.aws_ssm_parameter.token, 'aws_ssm_parameter.host': data.aws_ssm_parameter.host}"


def test_resources():
    token = Resource("aws_ssm_parameter", "token", name="workspace-token", path="/keys/")
    assert str(token) == "%%resource.aws_ssm_parameter.token"
    assert token._write() == 'resource "aws_ssm_parameter" "token" {\n    name = "workspace-token"\n    path = "/keys/"\n}'
    assert Resource.group == "resource"
    assert str(Resource.blocks) == "{'aws_ssm_parameter.token': resource.aws_ssm_parameter.token}"
    host = Resource("aws_ssm_parameter", "host", name="workspace-host")
    assert str(host) == "%%resource.aws_ssm_parameter.host"
    assert host._write() == 'resource "aws_ssm_parameter" "host" {\n    name = "workspace-host"\n}'
    assert str(Resource.blocks) == "{'aws_ssm_parameter.token': resource.aws_ssm_parameter.token, 'aws_ssm_parameter.host': resource.aws_ssm_parameter.host}"


def test_module():
    test = Module("generic_resources", source="./generic_module")
    assert test._write() == '"module" "generic_resources" {\n    source = "./generic_module"\n}'
    assert str(test) == '%%module.generic_resources'


def test_stacking_groups():
    host = Data("aws_ssm_parameter", "dbrx_host", name="dbrx_host")
    token = Data("aws_ssm_parameter", "dbrx_token", name="dbrx_token", path=host["name"])
    libs = Config("library", location="s3://bucket", entry_point="src.main")
    job = Resource("databricks_job", "dbrx_job", config_blocks=[libs], name="dbrx_job", host=host["name"], token=token["name"])
    assert str(job) == '%%resource.databricks_job.dbrx_job'
    assert job._write() == 'resource "databricks_job" "dbrx_job" {\n    name  = "dbrx_job"\n    host  = data.aws_ssm_parameter.dbrx_host.name\n    token = data.aws_ssm_parameter.dbrx_token.name\n    library  {\n        location    = "s3://bucket"\n        entry_point = "src.main"\n    }\n}'
