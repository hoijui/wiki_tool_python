"""MediaWiki API interaction functions."""
from typing import List, Iterable, Iterator, Dict, Any, Optional
from abc import ABC, abstractmethod

import click
import requests


class MediaWikiAPIError(click.ClickException):
    """MediaWiki API error."""

    pass


class CanNotDelete(MediaWikiAPIError):
    """Page can not be deleted."""

    pass


class MediaWikiAPI(ABC):
    """Base MediaWiki API class."""

    @abstractmethod
    def get_namespace_list(self) -> Iterable[int]:
        """Get iterable of all namespaces in wiki."""
        raise NotImplementedError()

    @abstractmethod
    def get_image_list(self, limit: int) -> Iterator[Dict[str, str]]:
        """
        Iterate over all images in wiki.

        Each image data is dictionary with two fields: `title` and `url`.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_page_list(
        self, namespace: int, limit: int, first_page: Optional[str] = None,
        redirect_filter_mode: str = 'all'
    ) -> Iterator[str]:
        """Iterate over all page names in wiki in `namespace`."""
        raise NotImplementedError()

    @abstractmethod
    def get_page(
        self, title: str,
    ) -> str:
        """Get text of page with `title`."""
        raise NotImplementedError()

    @abstractmethod
    def search_pages(
        self, search_request: str, namespace: int, limit: int,
    ) -> Iterator[str]:
        """Search pages in wiki in `namespace` with `search_request`."""
        raise NotImplementedError()

    @abstractmethod
    def get_deletedrevs_list(
        self, namespace: int, limit: int
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over deleted revisions in wiki in `namespace`."""
        raise NotImplementedError()

    @abstractmethod
    def delete_page(
            self, page_name: str, reason: Optional[str] = None
    ) -> None:
        """Delete page."""
        raise NotImplementedError()

    @abstractmethod
    def edit_page(
            self, page_name: str, text: str, summary: Optional[str] = None
    ) -> None:
        """Edit page, setting new text."""
        raise NotImplementedError()

    @abstractmethod
    def api_login(self, username: str, password: str) -> None:
        """Log in to MediaWiki API."""
        raise NotImplementedError()


class MediaWikiAPI1_19(MediaWikiAPI):
    """MediaWiki API 1.19 class with authentication data."""

    api_url: str
    index_url: str
    session: requests.Session
    edit_tokens: Dict[str, str]
    delete_tokens: Dict[str, str]

    def __init__(self, url: str):
        """Create MediaWiki API 1.19 class with given API URL."""
        self.api_url = '{}/api.php'.format(url)
        self.index_url = '{}/index.php'.format(url)
        self.session = requests.Session()
        self.edit_tokens = dict()
        self.delete_tokens = dict()

    def get_namespace_list(self) -> List[int]:
        """Iterate over namespaces in wiki."""
        params: Dict[str, Any] = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'namespaces',
            'format': 'json',
        }

        r = self.session.get(self.api_url, params=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])
        namespaces = data['query']['namespaces']

        return list(
            filter(
                lambda namespace_id: namespace_id >= 0,
                map(
                    lambda namespace: int(namespace),
                    namespaces.keys()
                )
            )
        )

    def get_image_list(self, limit: int) -> Iterator[Dict[str, str]]:
        """
        Iterate over all images in wiki.

        Each image data is dictionary with two fields: `title` and `url`.
        """
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'allimages',
            'aidir': 'ascending',
            'ailimit': limit,
            'format': 'json',
        }
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            images = data['query']['allimages']

            for image_data in images:
                yield {
                    'title': image_data['title'],
                    'url': image_data['url'],
                }

            if 'query-continue' not in data:
                break
            last_continue = data['query-continue']['allimages']

    def get_page_list(
        self, namespace: int, limit: int, first_page: Optional[str] = None,
        redirect_filter_mode: str = 'all'
    ) -> Iterator[str]:
        """Iterate over all page names in wiki in `namespace`."""
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': namespace,
            'apdir': 'ascending',
            'apfilterredir': redirect_filter_mode,
            'aplimit': limit,
            'format': 'json',
        }
        if first_page is not None:
            params['apfrom'] = first_page
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            pages = data['query']['allpages']

            for page_data in pages:
                yield page_data['title']

            if 'query-continue' not in data:
                break
            last_continue = data['query-continue']['allpages']

    def get_page(
        self, title: str,
    ) -> str:
        """Get text of page with `title`."""
        raise NotImplementedError()

    def search_pages(
        self, search_request: str, namespace: int, limit: int,
    ) -> Iterator[str]:
        """Search pages in wiki in `namespace` with `search_request`."""
        raise NotImplementedError()

    def get_deletedrevs_list(
        self, namespace: int, limit: int
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over deleted revisions in wiki in `namespace`."""
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'deletedrevs',
            'drnamespace': namespace,
            'drdir': 'newer',
            'drlimit': limit,
            'drprop': 'revid|user|comment|content',
            'format': 'json',
        }
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            deletedrevs = data['query']['deletedrevs']

            for deletedrev_data in deletedrevs:
                title: str = deletedrev_data['title']

                for revision in deletedrev_data['revisions']:
                    revision.update({'title': title})
                    yield revision

            if 'query-continue' not in data:
                break
            last_continue = data['query-continue']['deletedrevs']

    def delete_page(
            self, page_name: str, reason: Optional[str] = None
    ) -> None:
        """Delete page."""
        params: Dict[str, Any] = {
            'action': 'delete',
            'title': page_name,
            'format': 'json',
        }
        if reason is not None:
            params['reason'] = reason
        if page_name not in self.delete_tokens:
            self.delete_tokens.update(self.get_tokens('delete', page_name))
        params['token'] = self.delete_tokens[page_name],

        r = self.session.post(self.api_url, data=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            if data['error']['code'] == 'cantdelete':
                raise CanNotDelete(data['error']['info'])
            raise MediaWikiAPIError(data['error'])

        return None

    def edit_page(
            self, page_name: str, text: str, summary: Optional[str] = None
    ) -> None:
        """Delete page."""
        params: Dict[str, Any] = {
            'action': 'edit',
            'title': page_name,
            'text': text,
            'format': 'json',
        }
        if summary is not None:
            params['summary'] = summary
        if page_name not in self.edit_tokens:
            self.edit_tokens.update(self.get_tokens('edit', page_name))
        params['token'] = self.edit_tokens[page_name],

        r = self.session.post(self.api_url, data=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])

        return None

    def get_tokens(self, token_type: str, titles: str) -> Dict[str, str]:
        """Return page tokens for API."""
        params: Dict[str, Any] = {
            'action': 'query',
            'prop': 'info',
            'titles': titles,
            'intoken': token_type,
            'format': 'json',
        }

        r = self.session.post(self.api_url, params=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])
        if 'warning' in data:
            raise MediaWikiAPIError(data['warning'])

        return dict(map(
            lambda page_data: (
                    page_data['title'], page_data['{}token'.format(token_type)]
                    ),
            data['query']['pages'].values()
        ))

    def api_login(self, username: str, password: str) -> None:
        """Log in to MediaWiki API."""
        params1: Dict[str, Any] = {
            'action': 'login',
            'format': 'json',
            'lgname': username,
            'lgpassword': password,
        }

        r1 = self.session.post(self.api_url, data=params1)
        if r1.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r1.status_code))

        data1 = r1.json()
        if 'error' in data1:
            raise MediaWikiAPIError(data1['error'])
        if 'warning' in data1:
            raise MediaWikiAPIError(data1['warning'])

        if data1['login']['result'] == 'Success':
            return

        if data1['login']['result'] != 'NeedToken':
            raise MediaWikiAPIError('Login result is {}'.format(
                data1['login']['result']
            ))

        params2: Dict[str, Any] = {
            'action': 'login',
            'format': 'json',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': data1['login']['token'],
        }

        r2 = self.session.post(self.api_url, data=params2)
        if r2.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r2.status_code))

        data2 = r2.json()
        if 'error' in data2:
            raise MediaWikiAPIError(data2['error'])
        if 'warning' in data2:
            raise MediaWikiAPIError(data2['warning'])

        if data2['login']['result'] != 'Success':
            raise MediaWikiAPIError('Login result is {}'.format(
                data2['login']['result']
            ))


class MediaWikiAPI1_31(MediaWikiAPI):
    """MediaWiki API 1.31 class with authentication data."""

    api_url: str
    index_url: str
    session: requests.Session
    csrf_token: Optional[str]

    def __init__(self, url: str):
        """Create MediaWiki API 1.31 class with given API URL."""
        self.api_url = '{}/api.php'.format(url)
        self.index_url = '{}/index.php'.format(url)
        self.session = requests.Session()
        self.csrf_token = None

    def get_namespace_list(self) -> List[int]:
        """Iterate over namespaces in wiki."""
        params: Dict[str, Any] = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'namespaces',
            'format': 'json',
        }

        r = self.session.get(self.api_url, params=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])
        namespaces = data['query']['namespaces']

        return list(
            filter(
                lambda namespace_id: namespace_id >= 0,
                map(
                    lambda namespace: int(namespace),
                    namespaces.keys()
                )
            )
        )

    def get_image_list(self, limit: int) -> Iterator[Dict[str, str]]:
        """
        Iterate over all images in wiki.

        Each image data is dictionary with two fields: `title` and `url`.
        """
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'allimages',
            'aidir': 'ascending',
            'ailimit': limit,
            'format': 'json',
        }
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            images = data['query']['allimages']

            for image_data in images:
                yield {
                    'title': image_data['title'],
                    'url': image_data['url'],
                }

            if 'continue' not in data:
                break
            last_continue = data['continue']

    def get_page_list(
        self, namespace: int, limit: int, first_page: Optional[str] = None,
        redirect_filter_mode: str = 'all'
    ) -> Iterator[str]:
        """Iterate over all page names in wiki in `namespace`."""
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': namespace,
            'apdir': 'ascending',
            'apfilterredir': redirect_filter_mode,
            'aplimit': limit,
            'format': 'json',
        }
        if first_page is not None:
            params['apfrom'] = first_page
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            pages = data['query']['allpages']

            for page_data in pages:
                yield page_data['title']

            if 'continue' not in data:
                break
            last_continue = data['continue']

    def get_page(
        self, title: str
    ) -> str:
        """Get text of page with `title`."""
        params: Dict[str, Any] = {
            'action': 'raw',
            'title': title,
        }

        r = self.session.get(self.index_url, params=params)
        if r.status_code != 200:
            raise MediaWikiAPIError(
                'Status code is {}'.format(r.status_code)
            )

        return r.text

    def search_pages(
        self, search_request: str, namespace: int, limit: int,
    ) -> Iterator[str]:
        """Iterate over all page names in wiki in `namespace`."""
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'search',
            'srnamespace': namespace,
            'srlimit': limit,
            'format': 'json',
            'srsearch': search_request,
            'srwhat': 'text',
        }
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            pages = data['query']['search']

            for page_data in pages:
                yield page_data['title']

            if 'continue' not in data:
                break
            last_continue = data['continue']

    def get_deletedrevs_list(
        self, namespace: int, limit: int
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over deleted revisions in wiki in `namespace`."""
        params: Dict[str, Any] = {
            'action': 'query',
            'list': 'deletedrevs',  # TODO: deprecated since MediaWiki 1.25
            'drnamespace': namespace,
            'drdir': 'newer',
            'drlimit': limit,
            'drprop': 'revid|user|comment|content',
            'format': 'json',
        }
        last_continue: Dict[str, Any] = {}

        while True:
            current_params = params.copy()
            current_params.update(last_continue)
            r = self.session.get(self.api_url, params=current_params)
            if r.status_code != 200:
                raise MediaWikiAPIError(
                    'Status code is {}'.format(r.status_code)
                )

            data = r.json()
            if 'error' in data:
                raise MediaWikiAPIError(data['error'])
            deletedrevs = data['query']['deletedrevs']

            for deletedrev_data in deletedrevs:
                title: str = deletedrev_data['title']

                for revision in deletedrev_data['revisions']:
                    revision.update({'title': title})
                    yield revision

            if 'continue' not in data:
                break
            last_continue = data['continue']

    def delete_page(
            self, page_name: str, reason: Optional[str] = None
    ) -> None:
        """Delete page."""
        if self.csrf_token is None:
            self.csrf_token = self.get_token('csrf')

        params: Dict[str, Any] = {
            'action': 'delete',
            'title': page_name,
            'token': self.csrf_token,
            'format': 'json',
        }
        if reason is not None:
            params['reason'] = reason

        r = self.session.post(self.api_url, data=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])

        return None

    def edit_page(
            self, page_name: str, text: str, summary: Optional[str] = None
    ) -> None:
        """Edit page, setting new text."""
        if self.csrf_token is None:
            self.csrf_token = self.get_token('csrf')

        params: Dict[str, Any] = {
            'action': 'edit',
            'title': page_name,
            'text': text,
            'token': self.csrf_token,
            'format': 'json',
        }
        if summary is not None:
            params['summary'] = summary

        r = self.session.post(self.api_url, data=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])

        return None

    def get_token(self, token_type: str) -> str:
        """Return CSRF token for API."""
        params: Dict[str, Any] = {
            'action': 'query',
            'meta': 'tokens',
            'type': token_type,
            'format': 'json',
        }

        r = self.session.get(self.api_url, params=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()

        # TODO: handle errors
        token = data['query']['tokens']['{}token'.format(token_type)]

        return token

    def api_login(self, username: str, password: str) -> None:
        """Log in to MediaWiki API."""
        token = self.get_token('login')

        params: Dict[str, Any] = {
            'action': 'login',
            'format': 'json',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': token,
        }

        r = self.session.post(self.api_url, data=params)
        if r.status_code != 200:
            raise MediaWikiAPIError('Status code is {}'.format(r.status_code))

        data = r.json()
        if 'error' in data:
            raise MediaWikiAPIError(data['error'])