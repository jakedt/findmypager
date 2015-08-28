import logging as logger
import pyicloud
import json

from google.appengine.ext import ndb
from google.appengine.api import users
from uuid import uuid4


pyicloud.base.os.mkdir = lambda x: None


class CookieiCloudService(pyicloud.PyiCloudService):
  def __init__(self, apple_id, password, cookie_provider):
    self._cookie_provider = cookie_provider
    super(CookieiCloudService, self).__init__(apple_id, password, cookie_directory='/')

  def _get_cookie(self):
    self._cookie_provider.get()

  def _update_cookie(self, request):
    cookies_to_store = {name: val for name, val in request.cookies.items()
                        if name.startswith('X-APPLE-WEB-KB')}
    self._cookie_provider.save(cookies_to_store)


class CredentialCookieProvider(object):
  def __init__(self, credential_obj):
    self._credential_obj = credential_obj

  def get(self):
    logger.info('Reading cookie')
    return self._credential_obj.cookie

  def save(self, cookie_dict):
    logger.info('Saving cookie')
    self._credential_obj.cookie = json.dumps(cookie_dict)
    self._credential_obj.put()


class ICloudCredential(ndb.Model):
  uuid = ndb.StringProperty()
  userid = ndb.IntegerProperty()
  email = ndb.StringProperty(indexed=False)
  password = ndb.StringProperty(indexed=False)
  cookie = ndb.StringProperty(indexed=False)
  deviceid = ndb.StringProperty(indexed=False)


def get_or_create_credential():
  user_id = str(users.get_current_user().user_id())
  logger.info('User id: %s', user_id)
  found = ndb.Key(ICloudCredential, user_id).get()
  if found is None:
    logger.info('Creating key for user id: %s', user_id)
    created = ICloudCredential(id=user_id, email='', password='', uuid=str(uuid4()))
    return created, True
  return found, False
