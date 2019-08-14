import argparse
import asyncio
import json
import logging
from logging import config as logging_config

from aiohttp import web
from aiohttp.web_response import Response

parser = argparse.ArgumentParser()
parser.add_argument('--port', default=5000, type=int)


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [None for x in obj if x is None] + sorted(ordered(x) for x in obj if x is not None)
    else:
        return obj


class Server:
    """Server to emulate router bot and DeepPavlov model launched as REST Api.

    DeepPavlov model on each infer returns tuple with upper text and unchanged infer.

    Example:
        'Infer' -> ('INFER', 'Infer')

    Server endpoints:
        /bot{token}/getUpdates (get): Returns messages from user.
        /bot{token}/sendMessage (post): Receives payload that passed to DeepPavlov model.
        /answer (post): Endpoint emulates DeepPavlov REST API endpoint.
        /newTest (post): Add messages from user

    """
    _loop: asyncio.events.AbstractEventLoop

    def __init__(self, port: int) -> None:
        self._poller_input = []
        self._model_input = ''
        self._expected_output = set()
        self._convai = False
        self._state = False
        with open('../config.json', 'r') as config_file:
            config = json.load(config_file)
        logging_config.dictConfig(config['logging'])
        self._log = logging.root.manager.loggerDict['wrapper_logger']
        self._loop = asyncio.get_event_loop()
        self._app = web.Application(loop=self._loop)
        self._app.add_routes([web.get('/bot{token}/getUpdates', self._handle_updates),
                              web.post('/bot{token}/sendMessage', self._handle_message),
                              web.post('/answer', self._dp_model),
                              web.post('/newTest', self._set_new_test)])
        web.run_app(self._app, port=port)

    async def _dp_model(self, request: web.Request) -> Response:
        data = await request.json()
        self._test_result['model_input_correct'] = (ordered(data) == ordered(self._model_input))
        ret = []
        if self._state is False:
            for message in data['text1']:
                if self._convai is True:
                    text = message['payload']['text']
                    command = message['payload']['command']
                else:
                    text = message
                    command = None
                resp_list = [text.upper(), text] if command is None else [command]
                ret.append(resp_list)
        else:
            for message, state in zip(data['text1'], data['state']):
                if self._convai is True:
                    text = message['payload']['text']
                    command = message['payload']['command']
                else:
                    text = message
                    command = None
                history = [] if state is None else state
                if command is not None:
                    history.append(command)
                    resp_list = [command, history]
                else:
                    history.append(text)
                    resp_list = [text.upper(), history]
                ret.append(resp_list)
        return web.json_response(ret)

    async def _handle_updates(self, request: web.Request) -> Response:
        res = self._poller_input
        self._poller_input = []
        return web.json_response({'result': res})

    async def _handle_message(self, request: web.Request) -> Response:
        data = await request.json()
        self._gen_messages.append(data)
        if ordered(self._expected_output) == ordered(self._gen_messages):
            self._test_result['poller_output_correct'] = True
            self._event.set()
        return web.Response(status=200)

    async def _set_new_test(self, request: web.Request) -> Response:
        """Sets test data.

        Request must contain dictionary with following keys:
            'updates' (list): Messages from router bot.
            'model_input' (str): Serialized JSON object that router bot poller should send to the DeepPavlov model.
            'send_messages' (List[str]): Each item is serialized JSON object that poller sends to router bot's
                /sendMessage endpoint.

        """
        self._event = asyncio.Event()
        self._test_result = {'model_input_correct': False, 'poller_output_correct': False}
        self._loop.create_task(self._timer())
        data = await request.json()
        self._poller_input = data['poller_input']
        self._model_input = data['model_input']
        self._expected_output = data['expected_output']
        self._convai = data['convai']
        self._state = data['state']
        self._gen_messages = []
        await self._event.wait()
        return web.json_response(self._test_result)

    async def _timer(self):
        await asyncio.sleep(10)
        self._log.info('timer called event.set()')
        self._event.set()

if __name__ == '__main__':
    args = parser.parse_args()
    Server(args.port)
