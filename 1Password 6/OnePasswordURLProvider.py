#!/usr/bin/env python
#
import urllib2
import json

from autopkglib import Processor, ProcessorError


__all__ = ["OnePasswordURLProvider"]

# Variables for the update URL:
# - https://app-updates.agilebits.com/check/1/
# - Kernel version
# - String "OPM4"
# - Locale
# - The 1Password build number to update from
UPDATE_URL_FOUR = "https://app-updates.agilebits.com/check/1/13.0.0/OPM4/en/400600"
UPDATE_URL_FIVE = "https://app-updates.agilebits.com/check/1/14.0.0/OPM4/en/500000"
UPDATE_URL_SIX = "https://app-updates.agilebits.com/check/1/14.0.0/OPM4/en/553001"
DEFAULT_SOURCE = "Amazon CloudFront"
DEFAULT_MAJOR_VERSION = "6"


class OnePasswordURLProvider(Processor):
    """Provides a download URL for the latest 1Password"""
    input_variables = {
        "major_version": {
            "required": False,
            "description": "The 1Password major version to get. "
            "Possible values are '4', '5' or '6' and the default is '6'",
        },
        "base_url": {
            "required": False,
            "description": "The 1Password update check URL",
        },
        "source": {
            "required": False,
            "description": "Where to download the disk image. "
            "Possible values are 'Amazon CloudFront', 'CacheFly' and 'AgileBits'. "
            "Default is Amazon CloudFront."
        }
    }
    output_variables = {
        "url": {
            "description": "URL to the latest 1Password release.",
        },
    }
    description = __doc__

    def download_update_info(self, base_url):
        """Downloads the update url and returns a json object"""
        try:
            f = urllib2.urlopen(base_url)
            json_data = json.load(f)
        except BaseException as e:
            raise ProcessorError("Can't download %s: %s" % (base_url, e))

        return json_data

    def get_1Password_dmg_url(self, base_url, preferred_source):
        """Find and return a download URL"""

        self.output("Preferred source is %s" % preferred_source)

        # 1Password update check gets a JSON response from the server.
        # Grab it and parse...
        info_plist = self.download_update_info(base_url)
        version = info_plist.get('version', None)
        self.output("Found version %s" % version)

        sources = info_plist.get('sources', [])
        found_source = next((source for source in sources if source['name'] == preferred_source), None)
        if found_source:
            source_url = found_source.get('url', None)
            if not source_url:
                raise ProcessorError("No URL found for %s" % preferred_source)
            return source_url
        else:
            raise ProcessorError("No download source for %s" % preferred_source)

    def main(self):
        major_version = self.env.get("major_version", DEFAULT_MAJOR_VERSION)
        if int(major_version) == 4:
            UPDATE_URL = UPDATE_URL_FOUR
        elif int(major_version) == 5:
            UPDATE_URL = UPDATE_URL_FIVE
        elif int(major_version) == 6:
            UPDATE_URL = UPDATE_URL_SIX
        else:
            raise ProcessorError("Unsupported value for major version: %s" % major_version)
        base_url = self.env.get("base_url", UPDATE_URL)
        source = self.env.get("source", DEFAULT_SOURCE)
        self.env["url"] = self.get_1Password_dmg_url(base_url, source)
        self.output("Found URL %s" % self.env["url"])


if __name__ == "__main__":
    processor = OnePasswordURLProvider()
    processor.execute_shell()
