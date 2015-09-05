from edenred import Database
from nose.tools import eq_

def test_get_balance():
  db = Database(':memory:')
  eq_(db.get_balance(), 0.0)
  db.add_balance(5)
  db.add_balance(6)
  db.add_balance(7)
  eq_(db.get_balance(), 7)
  eq_(list(db.balance()), [5., 6., 7.])

def test_empty_balance():
  eq_(Database(':memory:').get_balance(), 0)

def test_empty_history():  
  eq_(list(Database(':memory:').balance()), [])
