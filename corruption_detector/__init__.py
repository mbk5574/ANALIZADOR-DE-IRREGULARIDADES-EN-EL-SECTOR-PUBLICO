# corruption_detector/__init__.py

import sys
import asyncio
from asyncio.proactor_events import _ProactorBaseWritePipeTransport

if sys.platform.startswith("win"):
    # 1) Forzar el SelectorEventLoopPolicy en Windows y de esta manera evitamos el error de bajo nivel de asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    orig = _ProactorBaseWritePipeTransport._loop_writing

    def _loop_writing(self, *args, **kwargs):
        try:
            return orig(self, *args, **kwargs)
        except AssertionError:
            return  

    _ProactorBaseWritePipeTransport._loop_writing = _loop_writing
