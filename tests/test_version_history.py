"""History contracts: snapshots, restore safety, existing database migration, retention."""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from main import app
from storage import Storage, initialize


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv('TURSO_DATABASE_URL', raising=False)
    monkeypatch.delenv('TURSO_AUTH_TOKEN', raising=False)
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'test.sqlite3'))
    with TestClient(app) as test:
        yield test


def new_doc(client):
    resp=client.post('/api/documents',json={'title':'Draft one'})
    assert resp.status_code == 201, resp.text
    return resp.json()['document']


def test_history_saves_rich_text_snapshots_and_restores_without_losing_current_state(client):
    doc=new_doc(client)
    url=f"/api/documents/{doc['id']}"
    versions=client.get(url+'/versions').json()['versions']
    assert [v['revision'] for v in versions]==[1]
    first=client.get(url+'/versions/1').json()['version']
    assert first['title']=='Draft one'
    assert first['delta']=={'ops':[{'insert':'\n'}]}

    formatted={'ops':[{'insert':'Hello ', 'attributes':{'italic':True}}, {'insert':'World','attributes':{'bold':True}}, {'insert':'\n'}]}
    r=client.patch(url,json={'revision':1,'title':'Draft two','delta':formatted})
    assert r.status_code==200, r.text
    assert r.json()['document']['revision']==2
    versions=client.get(url+'/versions').json()['versions']
    assert [v['revision'] for v in versions]==[2,1]
    assert client.get(url+'/versions/2').json()['version']['delta']==formatted
    assert client.get(url+'/versions/2').json()['version']['title']=='Draft two'

    restore=client.post(url+'/versions/1/restore',json={'current_revision':2})
    assert restore.status_code==200, restore.text
    restored=restore.json()['document']
    assert restored['revision']==3
    assert restored['title']=='Draft one'
    assert restored['delta']==first['delta']
    assert client.get(url+'/versions/2').json()['version']['delta']==formatted
    assert [v['revision'] for v in client.get(url+'/versions').json()['versions']]==[3,2,1]
    assert client.get(url).json()['document']==restored


def test_history_requires_document_access_and_owner_only_restore(client):
    doc=new_doc(client)
    url=f"/api/documents/{doc['id']}"
    assert client.post('/api/session',json={'user_id':'noah'}).status_code==200
    assert client.get(url+'/versions').status_code==404
    assert client.get(url+'/versions/1').status_code==404
    assert client.post(url+'/versions/1/restore',json={'current_revision':1}).status_code==404

    client.post('/api/session',json={'user_id':'maya'})
    client.post(url+'/shares',json={'email':'noah@demo.scribe','role':'viewer'})
    client.post('/api/session',json={'user_id':'noah'})
    assert client.get(url+'/versions').status_code==200
    assert client.get(url+'/versions/1').status_code==200
    assert client.post(url+'/versions/1/restore',json={'current_revision':1}).status_code==403
    client.post('/api/session',json={'user_id':'maya'})
    client.post(url+'/shares',json={'email':'noah@demo.scribe','role':'editor'})
    client.post('/api/session',json={'user_id':'noah'})
    assert client.patch(url,json={'revision':1,'title':'Collaborator changed'}).status_code==200
    assert client.post(url+'/versions/1/restore',json={'current_revision':2}).status_code==403


def test_history_restore_rejects_stale_revision_and_missing_version(client):
    doc=new_doc(client)
    url=f"/api/documents/{doc['id']}"
    client.patch(url,json={'revision':1,'title':'Changed'})
    assert client.post(url+'/versions/1/restore',json={'current_revision':1}).status_code==409
    assert client.post(url+'/versions/500/restore',json={'current_revision':2}).status_code==404
    assert client.get(url+'/versions/500').status_code==404
    assert client.get(url).json()['document']['title']=='Changed'


def test_history_caps_at_30_and_delete_removes_versions(client):
    doc=new_doc(client)
    url=f"/api/documents/{doc['id']}"
    for rev in range(1,36):
        resp=client.patch(url,json={'revision':rev,'title':f'Draft {rev}'})
        assert resp.status_code==200, resp.text
    versions=client.get(url+'/versions').json()['versions']
    assert len(versions)==30
    assert versions[0]['revision']==36
    assert versions[-1]['revision']==7
    assert client.get(url+'/versions/1').status_code==404
    assert client.delete(url).status_code==204
    assert client.app.state.db.one('SELECT revision FROM document_versions WHERE doc_id=?',doc['id']) is None


def test_upgrading_existing_sqlite_preserves_documents_and_backfills_current_snapshot(tmp_path):
    path=tmp_path/'existing.sqlite3'
    with sqlite3.connect(path) as con:
        con.execute('CREATE TABLE users (id TEXT PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL)')
        con.execute('CREATE TABLE documents (id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,delta_json TEXT NOT NULL,revision INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)')
        con.execute('CREATE TABLE shares (doc_id TEXT NOT NULL,user_id TEXT NOT NULL,role TEXT NOT NULL,PRIMARY KEY(doc_id,user_id))')
        con.execute('INSERT INTO users VALUES (?,?,?)',('maya','Maya Chen','maya@demo.scribe'))
        con.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?)',('old-id','maya','Keep me',json.dumps({'ops':[{'insert':'previous text\n'}]}),5,'2026-01-01','2026-01-03'))
    storage=Storage(local_path=str(path))
    initialize(storage)
    assert storage.one('SELECT title,revision FROM documents WHERE id=?','old-id')=={'title':'Keep me','revision':5}
    old=storage.one('SELECT revision,title,saved_at FROM document_versions WHERE doc_id=?','old-id')
    assert old=={'revision':5,'title':'Keep me','saved_at':'2026-01-03'}
    initialize(storage)  # migration is safe on repeated deployments
    assert len(storage.all('SELECT * FROM document_versions WHERE doc_id=?','old-id'))==1
    storage.change('UPDATE documents SET title=?,revision=revision+1 WHERE id=?','After upgrade','old-id')
    assert [x['revision'] for x in storage.all('SELECT revision FROM document_versions WHERE doc_id=? ORDER BY revision','old-id')]==[5,6]
