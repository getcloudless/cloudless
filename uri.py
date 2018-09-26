# coding: utf-8

import uri
uri.URI("https://foo.bar")
mysite = uri.URI("https://foo.bar")
mysite.scheme
mysite.scheme.name
mysite.scheme == "https"
mysite.scheme == "http"
mysite = uri.URI("git+https://foo.bar")
mysite = uri.URI("git+https://foo.bar.baz/%%$")
mysite = uri.URI("git+https")
mysite = uri.URI("git+https:::::::")
mysite = uri.URI("git+https:::::\\\\//")
mysite = uri.URI(":git+https")
mysite.scheme
mysite.auth'
mysite.auth
mysite = uri.URI("git+https://foo.bar.baz/foo")
mysite = uri.URI("git+https://foo.bar.baz/foo")
mysite
mysite.schema
mysite.scheme
mysite.scheme.name
mysite.scheme == "git+https"
mysite.scheme == "git+https://github.com/getcloudless/example-apache@v1.0.0"
mysite.scheme == "git+https://github.com/getcloudless/example-apache@v1.0.0"
v1uri == "git+https://github.com/getcloudless/example-apache@v1.0.0"
v1uri = "git+https://github.com/getcloudless/example-apache@v1.0.0"
mysite = uri.URI(v1uri)
mysite.scheme
mysite.scheme.name
mysite.base
mysite.fragment
mysite.path
mysite.path.split("@")
"@".split(mysite.path)
str(mysite.path).split("@")
get_ipython().run_line_magic('save', '0-37 uri.py')
