from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from starpy import fastagi
import logging
import re

max_attemps = 2
time_out = 2.500
id_regexp = '[1-9][0-9]{5,9}'
var_id = 'ID_NUMBER'
var_status = 'ID_STATUS'
sound_file = 'extensions'
sound_no_id = 'invalid'
sound_id_invalid = 'invalid'
sound_try_again = 'pls-try-again'


@inlineCallbacks
def get_id(agi):
    """Attemps to read a ID number using DTMF"""
    digits = None
    status = None

    try:
        for attemp in range(max_attemps):
            if attemp != 0:
                yield agi.streamFile(sound_try_again)

            (digits, timeout) = yield agi.getData(sound_file, time_out)

            if not digits:
                if not timeout:
                    digits, status = None, 'EMPTY'
                else:
                    digits, status = None, 'TIMEOUT'
                yield agi.streamFile(sound_no_id)

            elif re.search(id_regexp, digits):
                digits, status = None, 'WRONG'
                yield agi.streamFile(sound_id_invalid)

            else:
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
    fastagi.log.setLevel(logging.DEBUG)
    agi_factory = fastagi.FastAGIFactory(get_id)
    reactor.listenTCP(4573, agi_factory)
    reactor.run()
