from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from starpy import fastagi
import logging
import re
import treq

max_attemps = 2
time_out = 2.500
id_regexp = '[1-9][0-9]{5,9}'
var_id = 'ID_NUMBER'
var_status = 'ID_STATUS'
sound_file = 'extensions'
sound_no_id = 'invalid'
sound_id_invalid = 'invalid'
sound_try_again = 'pls-try-again'
rurl = 'http://bus.comedal.com.co:8022/ws/ivr/datos-cedula?cedula={}'
rtimeout = 2
ruser = None
rpassword = None

config = """
idn:
    max_attemps: 2
    time_out: 2.500
    regexp: [1-9][0-9]{5,9}

variables:
    id: ID_NUMBER
    status: ID_STATUS

sounds:
    enter_id: extensions
    no_id: invalid
    id_invalid: invalid
    try_again: pls-try-again

request:
    url: http://bus.comedal.com.co:8022/ws/ivr/datos-cedula?cedula={}
    timeout: 2
    user: admin
    password: password
"""


def load_config(config_file):
    with open(config_file, 'r') as stream:
        try:
            return yaml.safe_load(config)
        except yaml.YAMLError as exc:
            print(exc)

def get_module_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    """
    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s [%(name)-8s] %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


logger = get_module_logger("FastAGI")


@inlineCallbacks
def get_id(agi):
    """Attemps to read a ID number using DTMF"""
    digits = None
    status = None

    logger.info("New call has arrived")
    try:
        for attemp in range(max_attemps):
            if attemp != 0:
                yield agi.streamFile(sound_try_again)

            (digits, timeout) = yield agi.getData(sound_file, time_out)
            logger.info("New DTMF input: {}, with timeout: {}".format(
                digits, timeout)
            )

            if not digits:
                logger.info("No digits has been entered")
                if not timeout:
                    digits, status = None, 'EMPTY'
                else:
                    digits, status = None, 'TIMEOUT'
                yield agi.streamFile(sound_no_id)

            elif not re.search(id_regexp, digits):
                logger.info("The input doesn't match the regular expression")
                digits, status = None, 'WRONG'
                yield agi.streamFile(sound_id_invalid)

            else:
                logger.info("The digits value is correct")

                url = rurl.format(digits)
                response = yield treq.post(url, persistent=True, rtimeout,
                                           auth=(ruser, rpassword))

                logger.info(response)

                status = 'OK'
                break

    except Exception:
        digits = None
        status = 'ERROR'
    finally:

        if digits:
            yield agi.setVariable(var_id, digits)
        yield agi.setVariable(var_status, status)

        agi.finish()


if __name__ == "__main__":
    logger.info("Starting the factory")
    agi_factory = fastagi.FastAGIFactory(get_id)
    logger.info("Listening on port")
    reactor.listenTCP(4573, agi_factory)
    logger.info("Running the reactor")
    reactor.run()
