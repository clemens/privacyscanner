from ..base import AbstractChromeScan


class SecurityHeadersMixin(AbstractChromeScan):
    def _extract_security_headers(self):
        response_lookup = {response['url']: response for response in self.response_log}
        response = response_lookup[self.result['final_url']]
        headers_lower = {}
        for key, value in response['headers'].items():
            headers_lower[key.lower()] = value

        header_names = ['Referrer-Policy', 'X-Content-Type-Options',
                        'X-Frame-Options', 'Expect-CT',
                        'Access-Control-Allow-Origin']
        security_headers = {}
        for header_name in header_names:
            security_headers[header_name] = self._get_header(headers_lower, header_name)

        hsts_value = None
        if 'strict-transport-security' in headers_lower:
            hsts_value = self._parse_hsts(headers_lower['strict-transport-security'])
        security_headers['Strict-Transport-Security'] = hsts_value

        csp_value = None
        if 'content-security-policy' in headers_lower:
            csp_value = self._parse_csp(headers_lower['content-security-policy'])
        security_headers['Content-Security-Policy'] = csp_value

        xss_protection = None
        if 'x-xss-protection' in headers_lower:
            xss_protection = self._parse_xss_protection(headers_lower['x-xss-protection'])
        security_headers['X-XSS-Protection'] = xss_protection

        self.result['security_headers'] = security_headers

    @staticmethod
    def _parse_csp(header_value):
        csp = {}
        parts = [part.strip() for part in header_value.split(';')]
        for part in parts:
            values = part.split()
            key = values[0]
            values = values[1:]
            csp[key.lower()] = values
        csp['header_value'] = header_value
        return csp

    @staticmethod
    def _parse_hsts(header_value):
        parts = [part.strip() for part in header_value.split(';')]
        max_age = None
        for part in parts:
            if part.startswith('max-age='):
                max_age = part.split('=', 1)[1]
                try:
                    max_age = int(max_age)
                except ValueError:
                    pass
                break
        return {
            'header_value': header_value,
            'includeSubDomains': 'includeSubDomains' in parts,
            'preload': 'preload' in parts,
            'max-age': max_age
        }

    @staticmethod
    def _parse_xss_protection(header_value):
        mode = None
        is_active = None
        if ';' in header_value:
            is_active, mode_str = header_value.split(';', 1)
            is_active = is_active.strip() == '1'
            if mode_str.strip().startswith('mode='):
                mode = mode_str.split('=', 1)[1].strip()
        return {
            'header_value': header_value,
            'is_active': is_active,
            'mode': mode
        }

    @staticmethod
    def _get_header(headers, header_name):
        header_name = header_name.lower()
        if header_name in headers:
            value = headers[header_name]
            # Chrome will separate multiple headers with a newline,
            # however, RFC 2616 says that they should be interpreted
            # with a comma in between. See RFC2616 Sect. 4.2:
            # https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html#sec4.2
            value = value.replace('\n', ',')
            return value
        return None