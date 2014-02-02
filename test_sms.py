import responses
from nose.tools import eq_, raises
from edenred import send_sms
import mock

MOCK_ENV = {
  'SMSAPI_USERNAME': 'username',
  'SMSAPI_PASSWORD': 'password'	
}


@responses.activate
@mock.patch('os.getenv', MOCK_ENV.get)
def test_send_sms_success():
  responses.add(responses.POST ,'https://ssl.smsapi.pl/sms.do',
    body='OK:123456789:3.14', status=200)
  send_sms('123456789', 'hello world')
  eq_(len(responses.calls), 1)
  eq_(responses.calls[0].request.url, 'https://ssl.smsapi.pl/sms.do')
  eq_(responses.calls[0].request.body, 'username=username&to=123456789&message=hello+world&password=password&from=ECO')

@responses.activate
@raises(RuntimeError)
@mock.patch('os.getenv', MOCK_ENV.get)
def test_send_sms_failure():
  responses.add(responses.POST, 'https://ssl.smsapi.pl/sms.do',
    body='ERROR:1234', status=200)
  send_sms('123456789', 'hello world')
  eq_(len(responses.calls), 1)
  eq_(responses.calls[0].request.url, 'https://ssl.smsapi.pl/sms.do')
  eq_(responses.calls[0].request.body, 'username=username&to=123456789&message=hello+world&password=password&from=ECO')
