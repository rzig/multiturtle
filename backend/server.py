from aiohttp import web
import socketio
import uuid
import random
import string
from collections import defaultdict

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
routes = web.RouteTableDef()

def create_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def create_client_id():
    return str(uuid.uuid4())

rooms = set()
room_leaders = defaultdict(list)

subscribers = defaultdict(list) # map room => *active* sockets subscribed
socket_to_room = defaultdict(str) # map all socket => room id
roles = defaultdict(str) # map socket id => role
id_to_name = defaultdict(str)

@routes.post("/create_room")
async def create_room(request: web.Request):
    room_id = create_room_id()
    leader_id = create_client_id()
    rooms.add(room_id)
    room_leaders[room_id].append(leader_id)
    return web.json_response({"room_id": room_id, "leader_id": leader_id})

@routes.post("/join_request")
async def join_request(request: web.Request):
    data = await request.json()
    room_id = data["room_id"]
    user_id = data["user_id"]
    if not room_id in rooms:
        return web.json_response({"status": "error", "reason": "room does not exist"})
    else:
        # no authentication for now
        await sio.emit("client_join", {"id": user_id}, room=room_id)
        return web.json_response({"status": "accepted"})

@sio.event
def connect(sid, environ):
    print("connect ", sid)

@sio.event
async def join_room(sid, data):
    room_id = data["room_id"]
    client_id = data["id"]
    role = data["role"]
    if role == "leader":
        if client_id in room_leaders[room_id]:
            subscribers[room_id].append(sid)
        sio.enter_room(sid, room_id)
    socket_to_room[sid] = room_id
    roles[sid] = role
    id_to_name[sid] = client_id

@sio.event
async def publish_action(sid,data):
    await sio.emit("client_action", data, room=socket_to_room[sid])

@sio.event
async def disconnect(sid):
    room = socket_to_room[sid]
    role = roles[sid]
    del socket_to_room[sid]
    del roles[sid]
    if role == "leader":
        subscribers[room] = list(filter(lambda x: x != sid, subscribers[room]))
        sio.leave_room(sid, room)
    else:
        await sio.emit("remote_disconnect", id_to_name[sid], room=room)
        del id_to_name[sid]

app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app)