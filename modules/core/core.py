from ..typecheck import *

import sublime
import threading
import concurrent

from ..libs import asyncio
from .log import log_exception
from .error import Error
from .sublime_event_loop import SublimeEventLoop

T = TypeVar('T')

awaitable = Generator[Any, Any, T]
coroutine = asyncio.coroutine
future = asyncio.Future
CancelledError = asyncio.CancelledError

sublime_event_loop = SublimeEventLoop()
sublime_event_loop_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
asyncio.set_event_loop(sublime_event_loop)

def call_soon_threadsafe(callback, *args):
	return sublime_event_loop.call_soon(callback, *args)

def call_soon(callback, *args):
	return sublime_event_loop.call_soon(callback, *args)

def call_later(interval, callback, *args):
	return sublime_event_loop.call_later(interval, callback, *args)

def create_future():
	return sublime_event_loop.create_future()

def run_in_executor(func, *args):
	return asyncio.futures.wrap_future(sublime_event_loop_executor.submit(func, *args), loop=sublime_event_loop)

def all_methods(decorator):
	def decorate(cls):
		for attribute in cls.__dict__:
			if callable(getattr(cls, attribute)):
				setattr(cls, attribute, decorator(getattr(cls, attribute)))
		return cls
	return decorate

'''decorator for requiring that a function must be run in the background'''
def require_main_thread(function):
	def wrapper(*args, **kwargs):
		assert_main_thread()
		return function(*args, **kwargs)
	return wrapper


def auto_run(function):
	def wrapper(*args, **kwargs):
		function = function(*args, **kwargs)
		core.run(function)
		return coroutine
	return wrapper


def run(awaitable: awaitable[T], on_done: Callable[[T], None] = None, on_error: Callable[[Exception], None] = None) -> asyncio.Future:
	task = asyncio.ensure_future(awaitable, loop=sublime_event_loop)

	def done(task) -> None:
		exception = task.exception()

		if on_error and exception:
			on_error(exception)

			try:
				raise exception
			except Exception as e:
				log_exception()

			return

		result = task.result()
		if on_done:
			on_done(result)

	task.add_done_callback(done)
	return task

def assert_main_thread() -> None:
	assert is_main_thred(), 'expecting main thread'

def is_main_thred() -> bool:
	return isinstance(threading.current_thread(), threading._MainThread)

def display(msg: 'Any') -> None:
	sublime.error_message('{}'.format(msg))
