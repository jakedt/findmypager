import logging as logger
import webapp2

from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from pyicloud.exceptions import PyiCloudFailedLoginException
from email.utils import parseaddr

from data import ICloudCredential, CredentialCookieProvider, CookieiCloudService

ALERT_SEARCH_TERM = 'PagerDuty ALERT'


class FileAlert(InboundMailHandler):
  def receive(self, mail_message):
    logger.info('Received a message from: %s with subject %s', mail_message.sender,
                mail_message.subject)

    if (mail_message.subject.find(ALERT_SEARCH_TERM) >= 0 or
        mail_message.sender.find(ALERT_SEARCH_TERM) >= 0):
      logger.info('Received pagerduty alert to: %s', mail_message.to)

      # Fire our shit! ... But I am le tired.
      _, email_address = parseaddr(mail_message.to)
      uuid = email_address.split('@')[0]
      credential = ICloudCredential.query(ICloudCredential.uuid == uuid).get()

      if not credential:
        logger.warning('Unable to find credential with uuid: %s', uuid)
        return

      if not credential.deviceid:
        logger.warning('No deviceid selected for credential with uuid: %s', uuid)
        return

      cookie_jar = CredentialCookieProvider(credential)
      try:
        api = CookieiCloudService(credential.email, credential.password, cookie_jar)
      except PyiCloudFailedLoginException:
        logger.warning('Unable to login to iCloud for credential with uuid: %s', uuid)
        return

      all_devices = api.devices

      if credential.deviceid not in all_devices.keys():
        logger.warning('Selected device not available: %s, devices: %s, credential uuid: %s',
                       credential.deviceid, all_devices.keys(), uuid)
        return

      all_devices[credential.deviceid].play_sound()

    else:
      logger.info('Mail was not a pagerduty alert: %s', mail_message.subject)

app = webapp2.WSGIApplication([FileAlert.mapping()], debug=True)
