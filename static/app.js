'use strict';

const state = {
  session: null, documents: [], currentDoc: null, editor: null,
  filter: 'all', search: '', editVersion: 0, lastSavedVersion: 0,
  saveTimer: null, savePromise: null, saveError: false, toastTimer: null,
};

const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initials = (name) => name.split(' ').map(s => s[0]).slice(0,2).join('').toUpperCase();
const niceDate = (iso) => new Intl.DateTimeFormat('en-US', {month:'short',day:'numeric',year:'numeric'}).format(new Date(iso));

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, { credentials: 'same-origin', ...options,
      headers: options.body instanceof FormData ? {...(options.headers || {})} : {'Content-Type':'application/json', ...(options.headers || {})},
    });
  } catch {
    throw new Error('Network connection failed. Check your connection and try again.');
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const error = await response.json(); message = error.detail || message; } catch { /* non-JSON response */ }
    const err = new Error(Array.isArray(message) ? 'Please check your input.' : message);
    err.status = response.status;
    throw err;
  }
  return response.status === 204 ? null : response.json();
}

function toast(message, isError = false) {
  const element = $('#toast');
  element.textContent = message;
  element.classList.toggle('is-error', isError);
  element.classList.add('visible');
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => element.classList.remove('visible'), 3400);
}

function setBreadcrumb(label, secondary) {
  $('#breadcrumb').innerHTML = secondary
    ? `<button id="back-crumb" class="breadcrumb-back">Workspace</button><span class="breadcrumb-slash">/</span><strong>${escapeHTML(label)}</strong>`
    : `<span>Workspace</span><span class="breadcrumb-slash">/</span><strong>${escapeHTML(label)}</strong>`;
  $('#back-crumb')?.addEventListener('click', async () => {
    try {await flushSave(); await refreshDocs(); showDashboard('all');}
    catch (error) {toast(error.message, true);}
  });
}

function updateSidebar() {
  $('#count-all').textContent = state.documents.length;
  $('#count-owned').textContent = state.documents.filter(d => d.role === 'owner').length;
  $('#count-shared').textContent = state.documents.filter(d => d.role !== 'owner').length;
  $$('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.nav === state.filter && !state.currentDoc));
}

async function refreshDocs() {
  const {documents} = await api('/api/documents');
  state.documents = documents;
  updateSidebar();
}

function filteredDocs() {
  return state.documents.filter(doc =>
    (state.filter === 'all' || (state.filter === 'owned' ? doc.role === 'owner' : doc.role !== 'owner')) &&
    (doc.title.toLowerCase().includes(state.search.toLowerCase()) || doc.owner_name.toLowerCase().includes(state.search.toLowerCase()))
  );
}

function docsHTML() {
  const docs = filteredDocs();
  if (!docs.length) {
    return `<div class="empty-state"><div class="empty-symbol">▤</div><h3>${state.search ? 'No matching documents' : 'Nothing here yet'}</h3><p>${state.search ? 'Try a different search term.' : 'Create something new, or ask a teammate to share a document.'}</p><button class="btn btn-outline" id="empty-new">Create document</button></div>`;
  }
  return `<div class="doc-list">${docs.map(d => `
    <button class="doc-row" data-open="${d.id}">
      <span class="document-thumbnail"><span class="doc-thumbnail-lines">☷<br>▭</span></span>
      <span class="document-details"><strong>${escapeHTML(d.title)}</strong><span>${d.role === 'owner' ? 'You own this document' : `Shared by ${escapeHTML(d.owner_name)}`}</span></span>
      <span class="table-role ${d.role === 'owner' ? 'owned' : 'shared'}">${d.role === 'owner' ? 'Owner' : (d.role === 'editor' ? 'Can edit' : 'Can view')}</span>
      <span class="doc-date">${niceDate(d.updated_at)}</span>
      <span class="doc-row-arrow" aria-hidden="true">↗</span>
    </button>`).join('')}</div>`;
}

function renderDocList() {
  $('#list-container').innerHTML = docsHTML();
  $$('[data-open]').forEach(btn => btn.addEventListener('click', () => openDoc(btn.dataset.open)));
  $('#empty-new')?.addEventListener('click', createDoc);
}

function showDashboard(filter = 'all', push = true) {
  state.currentDoc = null;
  state.editor = null;
  state.filter = filter;
  if (push) history.pushState({}, '', '/');
  const title = {all:'All documents', owned:'Owned by me', shared:'Shared with me'}[filter];
  setBreadcrumb(title);
  updateSidebar();
  const own = state.documents.filter(d => d.role === 'owner').length;
  const shared = state.documents.length - own;
  $('#main').className = 'main-area dashboard-main';
  $('#main').innerHTML = `
    <div class="dashboard-inner">
      <div class="eyebrow"><span class="eyebrow-line"></span> YOUR WORKSPACE</div>
      <div class="dashboard-heading"><div><h1>Good to see you, ${escapeHTML(state.session.current.name.split(' ')[0])}<span class="heading-sparkle"> ✳</span></h1><p>All your ideas, notes, and shared work in one place.</p></div><button class="btn btn-primary create-top" id="create-top">＋ &nbsp; New document</button></div>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-upper"><span>Total documents</span><span class="stat-icon lilac">▤</span></div><strong>${state.documents.length}</strong><small>Your writing space</small></div>
        <div class="stat-card"><div class="stat-upper"><span>Created by you</span><span class="stat-icon mint">▣</span></div><strong>${own}</strong><small>Documents you own</small></div>
        <div class="stat-card"><div class="stat-upper"><span>Shared with you</span><span class="stat-icon peach">♧</span></div><strong>${shared}</strong><small>From your teammates</small></div>
      </div>
      <div class="document-section"><div class="section-title"><div><h2>${escapeHTML(title)}</h2><p>${filter === 'all' ? 'Pick up right where you left off.' : filter === 'owned' ? 'Documents you created and manage.' : 'Documents your teammates invited you to.'}</p></div><div class="search-box"><span aria-hidden="true">⌕</span><input id="search-input" type="search" placeholder="Search documents" value="${escapeHTML(state.search)}" aria-label="Search documents" /></div></div>
      <div class="list-head"><span>DOCUMENT</span><span>ACCESS</span><span>LAST MODIFIED</span><span></span></div>
      <div id="list-container"></div></div>
      <div class="dashboard-caption">✦ &nbsp; Built for thoughtful work, not distractions.</div>
    </div>`;
  $('#create-top').addEventListener('click', createDoc);
  $('#search-input').addEventListener('input', e => {state.search = e.target.value; renderDocList();});
  renderDocList();
}

function saveStatus(text, kind = '') {
  const el = $('#save-status');
  if (!el) return;
  el.textContent = text;
  el.className = 'save-status ' + kind;
}

function markDirty() {
  if (!state.currentDoc || state.currentDoc.role === 'viewer') return;
  state.editVersion++;
  state.saveError = false;
  saveStatus('● Unsaved changes', 'dirty');
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(() => {flushSave().catch(() => {});}, 700);
}

async function flushSave() {
  clearTimeout(state.saveTimer);
  const documentToSave = state.currentDoc;
  if (!documentToSave || documentToSave.role === 'viewer' || !state.editor) return;
  if (state.savePromise) return state.savePromise;
  if (state.lastSavedVersion === state.editVersion) return;
  state.savePromise = (async () => {
    while (state.lastSavedVersion !== state.editVersion && state.currentDoc === documentToSave) {
      const version = state.editVersion;
      const payload = {revision: documentToSave.revision, title: $('#doc-title').value, delta: state.editor.getContents()};
      saveStatus('◌ Saving…', 'saving');
      try {
        const result = await api(`/api/documents/${documentToSave.id}`, {method:'PATCH', body:JSON.stringify(payload)});
        documentToSave.revision = result.document.revision;
        documentToSave.title = result.document.title;
        documentToSave.updated_at = result.document.updated_at;
        state.lastSavedVersion = version;
        state.saveError = false;
      } catch (error) {
        state.saveError = true;
        saveStatus(error.status === 409 ? '⚠ Conflict — reopen to reload' : '⚠ Save failed — retry', 'error');
        toast(error.message, true);
        throw error;
      }
    }
    saveStatus('✓ All changes saved', 'saved');
  })();
  try {await state.savePromise;} finally {state.savePromise = null;}
}

async function openDoc(id, push = true) {
  if (state.currentDoc?.id === id) return;
  try {
    if (state.currentDoc) await flushSave();
    const {document: doc} = await api(`/api/documents/${encodeURIComponent(id)}`);
    state.currentDoc = doc;
    state.editVersion = 0;
    state.lastSavedVersion = 0;
    state.saveError = false;
    if (push) history.pushState({}, '', `/docs/${doc.id}`);
    renderEditor(doc);
  } catch (error) {toast(error.message, true);}
}

function renderEditor(doc) {
  const canEdit = doc.role !== 'viewer';
  setBreadcrumb(doc.title, true);
  updateSidebar();
  $('#main').className = 'main-area editor-main';
  $('#main').innerHTML = `
    <div class="editor-top">
      <div class="editor-heading"><button class="back-button" id="back-to-list" title="Back to documents" aria-label="Back to documents">←</button><span class="editor-doc-icon">▤</span>
      <div class="editor-title-wrap"><input id="doc-title" aria-label="Document title" maxlength="120" value="${escapeHTML(doc.title)}" ${canEdit?'':'readonly'} /><span class="editor-subtitle">${doc.role === 'owner' ? 'You are the owner' : `Owned by ${escapeHTML(doc.owner_name)}`} <span class="middle-dot">·</span> ${doc.role === 'viewer' ? 'View only' : 'You can edit'}</span></div></div>
      <div class="editor-actions"><span class="save-status saved" id="save-status">${canEdit ? '✓ All changes saved' : '◉ View only'}</span>${doc.role === 'owner' ? '<button class="btn btn-share" id="share-btn">♧ &nbsp; Share</button>' : ''}<button class="btn btn-outline more-button" id="more-button" title="Document options" aria-label="Document options">⋯</button></div>
    </div>
    <div class="editor-toolbar-shell ${canEdit ? '' : 'toolbar-disabled'}">
      <div id="toolbar" role="toolbar" aria-label="Text formatting">
        <span class="ql-formats"><select class="ql-header" aria-label="Paragraph style"><option selected></option><option value="1">Heading 1</option><option value="2">Heading 2</option><option value="3">Heading 3</option></select></span>
        <span class="ql-formats"><button class="ql-bold" aria-label="Bold"></button><button class="ql-italic" aria-label="Italic"></button><button class="ql-underline" aria-label="Underline"></button><button class="ql-strike" aria-label="Strikethrough"></button></span>
        <span class="ql-formats"><button class="ql-list" value="ordered" aria-label="Numbered list"></button><button class="ql-list" value="bullet" aria-label="Bulleted list"></button><button class="ql-blockquote" aria-label="Quote"></button></span>
        <span class="ql-formats"><button class="ql-clean" aria-label="Clear formatting"></button></span>
      </div>
      <div class="toolbar-side">${canEdit ? 'EDITING' : 'READ ONLY'} <span class="toolbar-status-dot"></span></div>
    </div>
    <div class="editor-scroll"><div class="paper"><div id="editor" aria-label="Document editor"></div></div><div class="page-footer"><span>SCRIBE DOCUMENT</span><span>${canEdit ? 'Changes auto-save while you write' : 'Shared with view-only access'}</span></div></div>`;
  $('#back-to-list').addEventListener('click', async () => {try {await flushSave(); await refreshDocs(); showDashboard(state.filter);} catch { /* stay on unsaved draft */ }});
  $('#more-button').addEventListener('click', () => showDocMenu(doc));
  $('#share-btn')?.addEventListener('click', () => openShareModal(doc));
  $('#doc-title').addEventListener('input', () => {markDirty(); setBreadcrumb($('#doc-title').value || 'Untitled', true);});
  $('#doc-title').addEventListener('blur', async e => {
    if (!e.target.value.trim() && canEdit) {e.target.value = 'Untitled document'; markDirty();}
  });
  if (!window.Quill) {
    $('#editor').textContent = 'The text editor could not load. Please check your internet connection and reload.';
    toast('Could not load Quill from CDN. Please check your internet connection.', true);
    return;
  }
  const editor = new Quill('#editor', {theme:'snow', modules:{toolbar: canEdit ? '#toolbar' : false, history:{delay:400,maxStack:100}},
    placeholder: canEdit ? 'Start writing your next big idea…' : '',
    formats:['header','bold','italic','underline','strike','list','blockquote']});
  editor.setContents(doc.delta, 'silent');
  editor.enable(canEdit);
  editor.on('text-change', (delta, old, source) => {if (source === 'user') markDirty();});
  state.editor = editor;
}

async function createDoc() {
  try {
    if (state.currentDoc) await flushSave();
    const {document: doc} = await api('/api/documents', {method:'POST', body:JSON.stringify({title:'Untitled document'})});
    await refreshDocs();
    showDashboard('all', false);
    await openDoc(doc.id);
    $('#doc-title')?.focus();
    $('#doc-title')?.select();
    toast('Document created');
  } catch (error) {toast(error.message, true);}
}

async function importFile(file) {
  if (!file) return;
  const suffix = file.name.toLowerCase().split('.').pop();
  if (!['txt','md'].includes(suffix)) return toast('Only .txt and .md files are supported', true);
  if (file.size > 512*1024) return toast('File is larger than 512 KB', true);
  const data = new FormData();
  data.append('file', file);
  try {
    if (state.currentDoc) await flushSave();
    const {document: doc} = await api('/api/import', {method:'POST',body:data});
    await refreshDocs();
    showDashboard('all', false);
    await openDoc(doc.id);
    toast(`Imported ${file.name}`);
  } catch (error) {toast(error.message, true);}
  finally {$('#file-input').value='';}
}

function closeModal() {$('#modal-root').innerHTML = '';}

async function showDocMenu(doc) {
  const canDelete = doc.role === 'owner';
  $('#modal-root').innerHTML = `<div class="modal-backdrop"><div class="modal modal-small" role="dialog" aria-modal="true" aria-labelledby="options-heading">
  <div class="modal-title-row"><div><h2 id="options-heading">Document options</h2><p>More ways to work with this document.</p></div><button class="icon-button" id="close-modal" aria-label="Close">✕</button></div>
  <div class="option-buttons"><button id="copy-doc-link" class="option-button">↗ <span>Copy document link</span></button>${canDelete ? '<button id="delete-doc" class="option-button danger-text">⌫ <span>Delete document</span></button>' : ''}</div>
  </div></div>`;
  modalEvents();
  $('#copy-doc-link').addEventListener('click', async () => {await copyLink(doc.id);closeModal();});
  $('#delete-doc')?.addEventListener('click', async () => {
    if (!window.confirm(`Delete “${doc.title}”? This cannot be undone.`)) return;
    try {await api(`/api/documents/${doc.id}`, {method:'DELETE'});closeModal();await refreshDocs();showDashboard('all');toast('Document deleted');}
    catch(error){toast(error.message,true);}
  });
}

function modalEvents() {
  $('#close-modal')?.addEventListener('click',closeModal);
  $('.modal-backdrop')?.addEventListener('mousedown',e => {if(e.target.classList.contains('modal-backdrop')) closeModal();});
}

async function copyLink(id) {
  try {await navigator.clipboard.writeText(`${location.origin}/docs/${id}`);toast('Document link copied');}
  catch {toast('Copy the document URL from your address bar');}
}

async function openShareModal(doc) {
  try {
    const {shares} = await api(`/api/documents/${doc.id}/shares`);
    const otherUsers = state.session.users.filter(u => u.id !== doc.owner_id);
    $('#modal-root').innerHTML = `<div class="modal-backdrop"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="share-heading">
      <div class="modal-title-row"><div><span class="modal-eyebrow">COLLABORATION</span><h2 id="share-heading">Share “${escapeHTML(doc.title)}”</h2><p>Give teammates access to this document.</p></div><button class="icon-button" id="close-modal" aria-label="Close">✕</button></div>
      <form id="share-form"><label class="field-label" for="share-email">Invite a teammate</label><div class="share-form-row"><select id="share-email" required aria-label="Choose a teammate">${otherUsers.map(u=>`<option value="${escapeHTML(u.email)}">${escapeHTML(u.name)} (${escapeHTML(u.email)})</option>`).join('')}</select><select id="share-role" aria-label="Permission"><option value="editor">Can edit</option><option value="viewer">Can view</option></select><button class="btn btn-primary" type="submit">Grant access</button></div></form>
      <div class="people-heading">PEOPLE WITH ACCESS</div><div class="share-person"><span class="person-avatar owner-avatar">${initials(doc.owner_name)}</span><div class="person-detail"><strong>${escapeHTML(doc.owner_name)} <span class="you-tag">Owner</span></strong><span>${escapeHTML(doc.owner_email)}</span></div><span class="person-role">Full access</span></div>
      ${shares.map(s=>`<div class="share-person"><span class="person-avatar">${initials(s.name)}</span><div class="person-detail"><strong>${escapeHTML(s.name)}</strong><span>${escapeHTML(s.email)}</span></div><span class="person-role">${s.role === 'editor' ? 'Can edit' : 'Can view'}</span><button data-revoke="${s.user_id}" class="revoke-button" aria-label="Revoke ${escapeHTML(s.name)} access" title="Remove access">✕</button></div>`).join('')}
      <div class="share-footer"><button id="copy-share-link" class="btn btn-outline">↗ &nbsp; Copy link</button><small>Only invited demo users can open this link.</small></div>
    </div></div>`;
    modalEvents();
    $('#copy-share-link').addEventListener('click', () => copyLink(doc.id));
    $('#share-form').addEventListener('submit', async event => {
      event.preventDefault();
      try {
        await api(`/api/documents/${doc.id}/shares`, {method:'POST',body:JSON.stringify({email:$('#share-email').value,role:$('#share-role').value})});
        toast('Access updated');await openShareModal(doc);
      } catch(error){toast(error.message,true);}
    });
    $$('[data-revoke]').forEach(button=>button.addEventListener('click',async()=>{
      try {await api(`/api/documents/${doc.id}/shares/${button.dataset.revoke}`,{method:'DELETE'});toast('Access removed');await openShareModal(doc);}
      catch(error){toast(error.message,true);}
    }));
  } catch(error){toast(error.message,true);}
}

async function switchAccount(user_id) {
  try {
    if (state.currentDoc) await flushSave();
    await api('/api/session',{method:'POST',body:JSON.stringify({user_id})});
    const {current, users} = await api('/api/session');
    state.session = {current,users};
    $('#account-avatar').textContent=initials(current.name);
    await refreshDocs();
    state.search='';
    showDashboard('all');
    toast(`Switched to ${current.name}`);
  } catch(error) {toast(error.message,true); $('#account-switch').value=state.session.current.id;}
}

async function navigatePopState() {
  const path = location.pathname;
  try {if (state.currentDoc) await flushSave();} catch {return;}
  if (path.startsWith('/docs/')) await openDoc(path.split('/')[2],false);
  else {await refreshDocs();showDashboard('all',false);}
}

async function init() {
  $('#new-document').addEventListener('click',createDoc);
  $('#import-document').addEventListener('click',()=>$('#file-input').click());
  $('#file-input').addEventListener('change',event=>importFile(event.target.files[0]));
  $$('.nav-item').forEach(btn => btn.addEventListener('click',async()=>{
    try {if(state.currentDoc) await flushSave(); await refreshDocs();state.search='';showDashboard(btn.dataset.nav);}
    catch(error){toast(error.message,true);}
  }));
  $('#brand-link').addEventListener('click',async e=>{e.preventDefault();try {if(state.currentDoc) await flushSave();await refreshDocs();showDashboard('all');}catch(error){toast(error.message,true);}});
  $('#account-switch').addEventListener('change',e=>switchAccount(e.target.value));
  window.addEventListener('popstate',navigatePopState);
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape')closeModal();
    if((event.ctrlKey || event.metaKey) && event.key==='s'){event.preventDefault();flushSave().catch(()=>{});}
  });
  try {
    state.session=await api('/api/session');
    $('#account-switch').value=state.session.current.id;
    $('#account-avatar').textContent=initials(state.session.current.name);
    await refreshDocs();
    const match=location.pathname.match(/^\/docs\/([^/]+)$/);
    if(match) await openDoc(match[1],false);
    else showDashboard('all',false);
  } catch(error) {
    $('#main').innerHTML=`<div class="fatal-error"><h2>Couldn't open Scribe</h2><p>${escapeHTML(error.message)}</p><button class="btn btn-primary" onclick="location.reload()">Try again</button></div>`;
  }
}

document.addEventListener('DOMContentLoaded',init);
