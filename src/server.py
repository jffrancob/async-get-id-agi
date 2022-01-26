import re
import confuse
import aiohttp
import logging.config

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.log import agi_server_logger as logger
from aioagi.urldispathcer import AGIView

from logger import LOGGING


class PartialFormatter(string.Formatter):
    def __init__(self, missing='~~~', bad_fmt='!!!'):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val = super(PartialFormatter, self).get_field(field_name, args, kwargs)
            # Python 3, 'super().get_field(field_name, args, kwargs)' works
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value is None:
            return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise


class GetIDView(AGIView):
    session = None

    with open("/etc/config.yaml") as stream:
        config = yaml.safe_load(stream)

    def __init__(self, *args, **kwargs):
        self.user = {}
        self.status = None
        if not self.session:
            self.session = aiohttp.ClientSession()

        super().__init__(*args, **kwargs)

    async def sip(self):
        await self.start()

    async def local(self):
        await self.start()

    async def dahdi(self):
        await self.start()

    async def start(self):
        # await self.request.agi.verbose(self.request.headers.get("agi_callerid"))
        # await self.request.agi.verbose(dir(self.request.agi))
        try:
            await self.get_id()
            await self.get_user_info()
        except Exception as error:
            self.status = 'ERROR'
        await self.set_vars()

    async def get_information(self, regExp, sounds, func_slide=None, tries=3,
                              confirm=3, timeout=2500, max_digits=255, cancel=None):
        attemps = 0
        try_again = False
        while tries is None or attemps < tries:
            if attemps > 0 and try_again and sounds.get("try-again"):
                await self.stream_text(sounds.get("try-again"))
            attemps += 1
            response = await self.get_data(sounds.get("prompt"),
                                           timeout=timeout, max_digits=max_digits)
            result, timeout = response.result, response.info == "(timeout)"
            if not result:
                if sounds.get("empty", sounds.get("invalid")):
                    await self.stream_text(sounds.get("empty", sounds.get("invalid")))
                try_again = True
            elif result == cancel:
                return None
            elif not re.search(regExp, result):
                if sounds.get("invalid"):
                    await self.stream_text(sounds.get("invalid"))
                try_again = True
            else:
                # await self.log_ivr_try("EXPRESSION", result)
                if func_slide:
                    await self.stream_text(sounds.get("number-is"))
                    for slide in func_slide(result):
                        await self.stream_text(slide)
                    choice = await self.choose_option(sounds.get("confirm"),
                                                      optionList=["1", "0"], tries=confirm)
                    if not choice:
                        await self.stream_text(sounds.get("repeat"))
                        try_again = False
                    elif choice == '1':
                        return result
                else:
                    return result
        return None

    async def get_id(self):

        for attemp in range(self.config["idn"]["max_attemps"]):
            if attemp != 0:
                await self.agi.stream_file(self.config["sounds"]["try_again"])

            data_result = await self.agi.get_data(self.config["sounds"]["enter_id"], self.config["idn"]["time_out"])
            id_number, timeout = data_result.result, data_result.info == "(timeout)"

            if not id_number:
                logger.info("No id_number has been entered")
                self.status = 'EMPTY' if not timeout else 'TIMEOUT'
                await self.agi.stream_file(self.config["sounds"]["no_id"])

            elif not re.search(self.config["idn"]["regexp"].get(), id_number):
                logger.info("The input doesn't match the regular expression")
                self.status = 'WRONG'
                await self.agi.stream_file(self.config["sounds"]["id_invalid"]))

            else:
                logger.info("The id_number value is correct")
                self.user[self.config["idn"]["field"]] = id_number
                self.status = 'OK'
                break

    async def get_user_info(self):
        url = self.config["request"]["url"]
        if not url:
            return

        method = self.config["request"]["method"]
        user = self.config["request"]["auth"]["login"]
        if user:
            password = self.config["request"]["auth"]["password"]
            auth = aiohttp.BasicAuth(user, password)
        else:
            auth = None

        params = self.config["request"]["params"]
        for key in params:
            if type(params[key]) is str:
                params[key] = params[key].format(**self.user)

        json_data = self.config["request"]["json"]
        for key in json_data:
            if type(json_data[key]) is str:
                json_data[key] = json_data[key].format(**self.user)

        timeout = self.config["request"]["timeout"]
        timeout = aiohttp.ClientTimeout(total=timeout)
        async with self.session.request(method, url,
                                        auth=auth,
                                        params=params,
                                        json=json_data,
                                        timeout=timeout
                                        ) as resp:
            response = await resp.json()
            logger.info(response)
            self.user.update(response)

    async def set_vars(self):
        await self.agi.set_variable(self.config["status"]["variable"], self.status)

        vars_dict = self.config["variables"]
        for var, value in vars_dict.items():
            try:
                if type(value) is str:
                    value = value.format(**self.user)
                await self.agi.set_variable(var, value)
            except Exception as error:
                logger.warning("It's not posible to set ({var}, {value}): {error}".format(**locals()))

    async def set_custom_vars(self):
        fmt = PartialFormatter()
        vars_dict = self.config["variables"]
        for var, value in vars_dict.items():
            if type(value) is str:
                value = fmt.format(value, **self.user)
            await self.agi.set_variable(var, value)


if __name__ == '__main__':
    logging.config.dictConfig(LOGGING)
    app = AGIApplication()
    app.router.add_route('*', '/hello-view/', GetIDView)
    runner.run_app(app)
