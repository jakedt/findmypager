import logging as logger
import webapp2

from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from email.utils import parseaddr

from data import ICloudCredential, send_notification

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

      send_notification(credential, uuid)

    else:
      logger.info('Mail was not a pagerduty alert: %s', mail_message.subject)

app = webapp2.WSGIApplication([FileAlert.mapping()], debug=True)
