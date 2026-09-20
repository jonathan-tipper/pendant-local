"""Offline speaker model integrity, word attribution and durable workflow contracts."""
import asyncio
from copy import deepcopy
import hashlib
import json
import sys
import tarfile
import threading
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from pendant_api import diarization as d
from pendant_api.config import atomic_json
from pendant_api.transcription import TranscriptionQueue, _normalise_result, _transcribe_local
from test_transcription import Store, prepared_model, until, status_of
from test_workspace import make_workspace, wav_bytes

WORDS = {'text': 'Hello there. Good morning.', 'duration': 4, 'language': 'en',
         'segments': [{'start': 0, 'end': 4, 'text': 'Hello there. Good morning.', 'words': [
             {'start': 0, 'end': 1, 'word': ' Hello'}, {'start': 1, 'end': 2, 'word': ' there.'},
             {'start': 2, 'end': 3, 'word': ' Good'}, {'start': 3, 'end': 4, 'word': ' morning.'}]}]}
TURNS = [{'start': 0, 'end': 2, 'speaker': 7}, {'start': 2, 'end': 4, 'speaker': 3}]


@pytest.fixture
def speaker_models(monkeypatch):
    payload = b'test-only model'
    monkeypatch.setattr(d, 'FILES', {name: hashlib.sha256(payload).hexdigest() for name in d.FILES})
    def install(path):
        path.mkdir(parents=True, exist_ok=True)
        for name in d.FILES:
            (path / name).write_bytes(payload)
        (path / 'SEGMENTATION-LICENSE').write_text('fixture licence')
        (path / 'ATTRIBUTION.txt').write_text('fixture attribution')
    return install


def ready(root, install):
    path = root / 'models' / d.MODEL_ID
    install(path)
    atomic_json(path / '.prepared.json', {'model': d.MODEL_ID})
    return path


def test_word_attribution_splits_turns_and_preserves_original_text():
    result = d.label_transcript(_normalise_result(WORDS), list(reversed(TURNS)), 2)
    assert result['speakers'] == {'speaker_1': 'Speaker 1', 'speaker_2': 'Speaker 2'}
    assert result['segments'] == [
        {'start': 0, 'end': 2, 'text': 'Hello there.', 'speaker': 'speaker_1'},
        {'start': 2, 'end': 4, 'text': 'Good morning.', 'speaker': 'speaker_2'}]
    assert result['text'] == WORDS['text']
    assert result['diarization']['requested_speakers'] == 2
    assert result['diarization']['unassigned_segments'] == 0


def test_overlap_unmatched_and_missing_words_are_honest_and_lossless():
    turns = [{'start': 1, 'end': 4, 'speaker': 0}, {'start': 2, 'end': 4, 'speaker': 1}]
    result = d.label_transcript(deepcopy(WORDS), turns)
    assert result['segments'][0]['speaker'] is None  # undetected first word
    assert result['segments'][-1]['speaker'] is None  # overlapping speakers
    assert ' '.join(s['text'] for s in result['segments']) == WORDS['text']
    for words in (None, [], [{'start': 0, 'end': 1, 'word': 'Missing text'}]):
        original = deepcopy(WORDS)
        if words is None:
            original['segments'][0].pop('words')
        else:
            original['segments'][0]['words'] = words
        labelled = d.label_transcript(original, TURNS)
        assert labelled['segments'][0]['speaker'] is None
        assert labelled['segments'][0]['text'] == original['text']


def test_silence_has_no_invented_speakers_and_invalid_turns_fail():
    empty = {'text': '', 'duration': 2, 'language': 'en', 'segments': []}
    assert d.label_transcript(empty, [])['diarization']['speaker_count'] == 0
    for turn in ({'start': float('nan'), 'end': 2, 'speaker': 0}, {'start': 0, 'end': 2, 'speaker': -1}):
        with pytest.raises(ValueError):
            d.label_transcript(WORDS, [turn])


@pytest.mark.parametrize('enabled,count', [(False,2),(True,0),(True,21),(True,True),(True,2.5),('true',None)])
def test_option_validation(enabled, count):
    with pytest.raises(ValueError):
        d.validate_options(enabled, count)


def test_model_readiness_detects_missing_corrupt_and_symlink_files(tmp_path, speaker_models):
    path = ready(tmp_path, speaker_models)
    assert d.downloaded(path)
    (path / 'embedding.onnx').write_bytes(b'corrupt model')
    assert not d.downloaded(path)
    with pytest.raises(d.DiarizationUnavailable):
        d.diarize_local(tmp_path / 'unused.wav', path)
    speaker_models(path)
    (path / 'segmentation.onnx').unlink()
    (path / 'segmentation.onnx').symlink_to(path / 'embedding.onnx')
    assert not d.downloaded(path)


def test_download_rejects_changed_content(monkeypatch, tmp_path):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def raise_for_status(self): pass
        def iter_bytes(self,*args): yield b'changed upstream model'
    monkeypatch.setattr(d.httpx, 'stream', lambda *args, **kwargs: Response())
    with pytest.raises(d.DiarizationUnavailable, match='integrity'):
        d._download(d.EMBEDDING_URL, tmp_path/'download', '0'*64, 1000)
    with pytest.raises(d.DiarizationUnavailable, match='size'):
        d._download(d.EMBEDDING_URL, tmp_path/'too-large', '0'*64, 1)


def test_archive_only_extracts_exact_regular_members(monkeypatch, tmp_path):
    def fake_download(url, target, *args):
        with tarfile.open(target, 'w:bz2') as archive:
            info = tarfile.TarInfo('sherpa-onnx-pyannote-segmentation-3-0/model.onnx')
            info.type = tarfile.SYMTYPE
            info.linkname = '../../escaped'
            archive.addfile(info)
    monkeypatch.setattr(d, '_download', fake_download)
    with pytest.raises(d.DiarizationUnavailable, match='archive'):
        d.prepare_models(tmp_path)
    assert not (tmp_path.parent/'escaped').exists()


async def test_queue_download_then_combined_job_persist_retry_and_names(tmp_path, speaker_models):
    prepared_model(tmp_path)
    store = Store(tmp_path)
    queue = TranscriptionQueue(tmp_path, store, transcriber=lambda *_: deepcopy(WORDS),
                               diarizer=lambda *_: deepcopy(TURNS), speaker_installer=speaker_models)
    with pytest.raises(d.DiarizationUnavailable):
        queue.enqueue('one', diarize=True)
    queue.start()
    try:
        download = queue.prepare_speaker_models()
        assert queue.prepare_speaker_models()['id'] == download['id']
        await until(lambda: status_of(queue, download) == 'completed')
        assert queue.status()['speaker_labels']
        job = queue.enqueue('one', diarize=True, num_speakers=2)
        await until(lambda: status_of(queue, job) == 'completed')
        transcript = store.records['one']['transcript']
        assert transcript['diarization']['speaker_count'] == 2 and transcript['speaker_revision']
        assert WORDS['text'] not in json.dumps(queue.list_jobs())
        cancelled = queue.enqueue('two', diarize=True, num_speakers=2)
        queue.cancel(cancelled['id'])
    finally:
        await queue.close()
    restored = TranscriptionQueue(tmp_path, store, transcriber=lambda *_: deepcopy(WORDS), diarizer=lambda *_: deepcopy(TURNS))
    assert next(j for j in restored.list_jobs() if j['id']==job['id'])['num_speakers']==2
    retried = restored.retry(cancelled['id'])
    assert retried['diarize'] and retried['num_speakers']==2
    restored.start()
    await until(lambda: status_of(restored, retried)=='completed')
    await restored.close()


async def test_cancel_during_diarization_keeps_previous_transcript_and_audio(tmp_path, speaker_models):
    prepared_model(tmp_path); ready(tmp_path, speaker_models)
    store=Store(tmp_path);store.records['one']['transcript']={'text':'Previous transcript','speakers':{'speaker_1':'Saved name'}}
    old=deepcopy(store.records['one']['transcript']); audio=(tmp_path/'one.wav').read_bytes()
    started, release = threading.Event(), threading.Event()
    def diarize(*args):
        started.set(); assert release.wait(3); return TURNS
    queue=TranscriptionQueue(tmp_path,store,transcriber=lambda *_:deepcopy(WORDS),diarizer=diarize)
    queue.start()
    try:
        job=queue.enqueue('one',diarize=True)
        await until(started.is_set)
        queue.cancel(job['id']);release.set()
        await until(lambda:not queue.status()['busy'])
        assert store.records['one']['transcript']==old
        assert store.records['one']['status']=='transcribed'
        assert (tmp_path/'one.wav').read_bytes()==audio
    finally:
        release.set();await queue.close()


async def test_diarization_failure_preserves_transcript_and_redacts_error(tmp_path, speaker_models):
    prepared_model(tmp_path);ready(tmp_path,speaker_models)
    store=Store(tmp_path);store.records['one']['transcript']={'text':'Keep this'}
    def fail(*args):raise RuntimeError('private speech or credential must not appear')
    queue=TranscriptionQueue(tmp_path,store,transcriber=lambda *_:deepcopy(WORDS),diarizer=fail)
    queue.start()
    try:
        job=queue.enqueue('one',diarize=True)
        await until(lambda:status_of(queue,job)=='failed')
        assert store.records['one']['transcript']=={'text':'Keep this'}
        assert 'private speech' not in json.dumps(queue.list_jobs())
    finally:await queue.close()


def test_native_adapter_uses_only_local_cpu_models_and_count(monkeypatch,tmp_path):
    seen={}
    def config(**kw):seen['config']=kw;return SimpleNamespace(validate=lambda:True)
    class Engine:
        sample_rate=16000
        def __init__(self, cfg): pass
        def process(self,audio,callback):
            callback(1,2)
            return SimpleNamespace(sort_by_start_time=lambda:[SimpleNamespace(start=0,end=1,speaker=0)])
    fake=SimpleNamespace(OfflineSpeakerDiarizationConfig=config, OfflineSpeakerDiarization=Engine,
        OfflineSpeakerSegmentationModelConfig=lambda **kw:kw, OfflineSpeakerSegmentationPyannoteModelConfig=lambda **kw:kw,
        SpeakerEmbeddingExtractorConfig=lambda **kw:kw, FastClusteringConfig=lambda **kw:kw)
    monkeypatch.setitem(sys.modules,'sherpa_onnx',fake)
    monkeypatch.setitem(sys.modules,'faster_whisper.audio',SimpleNamespace(decode_audio=lambda *args,**kw:[0]*16000))
    monkeypatch.setattr(d,'complete_files',lambda *args,**kw:True)
    progress=[]
    assert d.diarize_local(tmp_path/'audio.wav',tmp_path,2,progress=lambda **kw:progress.append(kw))==[{'start':0.,'end':1.,'speaker':0}]
    assert seen['config']['clustering']['num_clusters']==2
    assert seen['config']['segmentation']['provider']=='cpu'
    assert seen['config']['embedding']['model']==str(tmp_path/'embedding.onnx')
    assert progress[-1]['processed_seconds']==.5


def test_speaker_routes_exports_and_stale_rename_preserve_library(tmp_path,speaker_models):
    workspace=make_workspace(tmp_path,transcriber=lambda *_:deepcopy(WORDS))
    workspace.queue._speaker_injected=True;workspace.queue._diarizer=lambda *_:deepcopy(TURNS)
    ready(tmp_path,speaker_models);prepared_model(tmp_path)
    token=workspace.settings.token
    with TestClient(workspace.app) as client:
        headers={'Authorization':'Bearer '+token}
        record=client.post('/v1/recordings/import',headers=headers,files={'file':('test.wav',wav_bytes(),'audio/wav')}).json()
        rid=record['id']; path='/v1/recordings/'+rid
        for route,method,body in [('/v1/transcription/diarization/prepare','post',{}),(path+'/speakers','patch',{'revision':'a'*32,'names':{'speaker_1':'Name'}})]:
            assert getattr(client,method)(route,json=body).status_code==401
        assert client.patch('/v1/settings',headers=headers,json={'diarize':True}).status_code==200
        assert client.post(path+'/transcribe',headers=headers,json={'num_speakers':True}).status_code==422
        response=client.post(path+'/transcribe',headers=headers,json={'num_speakers':2})
        assert response.status_code==202 and response.json()['diarize']
        import time
        for _ in range(100):
            record=client.get(path,headers=headers).json()
            if record['status']=='transcribed':break
            time.sleep(.01)
        assert record['transcript']['diarization']['speaker_count']==2
        revision=record['transcript']['speaker_revision']
        bad=client.patch(path+'/speakers',headers=headers,json={'revision':revision,'names':{'unknown':'X'}})
        assert bad.status_code==409
        assert client.patch(path+'/speakers',headers=headers,json={'revision':revision,'names':{'speaker_1':'\n'}}).status_code==422
        changed=client.patch(path+'/speakers',headers=headers,json={'revision':revision,'names':{'speaker_1':'Alex','speaker_2':'Sam'}})
        assert changed.status_code==200
        assert changed.json()['transcript']['text']==WORDS['text']
        assert client.patch(path+'/speakers',headers=headers,json={'revision':revision,'names':{'speaker_1':'Stale'}}).status_code==409
        for fmt in ('txt','md','srt','json'):
            response=client.get(path+'/export?format='+fmt,headers=headers)
            assert response.status_code==200 and 'Alex' in response.text and 'Sam' in response.text
        assert client.patch('/v1/settings',headers=headers,json={'diarize':None}).status_code==422
        # Batch honours the same preference. Legacy transcripts remain unchanged.
        another=client.post('/v1/recordings/import',headers=headers,files={'file':('next.wav',wav_bytes(),'audio/wav')}).json()
        batch=client.post('/v1/transcription/batch',headers=headers,json={'recording_ids':[rid,another['id']]}).json()
        assert batch['queued']==1 and batch['jobs'][0]['diarize'] and len(batch['skipped'])==1


def test_whisper_requests_and_normalises_word_timestamps(monkeypatch,tmp_path):
    path=prepared_model(tmp_path)
    seen={}
    class Model:
        def __init__(self,*args,**kwargs):seen['init']=kwargs
        def transcribe(self,*args,**kwargs):
            seen['request']=kwargs
            segment=SimpleNamespace(start=0,end=1,text=' Hello',words=[SimpleNamespace(start=0,end=1,word=' Hello')])
            return iter([segment]),SimpleNamespace(language='en',duration=1)
    monkeypatch.setitem(sys.modules,'faster_whisper',SimpleNamespace(WhisperModel=Model))
    result=_normalise_result(_transcribe_local(tmp_path/'unused.wav',path,'en',word_timestamps=True))
    assert seen['init']['local_files_only'] and seen['request']['word_timestamps']
    assert result['segments'][0]['words']==[{'start':0.,'end':1.,'word':' Hello'}]
    invalid=deepcopy(result);invalid['segments'][0]['words'][0]['end']=float('inf')
    with pytest.raises(ValueError):_normalise_result(invalid)


async def test_interrupted_speaker_download_never_restarts_implicitly(tmp_path,speaker_models):
    store=Store(tmp_path)
    queue=TranscriptionQueue(tmp_path,store,transcriber=lambda *_:deepcopy(WORDS),speaker_installer=speaker_models)
    job=queue.prepare_speaker_models()
    reopened=TranscriptionQueue(tmp_path,store,transcriber=lambda *_:deepcopy(WORDS),speaker_installer=speaker_models)
    assert reopened.list_jobs()[0]['status']=='interrupted'
    reopened.start()
    await asyncio.sleep(.01)
    assert not (tmp_path/'models'/d.MODEL_ID).exists()
    reopened.retry(job['id'])
    await until(lambda:status_of(reopened,job)=='completed')
    await reopened.close()


def test_automatic_import_uses_speaker_preference_and_active_job_blocks_rename(tmp_path,speaker_models):
    started,release=threading.Event(),threading.Event()
    def transcriber(*args):started.set();assert release.wait(3);return deepcopy(WORDS)
    workspace=make_workspace(tmp_path,transcriber=transcriber)
    workspace.queue._speaker_injected=True;workspace.queue._diarizer=lambda *_:deepcopy(TURNS)
    ready(tmp_path,speaker_models);prepared_model(tmp_path)
    try:
        with TestClient(workspace.app) as client:
            client.headers['Authorization']='Bearer '+workspace.settings.token
            assert client.patch('/v1/settings',json={'diarize':True,'auto_transcribe':True}).status_code==200
            record=client.post('/v1/recordings/import',files={'file':('auto.wav',wav_bytes(),'audio/wav')}).json()
            assert started.wait(2)
            job=workspace.queue.list_jobs()[0]
            assert job['recording_id']==record['id'] and job['diarize'] and job['num_speakers'] is None
            assert client.patch('/v1/recordings/'+record['id']+'/speakers',json={'revision':'a'*32,'names':{'speaker_1':'Alex'}}).status_code==409
            release.set()
    finally:release.set()


def test_small_timestamp_drift_does_not_fragment_a_speaker_turn():
    transcript={'text':'A sentence.', 'language':'en','duration':3,'segments':[{'start':1.2,'end':2.5,'text':'A sentence.','words':[
        {'start':1.2,'end':1.4,'word':' A'}, {'start':1.4,'end':2.5,'word':' sentence.'}]}]}
    result=d.label_transcript(transcript,[{'start':1.45,'end':2.5,'speaker':0}])
    assert result['segments']==[{'start':1.2,'end':2.5,'text':'A sentence.','speaker':'speaker_1'}]
