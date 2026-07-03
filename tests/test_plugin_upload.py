"""Tests for the QGIS plugin upload helper."""

import builtins
import xmlrpc.client
import importlib
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

plugin_upload = importlib.import_module("wnt.plugin_upload")
PLUGIN_UPLOAD_PATH = str(Path(plugin_upload.__file__))


class FakeUploader:
    def __init__(self, result=None, error=None):
        self.result = result or (123, 456)
        self.error = error
        self.payload = None

    def upload(self, binary):
        self.payload = binary.data
        if self.error:
            raise self.error
        return self.result


class FakeServer:
    def __init__(self, uploader):
        self.plugin = uploader


def parameters():
    return SimpleNamespace(
        username="user",
        password="secret",
        server="plugins.example",
        port="443",
    )



def test_plugin_upload_imports_defusedxml_monkey_patch():
    assert plugin_upload.monkey_patch.__module__ == "defusedxml.xmlrpc"


def test_hide_password_masks_password():
    assert (
        plugin_upload.hide_password("https://user:secret@plugins.example:443/plugins/RPC2/")
        == "https://user:******@plugins.example:443/plugins/RPC2/"
    )


def test_main_uploads_binary_and_prints_ids(monkeypatch, tmp_path, capsys):
    archive = tmp_path / "plugin.zip"
    archive.write_bytes(b"zip-bytes")
    uploader = FakeUploader()

    captured = {}

    def server_proxy(address, **kwargs):
        captured["address"] = address
        captured.update(kwargs)
        return FakeServer(uploader)

    monkeypatch.setattr(plugin_upload.xmlrpc.client, "ServerProxy", server_proxy)

    plugin_upload.main(parameters(), [str(archive)])

    assert uploader.payload == b"zip-bytes"
    assert captured["address"] == "https://plugins.example:443/plugins/RPC2/"
    assert "secret" not in captured["address"]
    assert isinstance(captured["transport"], plugin_upload.AuthSafeTransport)
    assert captured["transport"].authorization.startswith("Basic ")
    output = capsys.readouterr().out
    assert "Connecting to: https://plugins.example:443/plugins/RPC2/ as user" in output
    assert "Plugin ID: 123" in output
    assert "Version ID: 456" in output


def test_main_reports_protocol_error(monkeypatch, tmp_path, capsys):
    archive = tmp_path / "plugin.zip"
    archive.write_bytes(b"zip-bytes")
    error = xmlrpc.client.ProtocolError(
        "https://user:secret@plugins.example",
        500,
        "nope",
        {"x": "y"},
    )
    uploader = FakeUploader(error=error)

    monkeypatch.setattr(plugin_upload.xmlrpc.client, "ServerProxy", lambda *args, **kwargs: FakeServer(uploader))

    plugin_upload.main(parameters(), [str(archive)])

    output = capsys.readouterr().out
    assert "A protocol error occurred" in output
    assert "https://user:******@plugins.example" in output
    assert "Error code: 500" in output


def test_main_reports_fault(monkeypatch, tmp_path, capsys):
    archive = tmp_path / "plugin.zip"
    archive.write_bytes(b"zip-bytes")
    uploader = FakeUploader(error=xmlrpc.client.Fault(7, "bad auth"))

    monkeypatch.setattr(plugin_upload.xmlrpc.client, "ServerProxy", lambda *args, **kwargs: FakeServer(uploader))

    plugin_upload.main(parameters(), [str(archive)])

    output = capsys.readouterr().out
    assert "A fault occurred" in output
    assert "Fault code: 7" in output
    assert "Fault string: bad auth" in output


def test_cli_requires_archive_argument(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["plugin_upload.py"])

    try:
        runpy.run_path(PLUGIN_UPLOAD_PATH, run_name="__main__")
    except SystemExit as exc:
        assert exc.code == 1

    output = capsys.readouterr().out
    assert "Please specify zip file." in output
    assert "Usage:" in output


def test_cli_uses_defaults_and_interactive_credentials(monkeypatch, tmp_path, capsys):
    archive = tmp_path / "plugin.zip"
    archive.write_bytes(b"zip-bytes")
    uploader = FakeUploader()

    monkeypatch.setattr(sys, "argv", ["plugin_upload.py", str(archive)])
    monkeypatch.setattr(plugin_upload.xmlrpc.client, "ServerProxy", lambda *args, **kwargs: FakeServer(uploader))
    monkeypatch.setattr(plugin_upload.getpass, "getuser", lambda: "default-user")
    monkeypatch.setattr(plugin_upload.getpass, "getpass", lambda: "typed-password")
    monkeypatch.setattr(builtins, "input", lambda: "")

    runpy.run_path(PLUGIN_UPLOAD_PATH, run_name="__main__")

    assert uploader.payload == b"zip-bytes"
    output = capsys.readouterr().out
    assert "Please enter user name [default-user]" in output
    assert "Plugin ID: 123" in output


def test_cli_accepts_typed_username(monkeypatch, tmp_path, capsys):
    archive = tmp_path / "plugin.zip"
    archive.write_bytes(b"zip-bytes")
    uploader = FakeUploader()

    monkeypatch.setattr(sys, "argv", ["plugin_upload.py", str(archive)])
    monkeypatch.setattr(plugin_upload.xmlrpc.client, "ServerProxy", lambda *args, **kwargs: FakeServer(uploader))
    monkeypatch.setattr(plugin_upload.getpass, "getuser", lambda: "default-user")
    monkeypatch.setattr(plugin_upload.getpass, "getpass", lambda: "typed-password")
    monkeypatch.setattr(builtins, "input", lambda: "typed-user")

    runpy.run_path(PLUGIN_UPLOAD_PATH, run_name="__main__")

    assert uploader.payload == b"zip-bytes"
    output = capsys.readouterr().out
    assert "https://plugins.qgis.org:443/plugins/RPC2/ as typed-user" in output
    assert "typed-password" not in output
