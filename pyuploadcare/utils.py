# coding: utf-8
import urlparse


def urljoin(base_url, path_and_query):
    """Returns API's URL path.

    Usage example::

        >>> urljoin('https://api.uploadcare.com/?fizz=buzz', '/files/?a=1&b=1')
        'https://api.uploadcare.com/files/?fizz=buzz&a=1&b=1'
        >>> urljoin('https://uploadcare.com/api/?fizz=buzz', '/files/?a=1')
        'https://uploadcare.com/api/files/?fizz=buzz&a=1'

    """
    base_url_parts = urlparse.urlsplit(base_url)
    path_and_query_parts = urlparse.urlsplit(path_and_query)

    parts_of_combined_path = filter(
        None,
        base_url_parts.path.split('/') + path_and_query_parts.path.split('/')
    )
    if parts_of_combined_path:
        combined_path = '/{0}/'.format('/'.join(parts_of_combined_path))
    else:
        combined_path = '/'

    if base_url_parts.query and path_and_query_parts.query:
        combined_query = '{0}&{1}'.format(base_url_parts.query,
                                          path_and_query_parts.query)
    else:
        combined_query = base_url_parts.query or path_and_query_parts.query

    return urlparse.urlunsplit((
        base_url_parts.scheme,
        base_url_parts.netloc,
        combined_path,
        combined_query,
        None
    ))
