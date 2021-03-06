"""
This module defines dictionaries, functions and classes to run the ognon servers.
"""

import http.server
import json
import os
import importlib
import threading
import logging
import traceback
from urllib.parse import urlparse

import pythonosc.osc_server
import pythonosc.dispatcher

from . import cursor
from . import control
from . import utils

functions = {}
cursors = {}

http_server = None
osc_server = None

def get_function(path):
    """
    Return a function from the functions dict.

    If the asked function does not exists in the dict, import it, store it in
    the dict and return it.
    """
    try:
        return functions[path]
    except KeyError:
        module_path, fun_name = os.path.split(path.rstrip(os.sep))
        module = importlib.import_module(
            name=module_path.replace(os.sep,'.'),
            package='ognon')
        functions[path] = getattr(module, fun_name)
        return functions[path]

def call_function(path, *args, **kwargs):
    """
    Get a function with get_function, call it with passed args/kwargs and
    return the result.
    """
    def handle_error(*err_msg):
        logging.warning('An error occurred during the call to {path}\n\t{error}'
            .format(path=path, error='\n\t'.join(err_msg)))
        raise Exception(*err_msg)

    try:
        f = get_function(path)
    except (ImportError, AttributeError):
        handle_error('Function not found')

    try:
        return f(*args, **kwargs)
    except NotImplementedError:
        handle_error('Not implemented')
    except cursor.UndefinedProjectError:
        handle_error('Undefined project',
            'You must first get a project.')
    except control.exporter.ExportDestNotFoundError:
        handle_error('Destination not found',
            'You must save the project before exporting it.')
    except control.projectmanager.ProjectNotFoundError:
        handle_error('Project not found',
            'You can\'t load a project that does not exists. Save it first.')
    except Exception:
        traceback.print_exc()
        handle_error('Oups...')


def get_cursor(name='default'):
    """
    Return a cursor from the cursors dict.

    If the asked cursor does not exists, store a new cursor in the dict and
    return it.
    """
    try:
        return cursors[name]
    except KeyError:
        cursors[name] = cursor.Cursor()
        return cursors[name]


class OgnonHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """
    This class is used to handle the HTTP requests that arrive at the server.

    We wait two kinds of requests :
    
    - GET requests to provide client pages.
    - POST requests to call functions from ognon.
    """

    def log_message(self, format, *args):
        # The default server log is redirected to logging.DEBUG.
        logging.debug(format%args)

    def write(self, *args):
        """
        Wrapper for the wfile.write method used to handle BrokenPipeError.
        """
        try:
            self.wfile.write(*args)
        except BrokenPipeError:
            logging.warning('BrokenPipeError')

    def do_GET(self):
        """
        Handler for GET request.
        """
        logging.info('http - GET {path}'.format(path=self.path))
        path = urlparse(self.path).path
        if path == '/':
            path = '/edit.html'

        file_path = utils.pkgabspath('client') + path
        content = ''
        mimetype = self.guess_type(file_path)

        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                content = f.read()
        except FileNotFoundError:
            with open(utils.pkgabspath('client/404.html'), 'rb') as f:
                self.send_response(404)
                content = f.read()


        self.send_header('Content-type', mimetype)
        self.end_headers()
        self.write(content)

        
    def do_POST(self):
        """
        Handler for POST request.

        The path tell which function to call. Args are given in the post body.
        Convert the function to json and send it as a response.
        If calling the function raise an exception, send an error message
        """
        logging.info('http - POST {path}'.format(path=self.path))

        content_len = int(self.headers.get('content-length', 0))
        post_body = json.loads(self.rfile.read(content_len).decode('utf-8'))
        if 'cursor' in post_body:
            post_body['cursor'] = get_cursor(post_body.get('cursor'))
        try:
            reply = call_function(self.path, **post_body)
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.write(bytes('\n'.join(e.args), 'utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.write(bytes(json.dumps(reply, cls=utils.SetEncoder), 'utf-8'))

    def end_headers (self):
        #TODO: check if this is really useful ! 
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET')
        http.server.SimpleHTTPRequestHandler.end_headers(self)


class OgnonOSCDispatcher(pythonosc.dispatcher.Dispatcher):
    """This is the class of the OSC dispatcher."""

    def handlers_for_address(self, address_pattern):
        """yields Handler namedtuples matching the given OSC pattern."""
        logging.info('osc - {path}'.format(path=address_pattern))

        def callback(path, cursor_id, *args):
            call_function(path, get_cursor(cursor_id), *args)

        yield pythonosc.dispatcher.Handler(callback, [])


def serve(http_address, osc_address, enable_osc=True):
    """
    Serve forever on the given addresses.

    Start to threading servers, an http server and an osc server.
    Set enable_osc to False to disable starting osc server thread.
    """
    global http_server, osc_server

    dispatcher = OgnonOSCDispatcher()
    osc_server = pythonosc.osc_server.OSCUDPServer(osc_address, dispatcher)
    osc_server_thread = threading.Thread(target=osc_server.serve_forever)

    http_server = http.server.HTTPServer(http_address, OgnonHTTPHandler)
    http_server_thread = threading.Thread(target=http_server.serve_forever)

    if enable_osc:
        osc_server_thread.start()
    http_server_thread.start()

def stop_serving():
    """
    Strop serving forever.
    """
    global http_server, osc_server
    http_server.shutdown()
    osc_server.shutdown()
