"""
Repo fetcher.

Helpers to fetch a repo from git so the user can deploy from a git repo rather than a local file.
"""
import uri
from cloudless.util.exceptions import DisallowedOperationException

class RepoFetcher:
    def __init__(self):
        pass

    def fetch(self, uri):
        """
        Fetches a repository given a URI.
        """
        parsed_uri = uri.URI(uri)
        if not parsed_uri.scheme:
            raise DisallowedOperationException("")
        elif parsed_uri.scheme == "git+https":
            pass
        elif parsed_uri.scheme == "file":
            pass
        else:
            raise DisallowedOperationException("Unsupported scheme!  Supported schemes: blah")
# coding: utf-8
#
#import uri
#uri.URI("https://foo.bar")
#mysite = uri.URI("https://foo.bar")
#mysite.scheme
#mysite.scheme.name
#mysite.scheme == "https"
#mysite.scheme == "http"
#mysite = uri.URI("git+https://foo.bar")
#mysite = uri.URI("git+https://foo.bar.baz/%%$")
#mysite = uri.URI("git+https")
#mysite = uri.URI("git+https:::::::")
#mysite = uri.URI("git+https:::::\\\\//")
#mysite = uri.URI(":git+https")
#mysite.scheme
#mysite.auth'
#mysite.auth
#mysite = uri.URI("git+https://foo.bar.baz/foo")
#mysite = uri.URI("git+https://foo.bar.baz/foo")
#mysite
#mysite.schema
#mysite.scheme
#mysite.scheme.name
#mysite.scheme == "git+https"
#mysite.scheme == "git+https://github.com/getcloudless/example-apache@v1.0.0"
#mysite.scheme == "git+https://github.com/getcloudless/example-apache@v1.0.0"
#v1uri == "git+https://github.com/getcloudless/example-apache@v1.0.0"
#v1uri = "git+https://github.com/getcloudless/example-apache@v1.0.0"
#mysite = uri.URI(v1uri)
#mysite.scheme
#mysite.scheme.name
#mysite.base
#mysite.fragment
#mysite.path
#mysite.path.split("@")
#"@".split(mysite.path)
#str(mysite.path).split("@")
#get_ipython().run_line_magic('save', '0-37 uri.py')
