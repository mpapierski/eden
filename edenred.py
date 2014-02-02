import os
import time
import requests
import hashlib
import json
import sqlite3
from datetime import datetime

SALT = 'f4a6?Sta+4'


class Database(object):
  def __init__(self, url='edenred.db'):
    """Setup database
    """
    self.db = sqlite3.connect(url)
    self.db.execute('''CREATE TABLE IF NOT EXISTS `balance` (`id` INTEGER PRIMARY KEY, `when` DATETIME, `value` REAL)''')
    self.db.commit()
  def add_balance(self, value):
    """Add new entry to `balance` table.
    """
    with self.db:
      self.db.execute('''INSERT INTO `balance` (`when`, `value`) VALUES (?, ?)''', (
        datetime.utcnow(), value, ))
  def get_balance(self):
    """Get balance. If there is no entries, return 0.0.
    """
    cur = self.db.cursor()
    cur.execute('''SELECT `value` FROM `balance` ORDER BY `id` DESC LIMIT 1''')
    for (value, ) in cur:
      return value
    return 0.0
  def balance(self):
    """Get all balance history
    """
    for (value, ) in self.db.execute('''SELECT `value` FROM `balance` ORDER BY `id` ASC'''):
      yield value

def send_sms(to, message):
  """Send SMS message to number `number` and message `message`.
  """
  username = os.getenv('SMSAPI_USERNAME')
  password = os.getenv('SMSAPI_PASSWORD')
  assert username
  assert password
  data = {
    'username': username,
    'password': password,
    'to': to,
    'message': message,
    'from': 'ECO',
  }
  r = requests.post('https://ssl.smsapi.pl/sms.do', data=data)
  response = r.content
  if response.startswith('ERROR:'):
    _, error_code = response.split(':')
    raise RuntimeError(error_code)
  assert response.startswith('OK:')
  print response

def balance(cards, timestamp=None):
  if timestamp is None:
    timestamp = int(time.time())
  # Calculate hash
  secret = hashlib.md5()
  secret.update(SALT)
  secret.update('{0}'.format(timestamp))
  data = {
    'action': 'balance',
    'cards': cards,
    'timestamp': timestamp,
    'hash': secret.hexdigest()
  }
  headers = {
    'Accept-Encoding': 'gzip',
    'User-Agent': 'Twoja Karta 1.1.0 (iPhone; iPhone OS 7.0.3; pl_PL)',
  }
  r = requests.post('http://www.edenred.pl/mobileapp/', 
    data=data,
    headers=headers)
  json_data = r.json()
  if str(cards) not in json_data.keys():
    print 'error'
    print json_data
    return
  card_details = json_data[str(cards)]
  if 'error' in card_details:
    raise RuntimeError(card_details['error'])
  assert 'amount' in card_details.keys(), json.dumps(card_details)
  amount = card_details['amount']
  return amount

def main():
  db = Database('edenred.db')

if __name__ == '__main__':
  main()
