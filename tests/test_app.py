import asyncio
import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend import main
from backend.store import Store


def test_store(tmp_path):
    db=Store(tmp_path/'test.db')
    sid=db.create()
    assert db.exists(sid)
    db.append(sid,'user','你好世界')
    db.append(sid,'assistant','你好！')
    assert db.list_messages(sid)[-1]['content']=='你好！'
    assert db.list_sessions()[0]['title']=='你好世界'
    db.delete(sid)
    assert not db.exists(sid)


def test_sse_delta_parser():
    s='data: '+json.dumps({'choices':[{'delta':{'content':'你好'}},{'delta':{'reasoning_content':'skip'}}]})
    assert main.consume_deepseek_line(s)=='你好'
    assert main.consume_deepseek_line('data: [DONE]')==''
    assert main.consume_deepseek_line('garbage')==''


def test_chat_and_status(monkeypatch,tmp_path):
    monkeypatch.setattr(main,'STORE', Store(tmp_path/'db.sqlite'))
    monkeypatch.setenv('DEEPSEEK_API_KEY','sk-testnotreal')
    async def fake_llm(messages,model,key):
        assert model=='deepseek-flash'
        assert messages[-1]['content']=='早上好'
        for x in ['早上','好呀！']:yield x
    monkeypatch.setattr(main,'stream_deepseek',fake_llm)
    with TestClient(main.app) as client:
        assert client.get('/api/app/status').json()['api_configured'] is True
        sid=client.post('/api/app/sessions').json()['id']
        response=client.post('/api/app/chat/stream',json={'session_id':sid,'message':'早上好','model':'deepseek-flash'})
        assert response.status_code==200
        events=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert [x['event'] for x in events]==['start','delta','delta','done']
        assert events[-1]['text']=='早上好呀！'
        assert len(client.get('/api/app/sessions/'+sid).json()['messages'])==2
        assert client.get('/').status_code==200
        assert client.get('/static/app.js').status_code==200
        assert client.post('/api/app/cancel',json={'session_id':sid}).json()['ok']


def test_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.setattr(main,'STORE',Store(tmp_path/'db.sqlite'))
    monkeypatch.setenv('DEEPSEEK_API_KEY','sk-请替换为你自己的密钥')
    with TestClient(main.app) as client:
        sid=client.post('/api/app/sessions').json()['id']
        assert client.post('/api/app/chat/stream',json={'session_id':sid,'message':'测试'}).status_code==503


def test_memory_is_persistent_and_added_to_system_prompt(tmp_path, monkeypatch):
    db = Store(tmp_path / 'memory.sqlite')
    monkeypatch.setattr(main, 'STORE', db)
    with TestClient(main.app) as client:
        assert client.get('/api/app/memories').json()['memories'] == []
        stored = client.post('/api/app/memories', json={'content': '喜欢简短的中文回复'})
        assert stored.status_code == 200
        note = client.get('/api/app/memories').json()['memories'][0]
        assert note['content'] == '喜欢简短的中文回复'
        assert '喜欢简短的中文回复' in main.system_prompt(None)
        assert client.delete('/api/app/memories/' + str(note['id'])).status_code == 200
        assert client.get('/api/app/memories').json()['memories'] == []


def test_double_chat_is_rejected_until_first_finishes(tmp_path, monkeypatch):
    db = Store(tmp_path / 'double.sqlite')
    monkeypatch.setattr(main, 'STORE', db)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'sk-notarealkey')
    sid = db.create()
    prior = main.Turn('in-progress')
    main.active_turns[sid] = prior
    try:
        with TestClient(main.app) as client:
            assert client.post('/api/app/chat/stream', json={
                'session_id': sid, 'message': '你好'
            }).status_code == 409
            assert client.post('/api/app/cancel', json={'session_id': sid}).json()['ok']
            assert prior.cancelled
    finally:
        main.active_turns.pop(sid, None)


def test_no_reasoning_content_leaks_to_tts():
    line = 'data: ' + json.dumps({
        'choices':[{'delta': {'reasoning_content': 'internal', 'content': '可以听见的回复'}}]
    }, ensure_ascii=False)
    assert main.parse_sse_line(line) == '可以听见的回复'


def test_invalid_memory_and_models(tmp_path, monkeypatch):
    db = Store(tmp_path / 'invalid.sqlite')
    monkeypatch.setattr(main, 'STORE', db)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'sk-testnotreal')
    sid = db.create()
    with TestClient(main.app) as client:
        assert client.post('/api/app/memories', json={'content': ''}).status_code == 422
        assert client.post('/api/app/chat/stream', json={
            'session_id': sid, 'message': '你好', 'model':'non-existent-model'
        }).status_code == 422
        assert client.get('/api/app/status').json()['version'] == '1.1.0'
