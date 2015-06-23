# -*- coding: utf-8 -*-
from __future__ import absolute_import
from PyQt5.QtCore import QDateTime, Qt, QUrl
from PyQt5.QtNetwork import QNetworkRequest, QNetworkCookie, QNetworkCookieJar


class SplashCookieJar(QNetworkCookieJar):

    def update_cookie_header(self, request):
        """ Use this cookiejar to set Cookie: request header """
        if not _should_send_cookies(request):
            return

        cookies = self.cookiesForUrl(request.url())
        if not cookies:
            return

        request.setRawHeader(b"Cookie", _cookies_to_raw(cookies))

    def fill_from_reply(self, reply):
        """ Add cookies from the reply to the cookiejar """
        # based on QNetworkReplyImplPrivate::metaDataChanged C++ code
        if not _should_save_cookies(reply.request()):
            return
        cookies = reply.header(QNetworkRequest.SetCookieHeader)
        if not cookies:
            return
        self.setCookiesFromUrl(cookies, reply.url())

    def delete(self, name=None, url=None):
        """
        Remove all cookies with a passed name for the passed url.
        Return a number of cookies deleted.
        """
        all_cookies = self.allCookies()
        if url is None:
            new_cookies = [c for c in all_cookies if bytes(c.name()) != name.encode('utf-8')]
        else:
            remove_cookies = self.cookiesForUrl(QUrl(url))
            if name is not None:
                remove_cookies = [c for c in remove_cookies if bytes(c.name()) == name.encode('utf-8')]
            to_remove = {self._cookie_fp(c) for c in remove_cookies}
            new_cookies = [
                c for c in all_cookies if self._cookie_fp(c) not in to_remove
            ]

        self.setAllCookies(new_cookies)
        return len(all_cookies) - len(new_cookies)

    @classmethod
    def _cookie_fp(cls, cookie):
        return bytes(cookie.toRawForm(QNetworkCookie.Full))

    def clear(self):
        """ Remove all cookies. Return a number of cookies deleted. """
        old_size = len(self.allCookies())
        self.setAllCookies([])
        return old_size

    def init(self, cookies):
        """
        Replace current cookies with ``cookies``. The argument should
        be a list of Python dicts with cookie data in HAR format.
        """
        print("init")
        qt_cookies = [self.har_cookie2qt(c) for c in cookies]
        self.setAllCookies(qt_cookies)

    def add(self, cookie):
        """
        Add a cookie. Cookie should be a Python dict with cookie
        data in HAR format.
        """
        cookies = list(self.allCookies())
        cookies.append(self.har_cookie2qt(cookie))
        self.setAllCookies(cookies)

    @classmethod
    def har_cookie2qt(cls, cookie):
        qcookie = QNetworkCookie()
        qcookie.setName(cookie[b"name"])
        qcookie.setValue(cookie[b"value"])

        if b'domain' in cookie:
            qcookie.setDomain(cookie[b"domain"].decode('utf-8'))

        if b'httpOnly' in cookie:
            qcookie.setHttpOnly(cookie[b"httpOnly"])

        if b'secure' in cookie:
            qcookie.setSecure(cookie[b"secure"])

        if b'path' in cookie:
            qcookie.setPath(cookie[b"path"].decode('utf-8'))

        if cookie.get(b'expires'):
            expires = QDateTime.fromString(cookie[b"expires"].decode('utf-8'), Qt.ISODate)
            qcookie.setExpirationDate(expires)

        return qcookie


def _should_send_cookies(request):
    """ Return True if cookies should be sent for a request """
    # based on QNetworkAccessManager::createRequest() C++ code
    attr = request.attribute(
        QNetworkRequest.CookieLoadControlAttribute,
        QNetworkRequest.Automatic
    )
    return attr == QNetworkRequest.Automatic


def _should_save_cookies(request):
    """ Return True if cookies should be saved for a request """
    # based on QNetworkReplyImplPrivate::metaDataChanged() C++ code
    attr = request.attribute(
        QNetworkRequest.CookieSaveControlAttribute,
        QNetworkRequest.Automatic
    )
    return attr == QNetworkRequest.Automatic


def _cookies_to_raw(cookies):
    """ Build raw Cookie: header value from a list of QNetworkCookie instances """
    # based on QNetworkRequest::fromheaderValue() C++ code
    return b"; ".join(
        bytes(cookie.toRawForm(QNetworkCookie.NameAndValueOnly))
        for cookie in cookies
    )
