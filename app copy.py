from quart import Quart, session, render_template, request, stream_with_context
from datastar_py.sse import ServerSentEventGenerator as SSE
from datastar_py.quart import make_datastar_response

from tinydb import TinyDB
import redis.asyncio as redis

import time
import asyncio
from random import choice


# CONFIG

app = Quart(__name__)
app.secret_key = 'a_secret_key'

db = TinyDB("data.json", sort_keys=True, indent=4)
gif_table = db.table('gifs')
mp3_table = db.table('mp3')
current_table = db.table('current')

# redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# UTILS


# VIEWS

async def main_view(current):
    mp3 = current['mp3']
    alias = current['mp3_alias']
    mp3_length = current['mp3_length']
    mp3_start = current['mp3_start']
    mp3_delay = round(time.time() - mp3_start)
    gif = current['gif']
    gif_start = current['gif_start']
    gif_delay = round(time.time() - gif_start)
    return f'''
<main 
id="main"
data-signals="{{rem: {mp3_length - mp3_delay}}}"
data-signals__ifmissing="{{vol: 2, play:0, expand:1}}"
data-on-interval="$rem--"
>
    <audio 
    data-ref="audio" 
    src="../static/mp3/{mp3}.opus#t={mp3_delay}" 
    data-on-signal-change="el.volume = $vol / 10" 
    loop></audio>
    <video id="bg-video" autoplay muted loop playsinline>
        <source src="../static/gif/{gif}#t={gif_delay}" type="video/mp4">
    </video>
    <div id="top" class="gt l">
        <p>nurad.io</p>
    </div>
    <div id="bot" class="gc">
        <div id="cover" class="gc" data-class="{{'g01': $expand}}">
            <img src="../static/img/{mp3}.jpg" data-on-click__viewtransition="$expand = !$expand">
            <div class="g01v gc" data-show="$expand">
                <p 
                id="trigger"
                data-text="$play ? 'Now playing' : 'Listen'"
                data-attr-initial="!$play"
                data-on-click="$play = !$play; $play ? $audio.play() : $audio.pause()"
                class="accent gt xs">Now playing</p>
                <p id="title" class="gt m">
                {alias}
                </p>
            </div>
        </div>
        <div id="player" data-show="$expand">
            <p class="accent">Rem:</p>
            <p data-text="Math.floor($rem / 60) + ':' + ($rem % 60 < 10 ? '0' : '') + ($rem % 60)"></p>
            <p class="accent">Vol:</p>
            <button
            id="vol-down"
            data-on-click="$vol = Math.max(0, Math.min(10, $vol - 1))"></button>
            <p data-text="$vol"></p>
            <button
            id="vol-up"
            data-on-click="$vol = Math.max(0, Math.min(10, $vol + 1))"></button>
        </div>
        <div class="gt xs" data-show="$expand">
            <a href="https://soundcloud.com/nura666/{mp3}">soundcloud.com/nura666/{mp3}</a>
        </div>
    </div>
</main>
'''

# APP

@app.before_serving
async def startup():
    asyncio.create_task(radio_station())
    # asyncio.create_task(gif_station())

async def radio_station():
    while True:
        songs = mp3_table.all()
        song = choice(songs)
        gifs = gif_table.all()
        gif = choice(gifs)
        current_table.update({
            'mp3': song['name'],
            'mp3_alias': song['alias'],
            'mp3_length': song['length'],
            'mp3_start': time.time(),
            'gif': gif['name'],
            'gif_start': time.time()
        }, doc_ids=[1])
        # await redis_client.publish('nura', 'new nura just dropped')
        # await asyncio.sleep(song['length'])
        await asyncio.sleep(10)

# async def gif_station():
#     while True:
#         await redis_client.publish('nura', 'new nura just dropped')
#         print("changed gif")
#         await asyncio.sleep(3)

# ROUTES

@app.before_request
async def before_request():
    if not session.get('last_update'): 
        session['last_update'] = 0

@app.get('/')
async def index():
    return await render_template('index.html')

@app.get('/main')
async def main():
    @stream_with_context
    async def event():
        current = current_table.get(doc_id=1)
        html = await main_view(current)
        yield SSE.merge_fragments(fragments=[html])
        while True:
            try:
                current = current_table.get(doc_id=1)
                if current['mp3_start'] > session['last_update']:
                    session['last_update'] = current['mp3_start']
                    html = await main_view(current)
                    yield SSE.merge_fragments(fragments=[html])
                    yield SSE.execute_script(script="document.querySelector('audio').play(); document.querySelector('video').load();")
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    return await make_datastar_response(event())

if __name__ == '__main__':
    app.run(debug=True)
