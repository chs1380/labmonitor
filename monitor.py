# https://github.com/moses-palmer/pynput/issues/52
import urllib
from queue import Queue

from pynput import keyboard
from pynput import mouse

from threading import Thread
import multiprocessing
import sys, getopt
from Model.EventListener import EventListener
from Model.Watcher import Watcher
from urllib import request, parse
import json

api = None
key = None
q = Queue()


def worker():
    while True:
        queue_size = q.qsize()
        if queue_size > 10:
            print("Batch processing for " + str(queue_size) + " events")
            events = []
            for i in range(queue_size):
                item = q.get()
                print("worker: " + str(item))
                d = item.__dict__
                d["event"] = item.__class__.__name__
                events.append(item.__dict__)
                q.task_done()

            try:
                req = request.Request(api + "event", data=json.dumps(events).encode('utf8'))
                resp = request.urlopen(req)
                print(resp)
            except Exception  as e:  # This is the correct syntax
                print(e)


def file_monitor():
    w = Watcher(api, key)
    w.run()


def input_monitor():
    t = Thread(target=worker)
    t.start()

    event_listener = EventListener(q)

    with mouse.Listener(on_move=event_listener.on_move, on_click=event_listener.on_click,
                        on_scroll=event_listener.on_scroll) as listener:
        with keyboard.Listener(on_press=event_listener.on_press, on_release=event_listener.on_release) as listener:
            listener.join()


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "a:k:")
    except getopt.GetoptError:
        print('monitor.py -a <url> -k <apikey>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('monitor.py -a <url> -k <apikey>')
            sys.exit()
        elif opt == '-a':
            global api
            api = arg
        elif opt == '-k':
            global key
            key = arg
    print('api is "', api)
    print('key is "', key)

    if api is None or key is None:
        sys.exit()

    jobs = [multiprocessing.Process(target=file_monitor), multiprocessing.Process(target=input_monitor)]

    # Start the processes (i.e. calculate the random number lists)
    for j in jobs:
        j.start()

    # Ensure all of the processes have finished
    for j in jobs:
        j.join()

    print("List processing complete.")


if __name__ == '__main__':
    main(sys.argv[1:])