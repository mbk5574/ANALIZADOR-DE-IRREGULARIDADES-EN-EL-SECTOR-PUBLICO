# corruption_detector/__init__.py

import sys
import asyncio
from asyncio.proactor_events import _ProactorBaseWritePipeTransport

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    orig = _ProactorBaseWritePipeTransport._loop_writing

    def _loop_writing(self, *args, **kwargs):
        try:
            return orig(self, *args, **kwargs)
        except AssertionError:
            return  

    _ProactorBaseWritePipeTransport._loop_writing = _loop_writing
