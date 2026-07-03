#!/usr/bin/env python
"""Upload a plugin package to the QGIS plugin repository."""

import base64
import sys
import getpass
from defusedxml.xmlrpc import monkey_patch
# defusedxml monkey_patch() is applied before XML-RPC use.
import xmlrpc.client  # nosec B411
from optparse import OptionParser
from urllib.parse import urlsplit, urlunsplit

monkey_patch()

# Configuration
PROTOCOL = 'https'
SERVER = 'plugins.qgis.org'
PORT = '443'
ENDPOINT = '/plugins/RPC2/'
VERBOSE = False


class AuthSafeTransport(xmlrpc.client.SafeTransport):
    """HTTPS XML-RPC transport using Basic auth without credentials in the URL."""

    def __init__(self, username, password):
        super().__init__()
        token = f"{username}:{password}".encode("utf-8")
        self.authorization = "Basic " + base64.b64encode(token).decode("ascii")

    def send_headers(self, connection, headers):
        connection.putheader("Authorization", self.authorization)
        super().send_headers(connection, headers)


def main(parameters, arguments):
    """Upload one plugin archive using interactive credentials."""
    address = "{protocol}://{server}:{port}{endpoint}".format(
        protocol=PROTOCOL,
        server=parameters.server,
        port=parameters.port,
        endpoint=ENDPOINT)
    print("Connecting to: {} as {}".format(address, parameters.username))

    transport = AuthSafeTransport(parameters.username, parameters.password)
    server = xmlrpc.client.ServerProxy(address, transport=transport, verbose=VERBOSE)

    try:
        with open(arguments[0], 'rb') as handle:
            plugin_id, version_id = server.plugin.upload(
                xmlrpc.client.Binary(handle.read()))
        print("Plugin ID: %s" % plugin_id)
        print("Version ID: %s" % version_id)
    except xmlrpc.client.ProtocolError as err:
        print("A protocol error occurred")
        print("URL: %s" % hide_password(err.url, 0))
        print("HTTP/HTTPS headers: %s" % err.headers)
        print("Error code: %d" % err.errcode)
        print("Error message: %s" % err.errmsg)
    except xmlrpc.client.Fault as err:
        print("A fault occurred")
        print("Fault code: %d" % err.faultCode)
        print("Fault string: %s" % err.faultString)


def hide_password(url, start=6):
    """Return a URL with any user-info password masked."""
    del start  # Kept for compatibility with callers of the historical helper.
    parsed = urlsplit(url)
    if "@" not in parsed.netloc:
        return url
    userinfo, host = parsed.netloc.rsplit("@", 1)
    username, separator, password = userinfo.partition(":")
    if not separator:
        return url
    safe_netloc = f"{username}:{'*' * len(password)}@{host}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))


if __name__ == "__main__":
    parser = OptionParser(usage="%prog [options] plugin.zip")
    parser.add_option(
        "-u", "--username", dest="username",
        help="Username of plugin site", metavar="user")
    parser.add_option(
        "-p", "--port", dest="port",
        help="Server port to connect to", metavar="80")
    parser.add_option(
        "-s", "--server", dest="server",
        help="Specify server name", metavar="plugins.qgis.org")
    options, args = parser.parse_args()
    if len(args) != 1:
        print("Please specify zip file.\n")
        parser.print_help()
        sys.exit(1)
    if not options.server:
        options.server = SERVER
    if not options.port:
        options.port = PORT
    if not options.username:
        # interactive mode
        username = getpass.getuser()
        print("Please enter user name [%s] :" % username, end=' ')

        res = input()
        if res != "":
            options.username = res
        else:
            options.username = username
    # Never accept passwords through argv, where they are visible to other processes.
    options.password = getpass.getpass()
    main(options, args)
