'use strict';

/* All user content is rendered with textContent. The only innerHTML below is the
   constant, bundled icon set. Audio and exports use authenticated blob requests. */
const ICONS = {
  library:'<rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 8h8M8 12h8M8 16h5"/>',
  device:'<path d="M9 7V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4"/><circle cx="12" cy="14" r="7"/><path d="M12 14h.01"/>',
  workflow:'<circle cx="5" cy="5" r="2"/><circle cx="19" cy="12" r="2"/><circle cx="5" cy="19" r="2"/><path d="M7 5h4a3 3 0 0 1 3 3v1a3 3 0 0 0 3 3M7 19h4a3 3 0 0 0 3-3v-1a3 3 0 0 1 3-3"/>',
  settings:'<path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><path d="m9 3-1 3-3 1-2 3 2 2-1 3 2 3 3-1 2 3h3l1-3 3-1 2-3-2-2 1-3-2-3-3 1-2-3Z"/>',
  lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
  refresh:'<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 7a7 7 0 0 1 12-1l2 3M4 15l2 3a7 7 0 0 0 12-1"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',
  storage:'<rect x="3" y="4" width="18" height="6" rx="2"/><rect x="3" y="14" width="18" height="6" rx="2"/><path d="M7 7h.01M7 17h.01M11 7h6M11 17h6"/>',
  audio:'<path d="M3 10v4M7 6v12M12 3v18M17 7v10M21 10v4"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  star:'<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z"/>',
  archive:'<path d="M4 8h16v12H4zM3 3h18v5H3zM9 12h6"/>',
  back:'<path d="m14 5-7 7 7 7"/>',
  tag:'<path d="M3 3h8l10 10-8 8L3 11Z"/><circle cx="7.5" cy="7.5" r="1"/>',
  file:'<path d="M5 3h9l5 5v13H5zM14 3v5h5M8 13h8M8 17h6"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
};
const $ = (selector, parent=document) => parent.querySelector(selector);
const $$ = (selector, parent=document) => [...parent.querySelectorAll(selector)];
const state = { token:'', view:'recordings', recordings:[], selected:null, selectedId:null,
  filter:'all', query:'', settings:null, transcription:null, jobs:[], audioURL:null,
  detailGeneration:0, libraryGeneration:0, panel:'transcript', polling:false, toastTimer:null,
  refreshing:false, sessionGeneration:0, total:0, dirtyNotes:new Set() };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}
function icon(name) {
  const node = el('span','icon');
  node.setAttribute('aria-hidden','true');
  node.innerHTML = '<svg viewBox="0 0 24 24">' + (ICONS[name] || ICONS.file) + '</svg>';
  return node;
}
function hydrateIcons(parent=document) {
  $$('[data-icon]',parent).forEach(node => { node.setAttribute('aria-hidden','true');
    node.innerHTML='<svg viewBox="0 0 24 24">'+(ICONS[node.dataset.icon] || ICONS.file)+'</svg>'; });
}
function initPendantAppearance() {
  const choices=$$('input[name="pendant-colour"]');
  const preview=$('#pendant-preview'),note=$('#pendant-colour-note');
  const storageKey='pendant_device_colour';
  function selectColour(value) {
    const choice=choices.find(input=>input.value===value) || choices[0];
    choice.checked=true;
    preview.dataset.colour=choice.value;
    preview.setAttribute('aria-label',choice.dataset.label+' Limitless Pendant illustration');
  }
  try{selectColour(localStorage.getItem(storageKey));}
  catch{selectColour('black');note.textContent='Colour applies to this visit. Browser storage is unavailable.';}
  choices.forEach(input=>input.addEventListener('change',()=>{
    if(!input.checked)return;
    selectColour(input.value);
    try{localStorage.setItem(storageKey,input.value);note.textContent=input.dataset.label+' selected. Saved in this browser.';}
    catch{note.textContent=input.dataset.label+' selected for this visit. Browser storage is unavailable.';}
  }));
}
function initSyncPreference() {
  const select=$('#capture-duration');
  try{const saved=localStorage.getItem('pendant_sync_seconds');if([...select.options].some(option=>option.value===saved))select.value=saved;}catch{}
  select.addEventListener('change',()=>{try{localStorage.setItem('pendant_sync_seconds',select.value);}catch{}});
}
function syncTimeLabel(seconds) {
  return seconds>=3600?'1 hour':seconds<60?`${seconds} seconds`:`${seconds/60} minute${seconds===60?'':'s'}`;
}
function button(text, action, className='button secondary', iconName) {
  const node=el('button',className); node.type='button';
  if(iconName) node.append(icon(iconName)); node.append(document.createTextNode(text));
  node.addEventListener('click',action); return node;
}
function badge(text,kind='neutral') { return el('span','badge '+kind,text); }
function dateText(value,options={day:'numeric',month:'short',year:'numeric'}) {
  const date=new Date(value); return Number.isNaN(date.getTime())?'Date unavailable':date.toLocaleDateString('en-GB',options);
}
function timeText(value) {const date=new Date(value);return Number.isNaN(date.getTime())?'':date.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});}
function duration(value) {
  if(!Number.isFinite(Number(value)) || value===null || value===undefined) return 'Duration pending';
  const seconds=Math.max(0,Math.round(Number(value))),m=Math.floor(seconds/60),s=seconds%60;
  return m>=60?`${Math.floor(m/60)}h ${m%60}m`:`${m}:${String(s).padStart(2,'0')}`;
}
function statusLabel(status) {return ({ready:'Ready to transcribe',queued:'Queued',transcribing:'Transcribing',transcribed:'Transcribed',transcription_failed:'Transcription failed',model_download:'Model download',interrupted:'Interrupted'})[status] || String(status || 'Unknown').replaceAll('_',' ').replace(/^./,x=>x.toUpperCase());}
function statusKind(status) {return ['completed','transcribed'].includes(status)?'good':['failed','transcription_failed','interrupted'].includes(status)?'error':['running','queued','transcribing'].includes(status)?'warning':'neutral';}
function toast(message,error=false) {
  const node=$('#toast'); clearTimeout(state.toastTimer);node.textContent=message;node.className='toast'+(error?' error':'');node.hidden=false;
  state.toastTimer=setTimeout(()=>{node.hidden=true;},error?9000:4500);
}
function alertMessage(message) {const node=$('#global-alert');node.textContent=message || '';node.hidden=!message;}
function errorMessage(data) {
  const detail=data?.detail ?? data;
  if(typeof detail==='string') return detail;
  if(Array.isArray(detail)) return detail.map(x=>x.msg||String(x)).join('; ');
  if(detail?.message) return detail.message;
  return detail?.error || 'The request could not be completed.';
}
async function api(path,options={}) {
  const headers=new Headers(options.headers || {});
  headers.set('Authorization','Bearer '+state.token);
  if(options.body && !(options.body instanceof FormData)) headers.set('Content-Type','application/json');
  let response;
  try { response=await fetch(path,{...options,headers,credentials:'same-origin',cache:'no-store'}); }
  catch {throw new Error('Cannot reach the local service. Check that pendant-local serve is still running.');}
  if(!response.ok) {
    let data;try{data=await response.json();}catch{data={detail:`Request failed (${response.status}).`};}
    if(response.status===401 && !$('#workspace').hidden) lockWorkspace();
    throw new Error(errorMessage(data));
  }
  return options.blob?response.blob():response.status===204?null:response.json();
}
const post=(path,body)=>api(path,{method:'POST',...(body!==undefined?{body:JSON.stringify(body)}:{})});
async function busy(node,work,label) {
  if(node?.disabled) return;
  const original=node?.textContent;
  if(node){node.disabled=true;node.setAttribute('aria-busy','true');if(label)node.textContent=label;}
  try{return await work();}catch(error){toast(error.message,true);return null;}
  finally{if(node){node.disabled=false;node.removeAttribute('aria-busy');if(label)node.textContent=original;}}
}
function busyDevice(node,work,label) {
  return busy(node,async()=>{
    const controls=$$('button',$('#view-device'));
    const previous=controls.map(button=>button.disabled);
    controls.forEach(button=>{button.disabled=true;});
    try{return await work();}
    finally{controls.forEach((button,index)=>{button.disabled=previous[index];});}
  },label);
}
function confirmAction(title,message,confirmText='Confirm') {
  return new Promise(resolve=>{
    const dialog=$('#confirm-dialog');$('#confirm-title').textContent=title;$('#confirm-description').textContent=message;$('#confirm-submit').textContent=confirmText;
    dialog.returnValue='cancel';dialog.addEventListener('close',()=>resolve(dialog.returnValue==='confirm'),{once:true});dialog.showModal();
  });
}
function setView(view,focus=false) {
  if(!['recordings','device','workflow','settings'].includes(view)) view='recordings';
  state.view=view;
  $$('.view').forEach(node=>node.hidden=node.id!=='view-'+view);
  $$('[data-view]').forEach(node=>{const active=node.dataset.view===view;node.classList.toggle('active',active);if(active)node.setAttribute('aria-current','page');else node.removeAttribute('aria-current');});
  $('#view-title').textContent=({recordings:'Recordings',device:'Device',workflow:'Workflow',settings:'Settings'})[view];
  history.replaceState(null,'','#'+view);
  if(focus) $('#main-content').focus({preventScroll:true});
  if(view==='device') loadCaptures().catch(error=>toast(error.message,true));
  if(view==='workflow'||view==='settings') refreshJobs().catch(error=>toast(error.message,true));
}
function revokeAudio() { if(state.audioURL){URL.revokeObjectURL(state.audioURL);state.audioURL=null;} const audio=$('#recording-audio');if(audio){audio.pause();audio.removeAttribute('src');audio.load();} }
function lockWorkspace() {
  state.sessionGeneration++;state.detailGeneration++;state.libraryGeneration++;state.token='';try{sessionStorage.removeItem('pendant_token');}catch{}
  revokeAudio();state.selected=null;state.selectedId=null;state.recordings=[];state.jobs=[];state.dirtyNotes.clear();state.total=0;
  $('#view-recordings').classList.remove('has-selection');renderRecordingList();renderEmptyDetail();
  $('#workspace').hidden=true;$('#login-view').hidden=false;$('#api-token').value='';$('#api-token').focus();alertMessage('');
}
function renderEmptyDetail() {
  const empty=el('div','empty-detail'),mark=el('div','empty-icon');mark.append(icon('audio'));
  empty.append(mark,el('p','eyebrow','A LITTLE LESS TO REMEMBER'),el('h2','','Your recordings, in one place.'),el('p','','Import an audio file or sync your Pendant. Listen, transcribe and keep what matters.'));
  const actions=el('div','empty-actions');actions.append(button('Import your first recording',()=>$('#audio-import').click(),'button primary'),button('Set up your Pendant',()=>setView('device'),'button secondary'));empty.append(actions);
  const trust=el('div','empty-trust');trust.append(icon('lock'),document.createTextNode('Local storage. Your choice of transcription model.'));empty.append(trust);$('#recording-detail').replaceChildren(empty);
}
async function login(token) {
  state.token=token.trim();
  try {
    state.settings=await api('/v1/settings');
    try{sessionStorage.setItem('pendant_token',state.token);}catch{}
    state.sessionGeneration++;$('#login-view').hidden=true;$('#workspace').hidden=false;$('#api-token').value='';$('#login-error').textContent='';
    renderSettings();setView(location.hash.slice(1) || 'recordings');
    await refreshWorkspace();
  }catch(error){state.token='';try{sessionStorage.removeItem('pendant_token');}catch{};$('#login-error').textContent=error.message;}
}
async function refreshWorkspace() {
  if(state.refreshing || !state.token)return;
  state.refreshing=true;$('#refresh-button').classList.add('spinning');
  try {
    const results=await Promise.allSettled([loadRecordings(),refreshJobs(),api('/v1/settings')]);
    if(results[2].status==='fulfilled'){state.settings=results[2].value;renderSettings();}
    const failures=results.filter(x=>x.status==='rejected');alertMessage(failures.map(x=>x.reason.message).join(' '));
    if(state.view==='device') await loadCaptures();
  }catch(error){alertMessage(error.message);}finally{state.refreshing=false;$('#refresh-button').classList.remove('spinning');}
}
async function loadRecordings() {
  const generation=++state.libraryGeneration;
  const query=new URLSearchParams({query:state.query,archived:String(state.filter==='archived'),status:'all'});
  const result=await api('/v1/recordings?'+query);
  if(generation!==state.libraryGeneration || !state.token)return;
  state.recordings=result.recordings || [];state.total=result.total ?? state.recordings.length;
  renderRecordingList();
}
function renderRecordingList() {
  const list=$('#recording-list');list.replaceChildren();
  const rows=state.recordings.filter(row=>state.filter!=='starred'||row.starred);
  $('#nav-count').textContent=String(state.total);$('#library-count').textContent=state.total>state.recordings.length?`${rows.length} of ${state.total} results`:`${rows.length} recording${rows.length===1?'':'s'}`;
  $('#library-foot-text').textContent=state.total>state.recordings.length?'Showing first '+state.recordings.length+' results. Search to narrow the list.':'Stored on this computer';
  if(!rows.length){const empty=el('div','list-empty');empty.append(icon(state.query?'search':'library'),el('h3','',state.query?'No matching recordings':state.filter==='starred'?'No starred recordings':state.filter==='archived'?'Your archive is empty':'Your library starts here'),el('p','',state.query?'Try a different title or phrase.':state.filter==='all'?'Import audio or sync your Pendant to get started.':state.filter==='starred'?'Star a recording to keep it close to hand.':'Archived recordings will appear here.'));if(state.filter==='all'&&!state.query){const row=button('Import audio',()=>$('#audio-import').click(),'button secondary','plus');row.style.marginTop='20px';empty.append(row);}list.append(empty);return;}
  let previousDate='';
  rows.forEach(record=>{
    const group=dateText(record.created_at,{weekday:'short',day:'numeric',month:'short'});
    if(group!==previousDate){list.append(el('p','date-label',group));previousDate=group;}
    const row=button('',()=>selectRecording(record.id),'recording-row'+(record.id===state.selectedId?' selected':''));
    row.setAttribute('aria-label',`${record.title}, ${statusLabel(record.status)}`);row.setAttribute('aria-pressed',String(record.id===state.selectedId));
    const top=el('div','row-top');top.append(el('span','row-title',record.title||'Untitled recording'));if(record.starred)top.append(el('span','row-star','☆'));
    const meta=el('div','row-meta');meta.append(el('span','',timeText(record.created_at)),el('span','','·'),el('span','',duration(record.duration_seconds)),el('span','','·'),el('span','',record.source==='pendant'?'Pendant':'Imported'));
    if(record.audio_incomplete)meta.append(el('span','','·'),el('span','','Partial download'));
    row.append(top,meta);if(record.transcript_text)row.append(el('p','row-excerpt',record.transcript_text));
    const bottom=el('div','row-bottom'),tags=el('div');(record.tags||[]).slice(0,2).forEach(tag=>tags.append(el('span','tag-chip',tag)));bottom.append(tags,badge(statusLabel(record.status),statusKind(record.status)));row.append(bottom);list.append(row);
  });
}
async function selectRecording(id,{keepScroll=false}={}) {
  if(state.selectedId && state.dirtyNotes.has(state.selectedId)){
    if(keepScroll)return;
    if(!await confirmAction('Leave without saving notes?','Your current notes have not been saved. Leaving this recording will discard those edits.','Discard edits'))return;
    state.dirtyNotes.delete(state.selectedId);
  }
  revokeAudio();
  const generation=++state.detailGeneration;state.selectedId=id;state.panel='transcript';
  $('#view-recordings').classList.add('has-selection');renderRecordingList();
  const detail=$('#recording-detail');
  if(!keepScroll){detail.replaceChildren(el('div','loading-line'));detail.append(el('p','list-empty','Loading recording…'));detail.scrollTop=0;}
  try{const record=await api('/v1/recordings/'+encodeURIComponent(id));if(generation!==state.detailGeneration||!state.token)return;state.selected=record;renderDetail(record);}
  catch(error){if(generation!==state.detailGeneration)return;detail.replaceChildren(button('Back to recordings',backToLibrary,'button secondary mobile-back','back'),el('p','list-empty',error.message));toast(error.message,true);}
}
function backToLibrary() {state.detailGeneration++;const audio=$('#recording-audio');if(audio)audio.pause();$('#view-recordings').classList.remove('has-selection');$('.recording-row.selected')?.focus({preventScroll:true});}
async function patchRecording(id,changes) {
  const record=await api('/v1/recordings/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify(changes)});
  if(state.selectedId===id)state.selected={...state.selected,...record};
  const index=state.recordings.findIndex(x=>x.id===id);if(index>=0)state.recordings[index]={...state.recordings[index],...record};
  renderRecordingList();return record;
}
function renderDetail(record) {
  revokeAudio();const detail=$('#recording-detail');detail.replaceChildren();
  const toolbar=el('div','detail-toolbar');toolbar.append(button('Library',backToLibrary,'button secondary mobile-back','back'));
  const source=el('span','source-label');source.append(icon(record.source==='pendant'?'device':'file'),document.createTextNode(record.source==='pendant'?'PENDANT RECORDING':'IMPORTED AUDIO'));toolbar.append(source);
  const actions=el('div','button-row');
  const star=button('',()=>busy(star,async()=>{const updated=await patchRecording(record.id,{starred:!state.selected.starred});star.classList.toggle('on',updated.starred);star.setAttribute('aria-pressed',String(updated.starred));star.setAttribute('aria-label',updated.starred?'Unstar recording':'Star recording');}), 'icon-button'+(record.starred?' on':''),'star');star.setAttribute('aria-label',record.starred?'Unstar recording':'Star recording');star.setAttribute('aria-pressed',String(!!record.starred));star.title='Star recording';
  const archive=button('',()=>busy(archive,async()=>{const updated=await patchRecording(record.id,{archived:!state.selected.archived});archive.classList.toggle('on',updated.archived);archive.setAttribute('aria-label',updated.archived?'Restore from archive':'Archive recording');toast(updated.archived?'Recording archived.':'Recording restored.');await loadRecordings();}), 'icon-button'+(record.archived?' on':''),'archive');archive.setAttribute('aria-label',record.archived?'Restore from archive':'Archive recording');archive.title='Archive or restore';
  const format=el('select','export-select');format.setAttribute('aria-label','Export format');[['md','Markdown'],['txt','Plain text'],['srt','Subtitles'],['json','JSON']].forEach(([value,label])=>{const opt=el('option','',label);opt.value=value;format.append(opt);});
  const exportButton=button('Export',()=>busy(exportButton,()=>exportRecording(record.id,format.value)),'button secondary','download');actions.append(star,archive,format,exportButton);toolbar.append(actions);detail.append(toolbar);
  const body=el('div','detail-body'),title=el('input','detail-title');title.value=record.title||'';title.maxLength=200;title.setAttribute('aria-label','Recording title');
  const saveState=el('p','detail-save-state');saveState.setAttribute('aria-live','polite');
  title.addEventListener('change',async()=>{if(!title.value.trim()){title.value=state.selected.title;return;}try{saveState.textContent='Saving title…';await patchRecording(record.id,{title:title.value.trim()});saveState.textContent='Title saved';}catch(error){saveState.textContent=error.message;toast(error.message,true);}});
  const meta=el('div','detail-meta');meta.append(el('span','',dateText(record.created_at,{weekday:'long',day:'numeric',month:'long',year:'numeric'})),el('span','','·'),el('span','',timeText(record.created_at)),el('span','','·'),el('span','',duration(record.duration_seconds)));
  const tags=el('div','tags-editor'),tagInput=el('input');tagInput.value=(record.tags||[]).join(', ');tagInput.placeholder='Add tags, separated by commas';tagInput.setAttribute('aria-label','Recording tags, separated by commas');tags.append(icon('tag'),tagInput);
  tagInput.addEventListener('change',async()=>{try{const tags=[...new Set(tagInput.value.split(',').map(x=>x.trim()).filter(Boolean))];await patchRecording(record.id,{tags});toast('Tags saved.');}catch(error){toast(error.message,true);}});
  body.append(title,saveState,meta,tags);
  if(record.audio_incomplete)body.append(el('p','inline-note','Partial recording: the recording’s end has not been received. A later sync can add more audio to this entry.'));
  if(record.audio_version_count>1)body.append(el('p','field-help',`Keeping the longest verified audio from ${record.audio_version_count} downloaded versions. Original files are retained.`));
  if(record.merged_into)body.append(button('Open main recording',()=>selectRecording(record.merged_into),'text-button'));
  const audioCard=el('div','audio-card'),audioHead=el('div','audio-head');audioHead.append(el('span','','ORIGINAL AUDIO'),el('span','',record.source==='pendant'?'Synced from Pendant':'Local import'));audioCard.append(audioHead);
  const audio=el('audio');audio.id='recording-audio';audio.controls=true;audio.preload='metadata';audio.setAttribute('aria-label','Play selected recording');
  const audioStatus=el('p','audio-placeholder','Loading audio…');audioCard.append(audioStatus,audio);body.append(audioCard);
  loadAudio(record.id,audio,audioStatus);
  const tabs=el('div','detail-section-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Recording details');
  const transcriptTab=button('Transcript',()=>switchDetailTab('transcript'),'detail-tab active');transcriptTab.id='transcript-tab';transcriptTab.setAttribute('role','tab');transcriptTab.setAttribute('aria-selected','true');transcriptTab.setAttribute('aria-controls','transcript-panel');
  const notesTab=button('Notes',()=>switchDetailTab('notes'),'detail-tab');notesTab.id='notes-tab';notesTab.setAttribute('role','tab');notesTab.setAttribute('aria-selected','false');notesTab.setAttribute('aria-controls','notes-panel');notesTab.tabIndex=-1;
  tabs.append(transcriptTab,notesTab,badge(statusLabel(record.status),statusKind(record.status)));body.append(tabs);
  tabs.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?'transcript':event.key==='End'?'notes':state.panel==='transcript'?'notes':'transcript';switchDetailTab(next);$('#'+next+'-tab').focus();}});
  const transcriptPanel=el('section');transcriptPanel.id='transcript-panel';transcriptPanel.setAttribute('role','tabpanel');transcriptPanel.setAttribute('aria-labelledby','transcript-tab');transcriptPanel.tabIndex=0;
  renderTranscript(record,transcriptPanel,audio);body.append(transcriptPanel);
  const notesPanel=el('section');notesPanel.id='notes-panel';notesPanel.setAttribute('role','tabpanel');notesPanel.setAttribute('aria-labelledby','notes-tab');notesPanel.hidden=true;
  const notesLabel=el('label','','Your notes'),notes=el('textarea','notes-textarea');notes.id='recording-notes';notesLabel.htmlFor=notes.id;notes.value=record.notes||'';notes.placeholder='Decisions, follow-ups, useful context…';
  notes.addEventListener('input',()=>state.dirtyNotes.add(record.id));
  const saveNotes=button('Save notes',()=>busy(saveNotes,async()=>{await patchRecording(record.id,{notes:notes.value});state.dirtyNotes.delete(record.id);toast('Notes saved.');}),'button primary');notesPanel.append(notesLabel,notes,saveNotes);body.append(notesPanel);detail.append(body);switchDetailTab(state.panel);
}
function switchDetailTab(panel) {
  state.panel=panel;['transcript','notes'].forEach(name=>{const active=name===panel;const tab=$('#'+name+'-tab');if(tab){tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;$('#'+name+'-panel').hidden=!active;}});
}
async function loadAudio(id,audio,status) {
  const generation=state.detailGeneration;
  try{const blob=await api('/v1/recordings/'+encodeURIComponent(id)+'/audio',{blob:true});if(generation!==state.detailGeneration||!audio.isConnected||!state.token)return;state.audioURL=URL.createObjectURL(blob);audio.src=state.audioURL;status.hidden=true;audio.addEventListener('error',()=>{status.textContent='This browser cannot play the original format. The audio file is still stored locally.';status.hidden=false;});}
  catch(error){if(audio.isConnected){status.textContent=error.message;audio.hidden=true;}}
}
function modelLabel(id){return id===state.transcription?.diarization?.model?'Local speaker analysis':state.transcription?.models?.find(model=>model.id===id)?.label || id;}
function modelSize(model){return model.download_mb>=1000?`${(model.download_mb/1000).toFixed(2)} GB`:`${model.download_mb} MB`;}
function transcriptionControls(record) {
  const box=el('div','transcription-controls'),pending=['queued','transcribing'].includes(record.status);
  if(pending){box.append(el('p','field-help','This recording has a transcription job in the queue.'),button('View workflow',()=>setView('workflow')));return box;}
  const models=state.transcription?.models || [],ready=models.filter(model=>model.downloaded);
  if(!state.transcription?.installed || !ready.length){box.append(el('p','field-help',state.transcription?.installed?'Download a model to transcribe this recording.':'The local speech engine needs installing.'),button('Set up transcription',()=>setView('settings'),'button primary'));return box;}
  const fields=el('div','transcription-options'),modelLabelNode=el('label','','Model for this recording'),model=el('select'),languageLabel=el('label','','Language'),language=el('select');
  model.id='recording-model';modelLabelNode.htmlFor=model.id;language.id='recording-language';languageLabel.htmlFor=language.id;
  ready.forEach(item=>{const option=el('option','',item.label);option.value=item.id;model.append(option);});
  model.value=ready.some(item=>item.id===defaultModel())?defaultModel():ready[0].id;
  [...$('#language-select').options].forEach(option=>language.append(option.cloneNode(true)));language.value=state.settings?.transcription?.default_language||'';
  const adaptLanguage=()=>{if(model.value.endsWith('.en'))language.value='en';language.disabled=model.value.endsWith('.en');};model.addEventListener('change',adaptLanguage);adaptLanguage();
  modelLabelNode.append(model);languageLabel.append(language);fields.append(modelLabelNode,languageLabel);box.append(fields);
  const speakerOptions=el('div','transcription-options'),speakerLabel=el('label','checkbox-label'),identify=el('input'),countLabel=el('label','','Number of speakers'),count=el('select');
  identify.type='checkbox';identify.id='recording-diarize';speakerLabel.htmlFor=identify.id;
  identify.checked=!!(record.transcript?.diarization||state.settings?.transcription?.diarize);
  identify.disabled=!state.transcription?.speaker_labels;
  if(identify.disabled)identify.checked=false;
  speakerLabel.append(identify,el('span','','Identify speakers'));
  count.id='recording-speaker-count';countLabel.htmlFor=count.id;
  const automatic=el('option','','Estimate automatically');automatic.value='';count.append(automatic);
  for(let i=1;i<=20;i++){const option=el('option','',String(i));option.value=String(i);count.append(option);}
  count.value=String(record.transcript?.diarization?.requested_speakers||'');
  const adaptSpeakers=()=>{count.disabled=!identify.checked;};identify.addEventListener('change',adaptSpeakers);adaptSpeakers();countLabel.append(count);speakerOptions.append(speakerLabel,countLabel);box.append(speakerOptions);
  if(identify.disabled)box.append(el('p','field-help','Download the local speaker models in Settings to identify speakers.'),button('Set up speaker analysis',()=>setView('settings')));
  else box.append(el('p','field-help','Speaker labels are estimates for this recording. If you know how many people spoke, choose the count. Talking over each other can leave uncertain labels.'));
  const action=button(record.transcript?'Transcribe again':'Transcribe recording',async()=>{
    if(record.transcript&&!await confirmAction('Replace this transcript?',`Run ${modelLabel(model.value)}${identify.checked?' with speaker analysis':''}? Your existing transcript stays available until the new job completes. Any speaker names will need assigning again.`,'Transcribe again'))return;
    await queueTranscription(record.id,action,model.value,language.value||null,{diarize:identify.checked,num_speakers:identify.checked&&count.value?Number(count.value):null});
  },'button primary','audio');box.append(action);return box;
}
function renderTranscript(record,panel,audio) {
  if(record.transcript_needs_update)panel.append(el('p','inline-note','More audio has been added since this transcript was made. Your existing transcript and speaker names are preserved. Choose Transcribe again to include the additional audio.'));
  const transcript=record.transcript;panel.append(transcriptionControls(record));
  if(!transcript?.text && !(transcript?.segments||[]).length){
    const empty=el('div','transcript-empty'),pending=['queued','transcribing'].includes(record.status);
    empty.append(el('h3','',pending?'Transcription is in progress.':record.status==='transcription_failed'?'Transcription needs attention.':record.status==='transcribed'?'No speech was transcribed.':'Make this recording searchable.'),el('p','',pending?'Follow the job in Workflow. The finished transcript will appear here.':record.error||(record.status==='transcribed'?'The model returned an empty transcript. Listen to the audio and check the language or model before trying again.':'Choose a downloaded model above. Your audio stays on this computer.')));panel.append(empty);return;
  }
  const diarization=transcript.diarization;
  panel.append(el('p','field-help',`${modelLabel(transcript.model||'Local model')} · ${transcript.language||'Language unknown'}${Number.isFinite(transcript.processing_seconds)?' · Processed in '+duration(transcript.processing_seconds):''} · ${diarization?`${diarization.speaker_count} speaker${diarization.speaker_count===1?'':'s'} labelled${diarization.requested_speakers?' · Requested '+diarization.requested_speakers:' · Estimated count'}`:'Speaker analysis not run'}`));
  if(diarization){
    const details=el('details','speaker-editor'),form=el('form','speaker-form');details.append(el('summary','','Name speakers'),el('p','field-help','Names apply only to this recording. Listen before assigning them; the model does not know who anyone is.'));
    Object.entries(transcript.speakers||{}).forEach(([id,name],index)=>{const label=el('label','',`Speaker ${index+1}`),input=el('input');input.name=id;input.value=name;input.maxLength=80;input.required=true;input.id='name-'+id;label.htmlFor=input.id;label.append(input);form.append(label);});
    const save=el('button','button secondary','Save speaker names');save.type='submit';save.disabled=['queued','transcribing'].includes(record.status)||!Object.keys(transcript.speakers||{}).length;form.append(save);details.append(form);panel.append(details);
    form.addEventListener('submit',event=>{event.preventDefault();busy(save,async()=>{const names=Object.fromEntries(new FormData(form));const updated=await api('/v1/recordings/'+encodeURIComponent(record.id)+'/speakers',{method:'PATCH',body:JSON.stringify({names,revision:transcript.speaker_revision})});Object.assign(transcript,updated.transcript);renderSegments();toast('Speaker names saved for this recording.');});});
    if(diarization.unassigned_segments)panel.append(el('p','field-help',`${diarization.unassigned_segments} segment${diarization.unassigned_segments===1?'':'s'} could not be assigned confidently. These are labelled “Speaker uncertain”.`));
  }
  const actions=el('div','transcript-actions'),search=el('label','transcript-find');search.append(icon('search'));const input=el('input');input.type='search';input.placeholder='Find in transcript';input.setAttribute('aria-label','Find in selected transcript');search.append(input);actions.append(search);panel.append(actions);
  const segmentsNode=el('div');panel.append(segmentsNode);
  const segments=transcript.segments?.length?transcript.segments:[{start:0,end:transcript.duration||record.duration_seconds,text:transcript.text}];
  function renderSegments(){segmentsNode.replaceChildren();const query=input.value.trim().toLocaleLowerCase();let matches=0;
    segments.forEach(segment=>{if(query&&!String(segment.text).toLocaleLowerCase().includes(query))return;matches++;const row=el('div','transcript-segment');row.dataset.start=String(segment.start||0);row.dataset.end=String(segment.end||0);
      const time=button(duration(segment.start||0),()=>{if(audio.readyState>0){audio.currentTime=Math.max(0,segment.start||0);audio.play().catch(()=>{});}else toast('Audio is still loading.');},'transcript-time');time.setAttribute('aria-label','Play from '+duration(segment.start||0));const text=el('div');if(diarization||segment.speaker)text.append(el('p','transcript-speaker',transcript.speakers?.[segment.speaker]||segment.speaker||'Speaker uncertain'));text.append(el('p','transcript-text',segment.text));row.append(time,text);segmentsNode.append(row);
    });if(!matches)segmentsNode.append(el('p','list-empty','No matching transcript segments.'));
  }
  input.addEventListener('input',renderSegments);renderSegments();
  audio.addEventListener('timeupdate',()=>{$$('.transcript-segment',segmentsNode).forEach(row=>row.classList.toggle('active',audio.currentTime>=Number(row.dataset.start)&&audio.currentTime<Number(row.dataset.end)));});
}
function defaultModel(){return state.settings?.transcription?.default_model || 'base.en';}
async function queueTranscription(id,node,model=defaultModel(),language=state.settings?.transcription?.default_language||null,speakerOptions={}) {
  await busy(node,async()=>{await post('/v1/recordings/'+encodeURIComponent(id)+'/transcribe',{model,language,...speakerOptions});toast('Recording added to the transcription queue.');await refreshJobs();await loadRecordings();if(state.selectedId===id)await selectRecording(id,{keepScroll:true});});
}
async function queueUntranscribed() {
  const node=$('#batch-transcribe');
  await busy(node,async()=>{
    const result=await api('/v1/recordings?archived=false&status=all');
    const records=result.recordings.filter(record=>!record.has_transcript&&!['queued','transcribing'].includes(record.status)).slice(0,100);
    if(!records.length){$('#batch-result').textContent='No untranscribed recordings are waiting in this batch.';return;}
    if(!await confirmAction(`Queue ${records.length} recording${records.length===1?'':'s'}?`,`Use ${modelLabel(defaultModel())} for up to ${duration(records.reduce((sum,record)=>sum+(record.duration_seconds||0),0))} of audio. Jobs run one at a time; processing time depends on the model and audio. Existing transcripts will be kept.`,'Queue recordings'))return;
    const batch=await post('/v1/transcription/batch',{recording_ids:records.map(record=>record.id)});
    $('#batch-result').textContent=`${batch.queued} recording${batch.queued===1?'':'s'} queued. ${batch.skipped.length} skipped.${batch.skipped.length?' '+[...new Set(batch.skipped.map(item=>item.reason))].join(' '):''}${result.total>500?' Showing the first 500 library entries. Search and open older recordings individually.':''}`;
    await refreshJobs();await loadRecordings();
  });renderWorkflowReadiness();
}
async function exportRecording(id,format) {
  const blob=await api('/v1/recordings/'+encodeURIComponent(id)+'/export?format='+encodeURIComponent(format),{blob:true});
  const url=URL.createObjectURL(blob),anchor=el('a');anchor.href=url;anchor.download=(state.selected?.title||'recording').replace(/[^a-zA-Z0-9._ -]/g,'_').slice(0,100)+'.'+format;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function importFiles(files) {
  if(!files.length)return;let imported=0,lastId=null,failed=[];
  await busy($('#import-button'),async()=>{for(const file of files){toast(`Importing ${file.name}…`);const form=new FormData();form.append('file',file);try{const record=await api('/v1/recordings/import',{method:'POST',body:form});imported++;lastId=record.id;}catch(error){failed.push(file.name+': '+error.message);}}
    state.filter='all';state.query='';$('#recording-search').value='';updateFilters();setView('recordings');await loadRecordings();if(lastId)await selectRecording(lastId);await refreshJobs();
    if(failed.length)alertMessage(failed.join(' '));toast(`${imported} recording${imported===1?'':'s'} imported.${failed.length?' '+failed.length+' could not be imported.':''}`,!!failed.length);
  },'Importing…');$('#audio-import').value='';
}
function updateFilters(){$$('[data-filter]').forEach(node=>{const active=node.dataset.filter===state.filter;node.classList.toggle('active',active);node.setAttribute('aria-pressed',String(active));});}
async function refreshJobs() {
  const generation=state.sessionGeneration;
  const status=await api('/v1/transcription/status');if(generation!==state.sessionGeneration||!state.token)return;
  const previous=state.jobs;state.transcription=status;state.jobs=status.jobs||[];
  renderJobs();renderTranscriptionSettings();
  const selectedFinished=state.jobs.some(job=>job.recording_id===state.selectedId&&['completed','failed','cancelled','interrupted'].includes(job.status)&&previous.some(old=>old.id===job.id&&['queued','running'].includes(old.status)));
  const finished=state.jobs.some(job=>job.kind==='transcription'&&['completed','failed','cancelled','interrupted'].includes(job.status)&&previous.some(old=>old.id===job.id&&['queued','running'].includes(old.status)));
  if(finished)await loadRecordings();
  if(selectedFinished){const focused=document.activeElement;if(!focused?.matches('input,textarea')&&!state.dirtyNotes.has(state.selectedId)&&state.view==='recordings'&&state.selectedId)await selectRecording(state.selectedId,{keepScroll:true});else toast(state.dirtyNotes.has(state.selectedId)?'Transcription updated. Reopen the recording when your notes are saved.':'Transcript ready. Open the recording to review it.');}
}
function renderJobs() {
  const list=$('#job-list'),focusId=list.contains(document.activeElement)?document.activeElement.id:null;list.replaceChildren();
  const active=state.jobs.filter(job=>['queued','running'].includes(job.status));$('#queue-count').hidden=!active.length;$('#queue-count').textContent=String(active.length);
  $('#queue-summary').textContent=`${active.filter(job=>job.status==='running').length} running · ${active.filter(job=>job.status==='queued').length} waiting · ${state.jobs.filter(job=>job.status==='completed').length} completed`+(state.jobs.some(job=>job.stopping)?' · Waiting for a cancelled operation to stop.':' · One job runs at a time.');
  if(!state.jobs.length){list.append(el('div','table-empty','Your queue is clear. Choose a recording or queue the untranscribed library.'));return;}
  const sorted=[...state.jobs].sort((a,b)=>Number(['queued','running'].includes(b.status))-Number(['queued','running'].includes(a.status)));
  sorted.forEach(job=>{const row=el('div','table-row'),copy=el('div','job-copy');const recording=state.recordings.find(x=>x.id===job.recording_id);
    copy.append(el('strong','',job.kind!=='transcription'?`Download ${modelLabel(job.model)}`:recording?.title || 'Recording transcription'),el('p','',`${modelLabel(job.model)}${job.diarize?' · Identify speakers'+(job.num_speakers?' ('+job.num_speakers+')':' (automatic)'):''} · ${dateText(job.created_at)} ${timeText(job.created_at)}${job.attempts?' · Attempt '+job.attempts:''}${Number.isFinite(job.elapsed_seconds)?' · '+duration(job.elapsed_seconds)+' elapsed':''}`));
    if(job.status==='running'){
      const progress=job.progress||{},stage=({starting:'Starting',loading_model:'Loading model into memory',reading_audio:'Reading audio and detecting speech',transcribing:'Transcribing speech',loading_speaker_models:'Loading speaker models',identifying_speakers:'Identifying speakers',downloading:'Downloading model files',checking_model:'Checking downloaded files',saving_transcript:'Saving transcript'})[progress.stage]||'Processing';
      const processed=Number(progress.processed_seconds),total=Number(progress.audio_duration_seconds);
      copy.append(el('p','job-progress-text',stage+(Number.isFinite(job.files_bytes)?` · ${(job.files_bytes/1000000).toFixed(1)} MB on disk`:'')+(total>0?` · ${duration(processed)} / ${duration(total)} audio`:'')+'.'));
      const meter=el('progress','job-progress');meter.setAttribute('aria-label',stage);if(total>0){meter.max=total;meter.value=Math.min(processed,total);}copy.append(meter);
    }
    if(job.error)copy.append(el('p','job-error',job.error));
    const actions=el('div','button-row');actions.append(badge(job.stopping?'Stopping':statusLabel(job.status),statusKind(job.status)));
    if(['queued','running'].includes(job.status)){const cancel=button('Cancel',()=>busy(cancel,async()=>{await post('/v1/jobs/'+encodeURIComponent(job.id)+'/cancel');await refreshJobs();toast('Cancellation requested. The current native operation may need time to stop.');}));cancel.id='job-cancel-'+job.id;actions.append(cancel);}
    if(['failed','cancelled','interrupted'].includes(job.status)){const retry=button('Retry',()=>busy(retry,async()=>{await post('/v1/jobs/'+encodeURIComponent(job.id)+'/retry');await refreshJobs();toast('Job queued again.');}));retry.id='job-retry-'+job.id;retry.disabled=!!job.stopping;actions.append(retry);}
    if(job.recording_id){const open=button('Open recording',()=>{setView('recordings');selectRecording(job.recording_id);});open.id='job-open-'+job.id;actions.append(open);}row.append(copy,actions);list.append(row);
  });
  if(focusId)document.getElementById(focusId)?.focus({preventScroll:true});
}
function renderSettings() {
  const settings=state.settings;if(!settings)return;
  $('#device-address').value=settings.address || '';
  const selected=settings.transcription?.default_model || 'base.en',model=$('#model-select');
  if(![...model.options].some(x=>x.value===selected)){const option=el('option','',selected);option.value=selected;model.prepend(option);}model.value=selected;
  const language=settings.transcription?.default_language || '';if(![...$('#language-select').options].some(x=>x.value===language)){const option=el('option','',language);option.value=language;$('#language-select').append(option);}$('#language-select').value=language;
  if($('#auto-transcribe'))$('#auto-transcribe').checked=!!settings.transcription?.auto_transcribe;
  $('#default-diarize').checked=!!settings.transcription?.diarize;
  const facts=$('#storage-facts');facts.replaceChildren();appendFact(facts,'Data directory',settings.data_dir||'Managed by local service');appendFact(facts,'Service version',settings.version||'Not reported');appendFact(facts,'Workspace access','Local access token');appendFact(facts,'Cloud sync','Not configured');appendFact(facts,'Device',settings.address||'Not configured');
}
function appendFact(list,label,value){const row=el('div');row.append(el('dt','',label),el('dd','',value));list.append(row);}
function renderWorkflowReadiness() {
  const status=state.transcription;if(!status)return;const model=status.models.find(item=>item.id===defaultModel()),speakerReady=!state.settings?.transcription?.diarize||status.speaker_labels,ready=status.installed&&model?.downloaded&&speakerReady;
  $('#workflow-readiness').textContent=!status.installed?'Install the local speech engine in Settings.':ready?'Ready. Choose one recording or queue the waiting library.':'Download your default model, or choose a model that is already ready.';
  if(!speakerReady)$('#workflow-readiness').textContent='Set up the speaker models in Settings, or turn off Identify speakers by default.';
  $('#workflow-model').textContent=`${modelLabel(defaultModel())} · ${state.settings?.transcription?.default_language||'Detect language'} · ${status.execution}${state.settings?.transcription?.diarize?' · Identify speakers':''} · ${ready?'Ready offline':'Setup needed'}`;
  $('#batch-transcribe').disabled=!ready;
}
function renderTranscriptionSettings() {
  const status=state.transcription;if(!status)return;
  const speaker=status.diarization||{},speakerJob=state.jobs.find(job=>job.kind==='speaker_model_download'&&['queued','running'].includes(job.status));
  $('#speaker-badge').textContent=status.speaker_labels?'Ready offline':!speaker.installed?'Engine not installed':speakerJob?statusLabel(speakerJob.status):'Download needed';
  $('#speaker-badge').className='badge '+(status.speaker_labels?'good':'warning');
  $('#speaker-engine-install').hidden=!!speaker.installed;$('#speaker-engine-command').textContent=speaker.install_command||'';
  $('#prepare-speakers').disabled=!status.installed||!speaker.installed||!!speaker.downloaded||!!speakerJob;
  $('#prepare-speakers').textContent=speaker.downloaded?'Speaker models are ready':speakerJob?'Download '+statusLabel(speakerJob.status).toLowerCase():'Download speaker models · 34 MB';
  $('#default-diarize').disabled=!status.speaker_labels&&!state.settings?.transcription?.diarize;
  const statusNode=$('#transcription-badge');statusNode.className='badge '+(status.installed?'good':'warning');statusNode.textContent=status.installed?'Engine installed':'Engine not installed';
  $('#transcription-info').textContent=status.installed?`Runs locally using ${status.execution}. No Ollama, LM Studio, API key or paid account is required. Download a model once, then transcribe offline.`:'The dashboard is installed, but its speech engine is missing. Install it in the same Python environment as this service using the command below.';
  $('#engine-install').hidden=status.installed;$('#engine-command').textContent=status.install_command||'';
  const models=status.models||[],select=$('#model-select'),previous=select.value;
  models.forEach(model=>{let option=[...select.options].find(item=>item.value===model.id);if(!option){option=el('option');option.value=model.id;select.append(option);}option.textContent=model.label+(model.downloaded?' · Ready':' · Download needed');});
  if(models.some(model=>model.id===previous))select.value=previous;
  const selected=models.find(model=>model.id===select.value),selectedJob=state.jobs.find(job=>job.kind==='model_download'&&job.model===select.value&&['queued','running'].includes(job.status));
  $('#prepare-model').disabled=!status.installed||!!selected?.downloaded||!!selectedJob;
  $('#prepare-model').textContent=selected?.downloaded?'Selected model is ready':selectedJob?'Download '+statusLabel(selectedJob.status).toLowerCase():'Download selected model';
  renderWorkflowReadiness();
  const list=$('#model-list'),stamp=JSON.stringify([status.installed,models,defaultModel(),state.jobs.filter(job=>job.kind==='model_download').map(job=>[job.model,job.status])]);
  if(list.dataset.stamp===stamp)return;list.dataset.stamp=stamp;
  const focusId=list.contains(document.activeElement)?document.activeElement.id:null;list.replaceChildren();
  models.forEach(model=>{
    const card=el('article','model-card'+(model.recommended?' recommended':'')),head=el('div','section-heading');head.append(el('h4','',model.label));if(model.recommended)head.append(badge('Recommended','good'));card.append(head,el('p','',model.description),el('p','field-help',`About ${modelSize(model)} download · ${model.id.endsWith('.en')?'English only':'Multilingual'} · CPU`));
    const active=state.jobs.find(job=>job.kind==='model_download'&&job.model===model.id&&['queued','running'].includes(job.status));
    const actions=el('div','button-row');actions.append(badge(model.downloaded?'Ready offline':active?statusLabel(active.status):'Not downloaded',model.downloaded?'good':active?'warning':'neutral'));
    if(model.downloaded){const use=button(defaultModel()===model.id?'Default model':'Use as default',()=>busy(use,async()=>{state.settings=await api('/v1/settings',{method:'PATCH',body:JSON.stringify({default_model:model.id,...(model.id.endsWith('.en')?{default_language:'en'}:{})})});renderSettings();renderTranscriptionSettings();toast('Default transcription model updated.');}));use.id='use-model-'+model.id;use.disabled=defaultModel()===model.id;actions.append(use);}
    else if(active)actions.append(button('View download',()=>setView('workflow')));
    else{const download=button('Download model',()=>downloadModel(model.id,download),'button secondary','download');download.id='download-model-'+model.id;download.disabled=!status.installed;actions.append(download);}
    card.append(actions);list.append(card);
  });
  if(focusId)document.getElementById(focusId)?.focus({preventScroll:true});
}
async function downloadModel(id,node) {
  const model=state.transcription?.models?.find(item=>item.id===id);
  if(!await confirmAction(`Download ${modelLabel(id)}?`,`About ${model?modelSize(model):'an unknown amount of'} disk space is needed. Model files come from Hugging Face. Your audio stays on this computer. Once downloaded, choose Use as default or select it on a recording.`,'Download model'))return;
  await busy(node,async()=>{await post('/v1/transcription/models/'+encodeURIComponent(id)+'/prepare');await refreshJobs();setView('workflow');toast('Model download queued. Progress appears below.');});renderTranscriptionSettings();
}
async function checkDevice() {
  return busyDevice($('#device-refresh'),async()=>{
    $('#connection-state').textContent='Checking…';
    try{
      const info=await api('/v1/device'),checked=timeText(info.checked_at||new Date());
      $('#connection-state').className='badge good';$('#connection-state').textContent='Seen at '+checked;
      $('#device-badge').className='badge good';$('#device-badge').replaceChildren(el('span','status-dot'),document.createTextNode('Device seen at '+checked));
      const facts=el('dl','facts-list'),telemetry=info.telemetry||{},power=telemetry.battery,storage=telemetry.storage,recording=telemetry.recording;
      const reported=value=>value==null?'Not reported':statusLabel(value);
      appendFact(facts,'Battery',info.battery_percent==null?'Not reported':info.battery_percent+'%');
      appendFact(facts,'Charging',reported(power?.state));appendFact(facts,'USB',reported(power?.usb));
      appendFact(facts,'Recording',reported(recording?.state));
      appendFact(facts,'Storage used',storage?.used_pages!=null?`${storage.used_pages.toLocaleString()} of ${storage.total_pages.toLocaleString()} pages`:'Not reported');
      appendFact(facts,'Firmware',info.firmware_ver||'Not reported');
      appendFact(facts,'Address',info.address||state.settings?.address||'Not reported');
      appendFact(facts,'Stored page range',info.oldest_flash_page!==undefined?info.oldest_flash_page+' → '+info.newest_flash_page:'Not reported');
      $('#device-facts').replaceChildren(facts);
      $('#recording-state').textContent=recording?`${reported(recording.state)} · checked at ${checked}`:'Not reported by the Pendant';
      if(info.status_warning)$('#device-facts').append(el('p','field-help',info.status_warning));
      const details=el('details','telemetry-details'),extra=el('dl','facts-list');
      details.append(el('summary','','More device details'));
      appendFact(extra,'Serial number',info.serial_num||'Not reported');
      appendFact(extra,'Wi-Fi',reported(telemetry.wifi?.state));
      if(telemetry.wifi?.rssi!=null)appendFact(extra,'Wi-Fi signal',telemetry.wifi.rssi+' dBm');
      if(recording)appendFact(extra,'Recording trigger',reported(recording.source));
      if(power){
        appendFact(extra,'Temperature alert',power.over_operating_temperature?'Above operating range':power.under_operating_temperature?'Below operating range':'No alert reported');
        ['voltage','current','temperature','capacity'].forEach(name=>appendFact(extra,statusLabel(name)+' (raw)',power[name+'_raw']));
      }
      details.append(extra,el('p','field-help','Raw power values have unverified units. Motion data is not decoded. Readings update when you check the device.'));
      $('#device-facts').append(details);
    }
    catch(error){$('#connection-state').className='badge error';$('#connection-state').textContent='Check failed';$('#device-badge').className='badge neutral';$('#device-badge').textContent='Device unavailable';$('#recording-state').textContent='Status unknown: device check failed';$('#device-facts').replaceChildren(el('p','muted','No current readings. Check the Pendant again when it is available.'));throw error;}
  });
}
async function scanDevice() {
  await busyDevice($('#device-scan'),async()=>{const list=$('#scan-results');list.replaceChildren(el('p','field-help','Looking for nearby Pendants…'));const result=await api('/v1/devices/scan?timeout=8');list.replaceChildren();if(!result.devices?.length){list.append(el('p','field-help','No Pendant found. Make sure it is nearby, awake and not connected to another app.'));return;}
    result.devices.forEach(device=>{const row=button('',()=>{$('#device-address').value=device.address;$('#device-address').focus();toast('Address selected. Choose Save device to use it.');},'scan-result');row.append(el('span','',(device.name||'Limitless Pendant')+(device.rssi==null?'':` · ${device.rssi} dBm`)),el('span','',device.address));list.append(row);});
  },'Scanning…');
}
async function loadCaptures() {
  const result=await api('/v1/captures');const list=$('#capture-list');list.replaceChildren();
  if(!result.captures?.length){list.append(el('div','table-empty','No transfers yet. Sync when your Pendant is nearby.'));return;}
  result.captures.forEach(capture=>{const row=el('div','table-row'),copy=el('div');copy.append(el('strong','',`Transfer · ${dateText(capture.started_at)} ${timeText(capture.started_at)}`));const summary=capture.capture;
    copy.append(el('p','',`${summary?.unique_pages_saved??0} pages saved · ${capture.acknowledge?'Deletion was enabled for this transfer':'Device audio kept'}${summary?.stop_reason?' · '+summary.stop_reason.replaceAll('_',' '):''}`));if(capture.error)copy.append(el('p','job-error',capture.error));
    const actions=el('div','button-row');actions.append(badge(statusLabel(capture.status),statusKind(capture.status)));
    if(capture.status!=='running'){const decode=button('Decode & add to library',()=>busy(decode,async()=>{const result=await post('/v1/captures/'+encodeURIComponent(capture.id)+'/decode');const summary=renderDecodeSummary(result);$('#sync-status').textContent=summary.text;await loadRecordings();await loadCaptures();toast(summary.toast,summary.hasWarnings||!summary.hasRecordings);}));actions.append(decode);}row.append(copy,actions);list.append(row);
  });
}
function renderDecodeSummary(result) {
  const available=Array.isArray(result.library_recordings)?result.library_recordings.length:0;
  const count=result.library_summary?.added??available,alreadySaved=result.library_summary?.already_present??0,extended=result.library_summary?.extended??0;
  const hasRecordings=count>0||alreadySaved>0;
  const labels={encrypted_chunks_without_key:'Encrypted chunks without a local key',decryption_failures:'Decryption failures',unsupported_packet_offsets:'Unsupported packet offsets',invalid_opus_packets:'Invalid Opus packets',flash_page_errors:'Flash page errors',malformed_messages:'Malformed messages',incomplete_journal_tail:'Incomplete journal tail',unverified_archive_record:'Unverified archive records',unverified_or_truncated_archive_tail:'Unverified or truncated archive tail'};
  const warnings=Object.entries(result.warnings||{}).filter(([,value])=>Number(value)>0).map(([name,value])=>`${labels[name]||name.replaceAll('_',' ')}: ${value}`);
  const empty=result.content?.audio_chunks===0?'No audio was present in the downloaded pages. 0 recordings added to the library.':'No playable audio recovered. 0 recordings added to the library.';
  const summary=hasRecordings?`${count} new recording${count===1?'':'s'} added.${extended?' '+extended+' existing recording'+(extended===1?'':'s')+' extended with more audio.':''}${alreadySaved>extended?' '+(alreadySaved-extended)+' already saved.':''}`:empty;
  const text=summary+' Raw transfer preserved.'+(warnings.length?' Decode warnings: '+warnings.join('; ')+'.':'');
  alertMessage(warnings.length||!hasRecordings?text:'');
  return {text,count,hasRecordings,hasWarnings:warnings.length>0,toast:hasRecordings?summary+(warnings.length?' Check the decode warnings.':''):'No playable audio recovered. Raw transfer preserved.'};
}
async function syncDevice() {
  await busyDevice($('#sync-button'),async()=>{
    const select=$('#capture-duration'),seconds=Number(select.value),progress=$('#sync-progress'),started=performance.now();
    const wasDisabled=select.disabled;select.disabled=true;state.syncing=true;alertMessage('');progress.hidden=false;
    const updateElapsed=()=>{progress.textContent=`Elapsed ${duration((performance.now()-started)/1000)} · Transfer limit ${syncTimeLabel(seconds)}. Keep this page open and your Mac awake.`;};
    updateElapsed();let timer=setInterval(updateElapsed,1000);
    const status=$('#sync-status');status.textContent='Connecting and downloading stored pages, including older diagnostics. This can take several minutes. A transient connection failure is retried once. Original audio stays on the device…';
    try{const capture=await post('/v1/captures',{acknowledge:false,idle_timeout:5,max_seconds:seconds});clearInterval(timer);timer=null;progress.textContent=`Transfer phase finished after ${duration((performance.now()-started)/1000)}.`;status.textContent='Transfer finished. Decoding saved audio and adding it to your library…';
      try{const result=await post('/v1/captures/'+encodeURIComponent(capture.id)+'/decode');const summary=renderDecodeSummary(result);const limited=capture.capture?.stop_reason==='time_limit';const next=[...select.options].find(option=>Number(option.value)>seconds);const limitNote=limited?`Reached the transfer limit of ${syncTimeLabel(seconds)}. Newer recordings may still be missing. ${next?'Try setting the limit to '+next.textContent+'.':'This is the longest available limit.'} `:'';status.textContent=`${limitNote}${capture.capture?.unique_pages_saved??0} pages saved. ${summary.text} ${capture.capture?.complete||limited?'':'This transfer does not confirm that every stored recording has been downloaded.'}`;if(limited)alertMessage(status.textContent);toast(limited?'Partial transfer saved. '+summary.toast:summary.toast,limited||summary.hasWarnings||!summary.hasRecordings);}
      catch(error){status.textContent='Raw audio was saved, but decoding needs attention: '+error.message;toast('Transfer saved. Decoding needs attention.',true);}
      await loadRecordings();await loadCaptures();await refreshJobs();
    }catch(error){status.textContent='Sync could not finish: '+error.message;await loadCaptures().catch(()=>{});throw error;}
    finally{if(timer!==null){clearInterval(timer);progress.textContent=`Sync ended after ${duration((performance.now()-started)/1000)}.`;}select.disabled=wasDisabled;state.syncing=false;}
  },'Syncing…');
}

hydrateIcons();
initPendantAppearance();
initSyncPreference();
$('#login-form').addEventListener('submit',event=>{event.preventDefault();busy($('#login-button'),()=>login($('#api-token').value),'Opening…');});
$$('[data-view]').forEach(node=>node.addEventListener('click',()=>setView(node.dataset.view)));
$$('[data-action]').forEach(node=>node.addEventListener('click',()=>node.dataset.action==='import'?$('#audio-import').click():setView(node.dataset.action)));
$('#lock-button').addEventListener('click',lockWorkspace);$('#settings-lock').addEventListener('click',lockWorkspace);
$('#refresh-button').addEventListener('click',refreshWorkspace);
$('#import-button').addEventListener('click',()=>$('#audio-import').click());$('#audio-import').addEventListener('change',event=>importFiles([...event.target.files]));
let searchTimer;$('#recording-search').addEventListener('input',event=>{state.query=event.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadRecordings().catch(error=>toast(error.message,true)),220);});
$$('[data-filter]').forEach(node=>node.addEventListener('click',()=>{state.filter=node.dataset.filter;updateFilters();loadRecordings().catch(error=>toast(error.message,true));}));
$('#device-refresh').addEventListener('click',checkDevice);$('#device-scan').addEventListener('click',scanDevice);
$('#device-config-form').addEventListener('submit',event=>{event.preventDefault();busy($('button',event.target),async()=>{const result=await api('/v1/device/config',{method:'PUT',body:JSON.stringify({address:$('#device-address').value.trim()})});state.settings.address=result.address;$('#device-badge').className='badge neutral';$('#device-badge').textContent='Device not checked';$('#connection-state').className='badge neutral';$('#connection-state').textContent='Not checked';$('#device-facts').replaceChildren(el('p','muted','Device saved. Check it to read the current status.'));toast('Device saved. You can now check it over Bluetooth.');});});
[['#start-recording',true],['#stop-recording',false]].forEach(([selector,enabled])=>$(selector).addEventListener('click',()=>busyDevice($(selector),async()=>{
  alertMessage('');
  $('#recording-state').textContent=enabled?'Synchronising clock, then checking recording state…':'Stopping and checking device state…';
  try{
    const result=await post('/v1/device/recording',{enabled}),observed=result.recording?.state;
    const stateLabel=observed==='listening'?'Listening for speech':observed?statusLabel(observed):'State unavailable';
    $('#recording-state').textContent=stateLabel+(result.device_execution_verified?' · confirmed by Pendant':'. Requested state was not confirmed.');
    $$('#device-facts dt').filter(dt=>dt.textContent==='Recording').forEach(dt=>{dt.nextElementSibling.textContent=stateLabel;});
    const warning=result.device_execution_verified?'':result.warning||'The requested recording state was not confirmed. Check the Pendant before continuing.';
    const message=warning||(observed==='listening'?'Pendant is listening for speech. Play back the next sync to verify audio capture.':stateLabel+' · confirmed by Pendant.');
    toast(message,!result.device_execution_verified);alertMessage(warning);
  }catch(error){$('#recording-state').textContent='Device control failed. '+error.message;alertMessage(error.message);throw error;}
},enabled?'Starting…':'Stopping…')));
$('#set-clock').addEventListener('click',()=>busyDevice($('#set-clock'),async()=>{const result=await post('/v1/device/clock');toast(result.device_execution_verified?'Clock synchronisation acknowledged by Pendant.':'Clock command sent; acknowledgement unavailable.',!result.device_execution_verified);}));
$('#provision-key').addEventListener('click',async()=>{if(await confirmAction('Set up your personal key?','This saves a private key locally and sends its public key to the Pendant for future recordings. It cannot decrypt existing audio recorded with a different key. Back up your data directory after setup.','Set up local key'))busy($('#provision-key'),async()=>{await post('/v1/device/key',{confirm_future_recordings:true});toast('Local key saved and command sent. Device execution is not verified.');});});
$('#sync-button').addEventListener('click',syncDevice);$('#captures-refresh').addEventListener('click',()=>busy($('#captures-refresh'),loadCaptures));
$('#jobs-refresh').addEventListener('click',()=>busy($('#jobs-refresh'),refreshJobs));
$('#preferences-form').addEventListener('submit',event=>{event.preventDefault();busy($('button[type="submit"]',event.target),async()=>{state.settings=await api('/v1/settings',{method:'PATCH',body:JSON.stringify({default_model:$('#model-select').value,default_language:$('#language-select').value||null,auto_transcribe:$('#auto-transcribe')?.checked||false,diarize:$('#default-diarize').checked})});renderSettings();renderTranscriptionSettings();toast('Transcription preferences saved.');});});
$('#prepare-speakers').addEventListener('click',async()=>{if(!await confirmAction('Download local speaker models?','Downloads about 34 MB from the sherpa-onnx project on GitHub. Your audio stays here. No account or paid service is required.','Download models'))return;await busy($('#prepare-speakers'),async()=>{await post('/v1/transcription/diarization/prepare');await refreshJobs();setView('workflow');toast('Speaker model download queued.');});});
$('#copy-speaker-command').addEventListener('click',()=>busy($('#copy-speaker-command'),async()=>{await navigator.clipboard.writeText($('#speaker-engine-command').textContent);toast('Installation command copied.');}));
$('#prepare-model').addEventListener('click',()=>downloadModel($('#model-select').value,$('#prepare-model')));
$('#model-select').addEventListener('change',()=>{if($('#model-select').value.endsWith('.en'))$('#language-select').value='en';renderTranscriptionSettings();});
$('#batch-transcribe').addEventListener('click',queueUntranscribed);
$('#copy-engine-command').addEventListener('click',()=>busy($('#copy-engine-command'),async()=>{await navigator.clipboard.writeText($('#engine-command').textContent);toast('Installation command copied.');}));
document.addEventListener('keydown',event=>{if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!document.activeElement?.matches('input,textarea,select')&&!$('#workspace').hidden&&!$('#confirm-dialog').open){event.preventDefault();setView('recordings');backToLibrary();$('#recording-search').focus();}});
window.addEventListener('hashchange',()=>{if(!$('#workspace').hidden)setView(location.hash.slice(1));});
window.addEventListener('beforeunload',event=>{if(state.dirtyNotes.size||state.syncing){event.preventDefault();event.returnValue='';}});
setInterval(async()=>{if(!state.token||state.polling||document.hidden)return;state.polling=true;try{await refreshJobs();if(state.jobs.some(job=>['queued','running'].includes(job.status)))await loadRecordings();}catch{}finally{state.polling=false;}},5000);
try{const token=sessionStorage.getItem('pendant_token');if(token)login(token);}catch{}
