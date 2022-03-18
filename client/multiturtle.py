from inspect import isclass
import turtle
import uuid
import asyncio
import socketio
import requests
from enum import Enum,IntEnum
from collections import defaultdict
from threading import Thread
from queue import Queue
import gc

class ConnectionType(Enum):
    DISCONNECTED = 0
    LEADER = 1
    CLIENT = 2

class ActionType(IntEnum):
    CLASS_CREATE = 1
    CLASS_METHOD = 2
    DIRECT_METHOD = 3
    JOIN = 4

proxies = dict()

conn = {"tp": ConnectionType.DISCONNECTED, "name": None}
socket = socketio.Client()

user_instances = defaultdict(dict) # user => (instance id => class instance)

message_queue = Queue()

def process_global_method(method,args,kwargs):
    if conn["tp"] == ConnectionType.CLIENT:
        socket.emit("publish_action", {"type": int(ActionType.DIRECT_METHOD), "method": str(method), "args": args, "kwargs": kwargs})

def process_class_method(instance, method, args, kwargs):
    if conn["tp"] == ConnectionType.CLIENT:
        socket.emit("publish_action", {"type": int(ActionType.CLASS_METHOD), "id": conn["name"], "instance": instance, "method": method, "args": args, "kwargs": kwargs})

def process_class_init(cl, instance, args, kwargs):
    if conn["tp"] == ConnectionType.CLIENT:
        socket.emit("publish_action", {"type": int(ActionType.CLASS_CREATE), "class": cl, "args": args, "kwargs": kwargs, "instance": instance, "id": conn["name"]})

def create_method_proxy(method,before=None,after=None):
    def f(*args,**kwargs):
        if before:
            before(method, args, kwargs)
        result = method(*args,**kwargs)
        if after:
            after(method, args, kwargs)
        return result
    return f

def create_class_proxy(cls,init_callback=None,method_callback_before=None,method_callback_after=None):
    def optional_callback(instance_id,name,cb):
        def wrapper(method,args,kwargs):
            if cb:
                cb(instance_id,name,args,kwargs)
        return wrapper

    class Proxied:
        def __init__(self, *args, **kwargs):
            self.id = uuid.uuid4().hex
            self._instance = cls(*args,**kwargs)
            for public in list(filter(lambda x: not x.startswith("__"), dir(self._instance))):
                if callable(self._instance.__getattribute__(public)):
                    self.__setattr__(
                        public,
                        create_method_proxy(
                            self._instance.__getattribute__(public),
                            optional_callback(self.id, public, method_callback_before),
                            optional_callback(self.id, public, method_callback_after)
                        )
                    )
            if init_callback:
                init_callback(self.id,args,kwargs)
    return Proxied

def find_or_create_method_proxy(method, proxied):
    if method in proxies:
        return proxies[method]
    else:
        proxies[method] = create_method_proxy(proxied.__dict__[method], before=lambda x,y,z: process_global_method(method, y, z))
        return proxies[method]

def find_or_create_class_proxy(cls, proxied):
    if cls in proxies:
        return proxies[cls]
    else:
        proxies[cls] = create_class_proxy(proxied.__dict__[cls], method_callback_before=process_class_method, init_callback=lambda x,y,z: process_class_init(cls, x, y, z))
        return proxies[cls]

def create_room():
    r = requests.post("http://localhost:8080/create_room")
    data = r.json()
    return data["room_id"], data["leader_id"]

def join_room(room, name, role):
    r = requests.post("http://localhost:8080/join_request", json={"room_id": room, "user_id": name, role: role})
    data = r.json()
    return data["status"]

def connect(room:str,name:str):
    # connecting as a client
    try:
        status = join_room(room, name, "student")
        if status != "accepted":
            raise Exception("Not accepted to room")
        else:
            conn["tp"] = ConnectionType.CLIENT
            conn["name"] = name
            socket.connect("http://localhost:8080")
            socket.emit('join_room', {'room_id': room, 'id': name, 'role': 'student'})
    except Exception:
        print("Could not connect to room. Continuing in local mode.")

def disconnect():
    socket.disconnect()

def wait_for_sockets():
    @socket.event
    def client_action(data):
        message_queue.put(data)
    @socket.event
    def client_join(data):
        message_queue.put({"type": ActionType.JOIN, "id": data["id"]})
    socket.wait()

def start_share():
    try:
        room, leader = create_room()
        conn["tp"] = ConnectionType.LEADER
        socket.connect("http://localhost:8080")
        conn["name"] = leader
        socket.emit('join_room', {'room_id': room, 'id': leader, 'role': 'leader'})
        print("Leading room " + str(room))
        turtle.Screen().setup()
        socket_thread = Thread(target=wait_for_sockets)
        socket_thread.start()
        event_responder()
    except Exception as e:
        print(e)
        print("Could not create room. Continuing in local mode.")

def event_responder():
    while True:
        data = message_queue.get()
        action_type = data["type"]
        if action_type == ActionType.CLASS_CREATE:
            cl = data["class"]
            args = data["args"]
            kwargs = data["kwargs"]
            instance_id = data["instance"]
            user_id = data["id"]
            user_instances[user_id][instance_id] = turtle.__dict__[cl](*args,**kwargs)
        elif action_type == ActionType.CLASS_METHOD:
            user_id = data["id"]
            instance_id = data["instance"]
            args = data["args"]
            kwargs = data["kwargs"]
            method = data["method"]
            if instance_id in user_instances[user_id]:
                getattr(user_instances[user_id][instance_id], method)(*args,**kwargs)
        elif action_type == ActionType.JOIN:
            user_id = data["id"]
            if user_id in user_instances:
                for instance_id in user_instances[user_id]:
                    user_instances[user_id][instance_id].clear()
                    user_instances[user_id][instance_id].reset()
                    user_instances[user_id][instance_id].hideturtle()
                del user_instances[user_id]
                gc.collect()

def __getattr__(name):
    if name[0] != '_' and name[1] != '_':
        if isclass(turtle.__dict__[name]):
            return find_or_create_class_proxy(name, turtle)
        if callable(turtle.__dict__[name]):
            return find_or_create_method_proxy(name, turtle)