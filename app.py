from quart import Quart, session, render_template, stream_with_context
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.quart import DatastarResponse

from tinydb import TinyDB
from dotenv import load_dotenv
# import redis.asyncio as redis

import os
import time
import asyncio
from random import choices


# CONFIG

load_dotenv()

app = Quart(__name__)
app.config['SECRET_KEY'] = os.getenv('QUART_SECRET_KEY')

db = TinyDB("data.json", sort_keys=True, indent=4)
gif_table = db.table('gifs')
mp3_table = db.table('mp3s')
current_table = db.table('current')

# UTILS


# VIEWS

async def main_view(current):
    mp3 = current['mp3']
    alias = current['mp3_alias']
    mp3_length = current['mp3_length']
    mp3_start = current['mp3_start']
    mp3_delay = round(time.time() - mp3_start)
    next_start = mp3_start + mp3_length
    gif = current['gif']
    return f'''
    <main 
    id="main"
    data-signals="{{rem: {mp3_length - mp3_delay}, next_start: {next_start}}}"
    data-signals__ifmissing="{{vol: 2, play:0, expand:1}}"
    data-on-interval="$rem--; if (Date.now() > {next_start} * 1000) {{ @get('/main'); }}"
    >
        <audio 
        data-ref="audio" 
        src="../static/mp3/{mp3}.opus#t={mp3_delay}" 
        data-on-signal-change="el.volume = $vol / 10" 
        loop></audio>
        <video id="bg-video" autoplay muted loop playsinline src="../static/gif/{gif}" type="video/mp4"></video>
        <div id="top" class="gt l">
            <p>nurad.io</p>
        </div>
        <div id="bot" class="gc">
            <div id="cover" class="gc" data-class="{{'g01': $expand}}">
                <img src="../static/img/{mp3}.jpg" data-on-click__viewtransition="$expand = !$expand">
                <div class="g01v gc" data-show="$expand">
                    <button
                    id="trigger"
                    data-text="$play ? 'Now playing' : 'Listen'"
                    data-attr-initial="!$play"
                    data-on-click="$play = !$play; @post('/play')"
                    class="accent gt xs">
                    Now playing
                    </button>
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

async def radio_station():
    while True:
        songs = mp3_table.all()
        weights = [song.get('played') for song in songs]
        max_weight = max(weights) + 1
        weights = [max_weight - weight for weight in weights]
        song = choices(songs, weights)[0]
        current_table.update({
            'mp3': song['name'],
            'mp3_alias': song['alias'],
            'mp3_length': song['length'],
            'mp3_start': time.time(),
        }, doc_ids=[1])
        mp3_table.update({'played': song['played'] + 1}, doc_ids=[song.doc_id])

        gifs = gif_table.all()
        weights = [gif.get('played') for gif in gifs]
        max_weight = max(weights) + 1
        weights = [max_weight - weight for weight in weights]
        gif = choices(gifs, weights)[0]
        current_table.update({
            'gif': gif['name'],
            'gif_start': time.time()
        }, doc_ids=[1])
        gif_table.update({'played': gif['played'] + 1}, doc_ids=[gif.doc_id])

        await asyncio.sleep(song['length'])

# ROUTES

@app.before_request
async def before_request():
    if not session.get('playing'): 
        session['playing'] = 0

@app.get('/')
async def index():
    return await render_template('index.html')

@app.get('/main')
async def main():
    @stream_with_context
    async def event():
        current = current_table.get(doc_id=1)
        html = await main_view(current)
        yield SSE.merge_fragments(html)
        yield SSE.execute_script("document.querySelector('video').load()")
        if session['playing']:
            yield SSE.execute_script("document.querySelector('audio').play()")
            yield SSE.merge_signals({'play': 1})
    return DatastarResponse(event())

@app.post('/play')
async def play():
    session['playing'] = not session['playing']
    return await main()

# if __name__ == '__main__':
#     app.run(debug=True)
