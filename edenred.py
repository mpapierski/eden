import os
import time
import requests
import hashlib
import json
import sqlite3
import pytz
from pushover import init, Client
from datetime import datetime

SALT = 'f4a6?Sta+4'
TIMEZONE = os.getenv('TIMEZONE')
DATABASE_URL = os.getenv('DATABASE_URL')
PUSHOVER_TOKEN = os.environ['PUSHOVER_TOKEN']
PUSHOVER_KEY = os.environ['PUSHOVER_KEY']

class Database(object):
  def __init__(self, url):
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
  init(PUSHOVER_TOKEN)
  pushover = Client(PUSHOVER_KEY)
  tz = pytz.timezone(TIMEZONE)
  now = tz.normalize(datetime.utcnow().replace(tzinfo=pytz.utc))
  card_number = os.getenv('CARD_NUMBER')
  db = Database(DATABASE_URL)
  current_value = db.get_balance()
  edenred_value = balance(int(card_number))
  print '{0}\t{1}\t{2}'.format(now, current_value, edenred_value)
  if current_value != edenred_value:
    delta = edenred_value - current_value
    db.add_balance(edenred_value)
    message = 'Edenred {3}. Previous {0}. Current {1}. Delta {2}.'.format(
      current_value,
      edenred_value,
      delta,
      now.strftime('%Y-%m-%d %H:%M:%S'))
    pushover.send_message(message, title='Edenred')

if __name__ == '__main__':
  main()
