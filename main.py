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

from data import get_or_create_credential, load_devices, send_notification


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(webapp2.RequestHandler):
  def get(self):
    login_failed = False
    devices = {}

    credential, new_credential = get_or_create_credential()

    logger.info('credential %s', credential)
    if not new_credential:
      devices, login_failed = load_devices(credential)

    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(credential=credential, devices=devices,
                                        login_failed=login_failed))

class CredentialHandler(webapp2.RequestHandler):
  def post(self):
    email = self.request.get('inputEmail')
    password = self.request.get('inputPassword')

    credential, credential_dirty = get_or_create_credential()
    logger.info('Credential: %s', credential)
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

    if credential_dirty:
      logger.info('Saving')
      credential.put()

    devices, login_failed = load_devices(credential)

    template = JINJA_ENVIRONMENT.get_template('devices.html')
    self.response.write(template.render(devices=devices, login_failed=login_failed,
                                        credential=credential))


class DeviceHandler(webapp2.RequestHandler):
  def post(self):
    deviceid = self.request.get('deviceid')

    credential, credential_dirty = get_or_create_credential()

    if credential.deviceid != deviceid:
      logger.info('Updating device')
      credential.deviceid = deviceid
      credential_dirty = True

    if credential_dirty:
      logger.info('Saving')
      credential.put()

    template = JINJA_ENVIRONMENT.get_template('testdevice.html')
    self.response.write(template.render(credential=credential))


class TestDeviceHandler(webapp2.RequestHandler):
  def post(self):
    credential, _ = get_or_create_credential()
    send_notification(credential, 'test')
    self.response.write('Notification sent.')


app = webapp2.WSGIApplication([
  ('/', MainHandler),
  ('/credential', CredentialHandler),
  ('/device', DeviceHandler),
  ('/test', TestDeviceHandler),
], debug=True)
