#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import logging as logger
import jinja2
import os

from pyicloud.exceptions import PyiCloudFailedLoginException

from data import (ICloudCredential, CookieiCloudService, get_or_create_credential,
                  CredentialCookieProvider)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(webapp2.RequestHandler):
  def get(self):
    credential, new_credential = get_or_create_credential()

    logger.info('credential %s', credential)

    devices = {}
    login_failed = False
    if not new_credential:
      cookie_jar = CredentialCookieProvider(credential)
      login_failed = True
      try:
        api = CookieiCloudService(credential.email, credential.password, cookie_jar)
        login_failed = False
        devices = {deviceid: (dev['name'], dev['deviceDisplayName'])
                   for deviceid, dev in api.devices.items()
                   if dev['deviceDisplayName'].find('MacBook') < 0}
      except PyiCloudFailedLoginException:
        logger.warning('iCloud login failed')

    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(credential=credential, devices=devices,
                                        login_failed=login_failed))


  def post(self):
    email = self.request.get('email')
    password = self.request.get('password')
    deviceid = self.request.get('deviceid')

    credential, credential_dirty = get_or_create_credential()
    if credential.email != email:
      logger.info('Updating email address')
      credential.cookie = None
      credential.email = email
      credential_dirty = True

    if credential.password != password:
      logger.info('Updating password')
      credential.cookie = None
      credential.password = password
      credential_dirty = True

    if credential.deviceid != deviceid:
      logger.info('Updating device')
      credential.deviceid = deviceid
      credential_dirty = True

    if credential_dirty:
      logger.info('Saving')
      credential.put()
      self.response.write('Saved')
    else:
      self.response.write('No change')


app = webapp2.WSGIApplication([
  ('/', MainHandler)
], debug=True)
