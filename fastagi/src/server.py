import re
import json
import yaml
import string
import aiohttp
import logging.config

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.log import agi_server_logger as logger
from aioagi.urldispathcer import AGIView

from logger import LOGGING
from slider import Slider


class PartialFormatter(string.Formatter):
    def __init__(self, missing='~~~', bad_fmt='!!!'):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val = super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, spec):
        if value is None:
            return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise


class GetIDView(AGIView, Slider):
    http_client = None

    with open("/etc/config.yaml") as stream:
        config = yaml.safe_load(stream)

    def __init__(self, *args, **kwargs):
        self.user = {}
        self.status = None

        logger.info(f"{self.config}")

        if not self.http_client:
            self.http_client = aiohttp.ClientSession()

        super().__init__(*args, **kwargs)

    async def sip(self):
        await self.start()

    async def local(self):
        await self.start()

    async def dahdi(self):
        await self.start()

    async def start(self):
        await self.agi.answer()
        try:
            # await self.get_id()
            logger.info(f"Getting ID {self.config}")
            id_number = await self.get_information(self.config["idn"]["regexp"],
                                                   self.config["sounds"]["enter_id"],
                                                   func_slide=self.config["idn"]["slider"],
                                                   tries=self.config["idn"]["max_attemps"],
                                                   optionList=["1", "0"]
                                                   )
            id_field = self.config["idn"]["field"]
            self.user[id_field] = id_number
            logger.info(f"ID Number: {id_number}")
            logger.info(f'Request: {self.config["request"]}')

            http_request = self.config["request"]["url"]
            if http_request and id_number:
                user_info = await self.http_request(http_request,
                                                    params={id_field: id_number},
                                                    auth_data=self.config["request"]["auth"],
                                                    timeout=self.config["request"]["timeout"]
                                                    )
            else:
                user_info = {}

            logger.info(f"User: {self.user}")
            logger.info(f"ID Number: {user_info}")
            if user_info:
                self.user.update(user_info)

        except Exception as error:
            logger.info(error)
            self.status = 'ERROR'

        await self.set_custom_vars()

    async def choose_option(self, audioPrompt, optionList=['1', '2', '*'], tries=3):
        logger.info(f"Starting choose_option with {audioPrompt}")
        sounds = self.config["sounds"]["choose-option"]
        attemps = 0
        while not tries or attemps < tries:
            attemps = attemps + 1
            response = await self.agi.get_data(audioPrompt, timeout=2500, max_digits=1)
            result, _ = response.result, response.info == "(timeout)"
            if not result and 'T' in optionList:
                result = 'T'
            if result not in optionList:
                if not result:
                    await self.agi.stream_file(sounds["empty"])
                else:
                    await self.agi.stream_file(sounds["invalid"])
                if not tries or attemps < tries:
                    await self.agi.stream_file(sounds["try-again"])
            else:
                event, info = ("TIMEOUT", "NONE") if result == 'T' else ("OPTION", result)
                return result
        return None

    async def get_information(self, regExp, sounds, func_slide=None, tries=3,
                              confirm=3, timeout=2500, max_digits=255, cancel=None,
                              optionList=["1", "2", "*"]):
        attemps = 0
        try_again = False
        while tries is None or attemps < tries:
            if attemps > 0 and try_again and sounds.get("try-again"):
                await self.agi.stream_file(sounds.get("try-again"))
            attemps += 1
            response = await self.agi.get_data(sounds.get("prompt"),
                                               timeout=timeout, max_digits=max_digits)
            result, timeout = response.result, response.info == "(timeout)"
            if not result:
                if sounds.get("empty", sounds.get("invalid")):
                    await self.agi.stream_file(sounds.get("empty", sounds.get("invalid")))
                try_again = True
            elif result == cancel:
                return None
            elif not re.search(regExp, result):
                if sounds.get("invalid"):
                    await self.agi.stream_file(sounds.get("invalid"))
                try_again = True
            else:
                if func_slide:
                    await self.agi.stream_file(sounds.get("number-is"))
                    digits_dir = self.config["sounds"]["digits"]
                    func = getattr(self, func_slide)
                    for slide in func(result):
                        await self.agi.stream_file(f"{digits_dir}/{slide}")
                    choice = await self.choose_option(sounds.get("confirm"),
                                                      optionList, tries=confirm)
                    if not choice and (tries is None or attemps < tries):
                        await self.agi.stream_file(sounds.get("repeat"))
                        try_again = False
                    elif choice == '1':
                        return result
                else:
                    return result
        return None

    async def http_request(self, url, method="GET", params=None, auth_data=None,
                           json_data=None, headers=None, json_result=True, timeout=5):

        if auth_data and auth_data.get("login"):
            auth = aiohttp.BasicAuth(**auth_data)
        else:
            auth = None

        if timeout:
            timeout = aiohttp.ClientTimeout(total=timeout)

        logger.debug(f"{url}, {params}")
        async with self.http_client.request(method, url,
                                            auth=auth,
                                            params=params,
                                            json=json_data,
                                            headers=headers,
                                            timeout=timeout
                                            ) as resp:
            logger.debug(f"Response: {resp}")
            if json_result:
                try:
                    response = await resp.json(content_type=None)
                except Exception as error:
                    logger.error(f"Something failed trying to convert result into json: {error}")
                    response = await resp.text()
            else:
                response = await resp.text()

            logger.info(f"Response: {response}")

            return response

    async def set_custom_vars(self):
        fmt = PartialFormatter()
        vars_dict = self.config["variables"]
        for var, value in vars_dict.items():
            if type(value) is str:
                value = fmt.format(value, **self.user)
            logger.info(f"Setting '{var}' to '{value}'")
            await self.agi.set_variable(var, value)


if __name__ == '__main__':
    logging.config.dictConfig(LOGGING)
    app = AGIApplication()
    app.router.add_route('*', '', GetIDView)
    runner.run_app(app)
