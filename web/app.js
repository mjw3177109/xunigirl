const $ = id => document.getElementById(id);
const V = '/voice';
const state = {session:null,controller:null,turn:null,recording:false,stream:null,audioCtx:null,audioNode:null,audioSource:null,raw:[],inputHz:48000,lastSpeech:0,startedAt:0,recordTimer:null,volume:0,ttsQueue:[],ttsBusy:false,ttsEpoch:0,ttsAbort:null,audio:null,dhCode:null,dhTimer:null,dhFinished:false,dhPlaying:false,idleList:[],videoMode:false,videoQueue:[],audioDone:null,recordPrefill:[],vad:null,vadBusy:false,liveVadSupported:false,qqSocket:null,qqQueue:[],qqWorking:false};
const showNotice = (message) => { $('notice').hidden = !message; $('notice').textContent = message || ''; };
const setStatus=(id, good,text)=>{ $(id+'Lamp').className='lamp '+(good?'ok':'fail'); $(id+'Label').textContent=text; };
async function api(path, opts={}) {
 const r=await fetch(path,opts);if(!r.ok){let detail='';try{const j=await r.json();detail=typeof j.detail==='string'?j.detail:JSON.stringify(j.detail)}catch{}throw new Error(`${r.status} ${detail}`)};
 return r.json();
}
const jsonOpts = body => ({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function bubble(role,txt='') { const empty=$('messages').querySelector('.welcome');if(empty)empty.remove();const el=document.createElement('div');el.className='bubble '+role;const title=document.createElement('div');title.className='who';title.textContent=role==='user'?'你':'小雅';const content=document.createElement('div');content.className='body';content.textContent=txt;el.append(title,content);$('messages').append(el); scrollBottom();return content; }
function scrollBottom(){const el=$('messages');el.scrollTop=el.scrollHeight;}
async function sessionRefresh() {const r=await api('/api/app/sessions');const wrap=$('sessions');wrap.replaceChildren();r.sessions.forEach(s=>{const row=document.createElement('div');row.className='session '+(s.id===state.session?'active':'');const title=document.createElement('span');title.textContent=s.title;row.appendChild(title);row.onclick=()=>openSession(s.id);const x=document.createElement('button');x.textContent='×';x.title='删除该对话';x.onclick=async event=>{event.stopPropagation();if(!confirm('删除此对话和历史？'))return;await api('/api/app/sessions/'+s.id,{method:'DELETE'});if(s.id===state.session)await newSession();else await sessionRefresh()};row.appendChild(x);wrap.appendChild(row)});}
async function newSession(){await stopAll();const r=await api('/api/app/sessions',{method:'POST'});state.session=r.id; $('messages').innerHTML='<div class="welcome"><div class="welcomeOrb">✦</div><h2>你好呀，今天想聊什么？</h2><p>我可以用文字和你聊天，也可以听你说话、读出回复。</p></div>';await sessionRefresh();}
async function openSession(id){await stopAll();state.session=id;const r=await api('/api/app/sessions/'+id);$('messages').replaceChildren();for(const m of r.messages)bubble(m.role,m.content);await sessionRefresh();}
function buttonsBusy(busy){$('send').disabled=busy;$('stop').disabled=!busy;}
async function stopAll(){state.controller?.abort();state.controller=null;if(state.session)fetch('/api/app/cancel',jsonOpts({session_id:state.session})).catch(()=>{});buttonsBusy(false);stopTts();if(state.dhCode){fetch(V+'/api/dh/discard',jsonOpts({code:state.dhCode})).catch(()=>{});state.dhCode=null;} if(state.dhTimer)clearInterval(state.dhTimer);state.dhTimer=null;state.videoQueue=[];state.dhFinished=false;stopVideo();}
function stopVideo(){state.dhPlaying=false;const v=$('avatarVideo');v.onended=null;v.pause();v.removeAttribute('src');v.load();v.style.display='none';$('avatarPlaceholder').style.display='flex';$('videoState').textContent='待机';}
function stopTts(){state.ttsEpoch++;state.ttsQueue.length=0;state.ttsAbort?.abort();state.audio?.pause();state.audioDone?.();state.audioDone=null;state.audio?.removeAttribute('src');state.audio=null;state.ttsBusy=false;}
function speechSafe(sentence){return sentence.replace(/<think>[\s\S]*?<\/think>/gi,'')
 .replace(/```[\s\S]*?```/g,'').replace(/!\[([^\]]*)\]\([^)]+\)/g,'$1')
 .replace(/\[([^\]]+)\]\(https?:\/\/[^)]*\)/g,'$1')
 .replace(/https?:\/\/\S+/g,'一个链接').replace(/[*_`#>]/g,'').trim();}
function queueTts(sentence){const safe=speechSafe(sentence);if(!$('speak').checked||!safe)return;state.ttsQueue.push(safe);void drainTts();}
async function drainTts(){if(state.ttsBusy)return;state.ttsBusy=true;const epoch=state.ttsEpoch;try{while(state.ttsQueue.length&&epoch===state.ttsEpoch){const txt=state.ttsQueue.shift();state.ttsAbort=new AbortController();let res;try{res=await fetch(V+'/api/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt}),signal:state.ttsAbort.signal});if(!res.ok)throw Error('TTS HTTP '+res.status);const wav=await res.blob();if(epoch!==state.ttsEpoch)break;const url=URL.createObjectURL(wav);const a=new Audio(url);state.audio=a;a.onplay=()=>{void startBarge()};try {await new Promise((resolve,reject)=>{state.audioDone=resolve;a.onended=resolve;a.onerror=()=>reject(Error('音频播放失败'));a.play().catch(reject)})}finally{URL.revokeObjectURL(url);if(state.audio===a)state.audioDone=null;}}catch(e){if(epoch===state.ttsEpoch&&e.name!=='AbortError')showNotice('语音朗读失败：'+e.message+'。检查声音参考音频和本地 TTS 模型。');break;}}}finally{if(epoch===state.ttsEpoch){state.ttsBusy=false;state.ttsAbort=null;}}}
function consumeSentences(buffer,flush=false){let idx=0,last=0;const sentences=[];for(let i=0;i<buffer.length;i++){if('。！？!?；;\n'.includes(buffer[i]) || (buffer[i]==='，' && i-last>26)){const sentence=buffer.slice(last,i+1).trim();if(sentence)sentences.push(sentence);last=i+1;}}if(flush&&buffer.slice(last).trim()){sentences.push(buffer.slice(last).trim());return {sentences,rest:''}}return {sentences,rest:buffer.slice(last)}}
async function sendMessage(text){text=text.trim();if(!text||!state.session||state.controller)return;
 if(state.dhTimer)clearInterval(state.dhTimer);state.dhTimer=null;
 if(state.dhCode){fetch(V+'/api/dh/discard',jsonOpts({code:state.dhCode})).catch(()=>{});state.dhCode=null;}
 state.videoQueue=[];state.dhFinished=false;stopVideo();stopTts();showNotice('');bubble('user',text);const target=bubble('assistant','');$('text').value='';state.controller=new AbortController();const current=state.controller;buttonsBusy(true);let whole='',ttsBuffer='',done=false;
try{let r;for(let attempt=0;attempt<10;attempt++){
  r=await fetch('/api/app/chat/stream',{...jsonOpts({session_id:state.session,message:text,model:$('model').value,system_prompt:$('persona').value}),signal:current.signal});
  if(r.status!==409)break;
  await new Promise(resolve=>setTimeout(resolve,250));
}if(!r.ok){let d=await r.text();throw Error(`聊天接口 ${r.status}: ${d.slice(0,250)}`)}const reader=r.body.getReader(),decoder=new TextDecoder();let partial='';while(true){const {value,done:ended}=await reader.read();if(ended)break;partial+=decoder.decode(value,{stream:true});let pos;while((pos=partial.indexOf('\n\n'))>=0){const block=partial.slice(0,pos);partial=partial.slice(pos+2);if(!block.startsWith('data:'))continue;let item;try{item=JSON.parse(block.slice(5).trim())}catch{continue}
 if(item.event==='delta'){whole+=item.text;target.textContent=whole;scrollBottom();if(!$('digital').checked){ttsBuffer+=item.text;const split=consumeSentences(ttsBuffer);ttsBuffer=split.rest;split.sentences.forEach(queueTts)}}
 if(item.event==='error')throw Error(item.message);
 if(item.event==='done'){done=true;if(!$('digital').checked){consumeSentences(ttsBuffer,true).sentences.forEach(queueTts)}else if($('speak').checked&&whole.trim()){await runDh(whole)} }
 if(item.event==='cancelled')return;
 }}if(!done&&!current.signal.aborted)throw Error('服务端中断，回复未完整保存。');}catch(e){if(e.name!=='AbortError'){showNotice('请求失败：'+e.message);if(!whole)target.textContent='（回复失败）'}}finally{if(state.controller===current){state.controller=null;buttonsBusy(false)}await sessionRefresh().catch(()=>{});}return done?whole:null;}
// A segmented DUIX reply may spend time rendering the next segment after the
// previous video has finished. Keep the task ID and keep polling until the
// bridge reports "done" AND every segment has actually finished playing.
function finishDh(){
 if(state.dhTimer){clearInterval(state.dhTimer);state.dhTimer=null;}
 state.dhCode=null;state.dhFinished=false;state.dhPlaying=false;
 $('videoState').textContent='播放完毕';void idleMedia();
}
async function runDh(text){
 try{
  const r=await api(V+'/api/dh/speak',jsonOpts({text}));
  if(!r.code)throw Error('DUIX 未返回任务编号');
  state.dhCode=r.code;state.videoQueue=[];state.dhFinished=false;state.dhPlaying=false;
  stopVideo();$('videoState').textContent='正在生成数字人首段视频…';
  const played=new Set();if(state.dhTimer)clearInterval(state.dhTimer);
  const poll=async()=>{
   if(!state.dhCode)return;
   try{
    const x=await api(V+'/api/dh/status');
    if(x.code!==state.dhCode)return;
    $('videoState').textContent=x.message||x.state;
    for(const segment of (x.videos||[])){
     const url=V+segment.video_url;
     if(!played.has(url)){played.add(url);state.videoQueue.push(url);}
    }
    if(!state.dhPlaying&&state.videoQueue.length)playDhNext();
    if(x.state==='error'||x.state==='discarded'){
     if(state.dhTimer)clearInterval(state.dhTimer);
     state.dhTimer=null;state.dhCode=null;state.dhFinished=false;
     state.videoQueue=[];stopVideo();
     if(x.state==='error'){
      showNotice('数字人失败，尝试普通语音朗读：'+x.message);
      if($('speak').checked)consumeSentences(text,true).sentences.forEach(queueTts);
     }
     return;
    }
    if(x.state==='done')state.dhFinished=true;
    if(state.dhFinished&&!state.dhPlaying&&!state.videoQueue.length)finishDh();
   }catch(e){console.warn('[DUIX] status poll failed:',e);}
  };
  state.dhTimer=setInterval(()=>void poll(),1600);
  await poll();
 }catch(e){
  showNotice('数字人提交失败，已尝试普通语音：'+e.message);
  if($('speak').checked)consumeSentences(text,true).sentences.forEach(queueTts);
 }
}
function playDhNext(){
 if(!state.videoQueue.length){
  state.dhPlaying=false;
  if(state.dhFinished)finishDh();
  else $('videoState').textContent='等待下一段数字人视频…';
  return;
 }
 const v=$('avatarVideo');state.dhPlaying=true;
 $('avatarPlaceholder').style.display='none';v.style.display='block';
 v.muted=false;v.loop=false;v.src=state.videoQueue.shift();
 v.onended=()=>{state.dhPlaying=false;playDhNext();};
 v.play().then(()=>{void startBarge()}).catch(e=>{
  state.dhPlaying=false;showNotice('浏览器阻止视频播放：'+e.message+'；请点击页面后重试。');
 });
}
function resampleToPcm16(buffers,rate){const size=buffers.reduce((a,b)=>a+b.length,0);const input=new Float32Array(size);let pos=0;for(const block of buffers){input.set(block,pos);pos+=block.length;}const ratio=rate/16000;const count=Math.floor(input.length/ratio);const out=new Int16Array(count);for(let j=0;j<count;j++){const start=Math.floor(j*ratio),end=Math.min(input.length,Math.floor((j+1)*ratio));let sum=0;for(let k=start;k<end;k++)sum+=input[k];const v=Math.max(-1,Math.min(1,sum/Math.max(1,end-start)));out[j]=v<0?v*32768:v*32767;}return out.buffer;}
async function recordToggle(){if(state.recording){await finishRecord();return;}await startRecord();}
async function startRecord(prefill=[]){try{await stopBarge();await stopAll();state.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,channelCount:1},video:false});const context=new AudioContext();state.audioCtx=context;await context.audioWorklet.addModule('/static/worklet.js');const source=context.createMediaStreamSource(state.stream);state.audioSource=source;const node=new AudioWorkletNode(context,'voice-worklet');state.audioNode=node;const mute=context.createGain();mute.gain.value=0;source.connect(node);node.connect(mute);mute.connect(context.destination);
 state.inputHz=context.sampleRate;state.raw=[...prefill];state.recording=true;state.startedAt=Date.now();state.lastSpeech=Date.now();$('mic').textContent='■ 结束';$('recordStatus').textContent='正在录音，停顿 1.8 秒自动发送';node.port.onmessage=e=>{if(!state.recording)return;const d=e.data;state.raw.push(d);const amp=Math.sqrt(d.reduce((s,x)=>s+x*x,0)/d.length);state.volume=amp;if(amp>.018)state.lastSpeech=Date.now();};state.recordTimer=setInterval(()=>{if(!state.recording)return;const ms=Date.now()-state.startedAt;if(ms>26000||(ms>1600&&state.raw.length>30&&Date.now()-state.lastSpeech>1800))void finishRecord();},250);}catch(e){showNotice('录音不可用：'+e.message);await cleanupMic();}}
async function cleanupMic(){clearInterval(state.recordTimer);state.recordTimer=null;state.recording=false;$('mic').textContent='🎙️ 说话';$('recordStatus').textContent='可切换语音输入';state.audioNode?.disconnect();state.audioSource?.disconnect();state.stream?.getTracks().forEach(t=>t.stop());await state.audioCtx?.close().catch(()=>{});state.stream=null;state.audioCtx=null;state.audioNode=null;state.audioSource=null;}
async function finishRecord(){if(!state.recording)return;const chunks=state.raw,rate=state.inputHz;await cleanupMic();if(!chunks.length)return;$('recordStatus').textContent='正在识别语音…';try{const pcm=resampleToPcm16(chunks,rate);const res=await fetch(V+'/api/stt',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Max-Audio-Sec':'30'},body:pcm});if(!res.ok)throw Error('STT '+res.status+': '+(await res.text()).slice(0,180));const j=await res.json();if(j.text?.trim())await sendMessage(j.text);else showNotice('未识别到清晰语音，请重试。');}catch(e){showNotice('语音识别失败：'+e.message+'。检查本地 FunASR 模型。')}finally{$('recordStatus').textContent='可切换语音输入';}}
async function personas(){try{const r=await api(V+'/api/persona/list');const voice=$('voices');voice.replaceChildren();if(!r.voices?.length){voice.add(new Option('请添加参考音频',''));$('speak').checked=false;}else for(const x of r.voices)voice.add(new Option(x.label,x.name));voice.value=r.current.voice||'';const idle=$('idle');idle.replaceChildren();for(const x of r.idles||[])idle.add(new Option(x.label,x.name));if(r.current.idle)idle.value=r.current.idle;const avatars=$('avatars');avatars.replaceChildren();for(const x of r.avatars||[])avatars.add(new Option(x.label,x.name));if(r.current.avatar)avatars.value=r.current.avatar;}catch{$('voices').innerHTML='<option>语音服务未就绪</option>';}}
async function idleMedia(){try{const r=await api(V+'/api/media/bg-images');state.idleList=r.media||[];if(state.idleList.length&&!state.dhCode){const media=state.idleList[0];const v=$('avatarVideo');const u=V+'/media/bg-images/'+encodeURIComponent(media.name);if(media.type==='video'){v.src=u;v.loop=true;v.muted=true;v.style.display='block';$('avatarPlaceholder').style.display='none';v.play().catch(()=>{});}else{v.style.display='none';$('avatarPlaceholder').style.display='flex';$('avatarPlaceholder').style.backgroundImage=`url(${JSON.stringify(u)})`;}}}catch{}}

// Optional hands-free barge-in. Must be enabled explicitly; headphones are recommended.
// Silero VAD receives 16 kHz PCM16 while AI audio/video is playing. A 1.6-second
// local microphone pre-roll is carried into the new recording, so the first
// syllable is not lost when the VAD detects speech after its confirmation delay.
function aiAudioPlaying(){
  const a=state.audio,v=$('avatarVideo');
  return !!((a&&!a.paused&&!a.ended)||(v&&!v.paused&&!v.muted&&!v.ended));
}
async function stopBarge(){
  const v=state.vad;state.vad=null;
  if(!v)return;
  v.active=false;
  try{v.ws?.close()}catch{}
  try{v.node?.disconnect();v.source?.disconnect()}catch{}
  v.stream?.getTracks().forEach(t=>t.stop());
  try{await v.ctx?.close()}catch{}
}
async function startBarge(){
  if(!state.liveVadSupported||!$('autoBarge').checked||state.vad||state.vadBusy||state.recording)return;
  state.vadBusy=true;
  let stream=null,ctx=null,node=null,source=null,ws=null;
  try{
    stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,channelCount:1},video:false});
    ctx=new AudioContext();await ctx.audioWorklet.addModule('/static/worklet.js');
    source=ctx.createMediaStreamSource(stream);node=new AudioWorkletNode(ctx,'voice-worklet');
    const muted=ctx.createGain();muted.gain.value=0;source.connect(node);node.connect(muted);muted.connect(ctx.destination);
    const proto=location.protocol==='https:'?'wss':'ws';ws=new WebSocket(`${proto}://${location.host}${V}/api/vad`);
    const v={stream,ctx,node,source,ws,active:true,raw:[],samples:[],triggered:false,rate:ctx.sampleRate};state.vad=v;
    node.port.onmessage=e=>{
      if(state.vad!==v||!v.active||!aiAudioPlaying()||state.recording)return;
      const block=e.data;v.raw.push(block);
      const maxChunks=Math.ceil(1.6*v.rate/128);
      if(v.raw.length>maxChunks)v.raw.shift();
      const sample=resampleToPcm16([block],v.rate);
      v.samples.push(...new Int16Array(sample));
      while(v.samples.length>=512){
        const chunk=v.samples.splice(0,512);
        if(v.ws.readyState===WebSocket.OPEN)v.ws.send(new Int16Array(chunk).buffer);
      }
    };
    ws.onmessage=e=>{
      if(state.vad!==v||v.triggered)return;
      let item;try{item=JSON.parse(e.data)}catch{return}
      if(item.event==='speech_start'&&aiAudioPlaying()){
        v.triggered=true;const preRoll=v.raw.slice();
        $('recordStatus').textContent='检测到插话，正在听你说…';
        void (async()=>{await stopBarge();await startRecord(preRoll);})().catch(e=>showNotice('插话检测失败：'+e.message));
      }
    };
    ws.onerror=()=>{if(state.vad===v){showNotice('Silero VAD 未连接，请检查模型；可关闭免按键插话。')}};
  }catch(e){
    showNotice('免按键插话初始化失败：'+e.message);
    $('autoBarge').checked=false;
    try{ws?.close()}catch{};try{node?.disconnect();source?.disconnect()}catch{}
    stream?.getTracks().forEach(t=>t.stop());try{await ctx?.close()}catch{}
    state.vad=null;
  }finally{state.vadBusy=false;}
}

// Browser-side replacement for DSH's QQ plugin. The original Python bridge
// remains responsible for talking to NapCat/OneBot; only one configured QQ ID
// is accepted by the server-side allowlist patch.
function qqConnect(){
  if(!$('qq').checked||state.qqSocket)return;
  const proto=location.protocol==='https:'?'wss':'ws';
  const ws=new WebSocket(`${proto}://${location.host}${V}/api/qq/ws`);
  state.qqSocket=ws;
  ws.onopen=()=>{showNotice('QQ 桥接已连接。请确认 NapCat 已按 README 设置并启用白名单。')};
  ws.onmessage=e=>{
    let data;try{data=JSON.parse(e.data)}catch{return}
    if(data.type==='qq_message'&&data.text){state.qqQueue.push(data.text);void qqDrain()}
    if(data.type==='sent'&&!data.ok)showNotice('QQ 回传失败：'+(data.detail||'配置问题'));
  };
  ws.onerror=()=>showNotice('QQ 桥接连接异常，检查 NapCat 与桥接配置。');
  ws.onclose=()=>{if(state.qqSocket===ws){state.qqSocket=null;if($('qq').checked)showNotice('QQ 已断开，可关闭再打开开关重新连接。')}};
}
async function qqDrain(){
  if(state.qqWorking)return;state.qqWorking=true;
  try{
    while(state.qqQueue.length&&$('qq').checked){
      const message=state.qqQueue.shift();
      // Do not steal a running local turn or discard an incoming QQ message.
      let tries=0;
      while(state.controller&&tries<180){await new Promise(r=>setTimeout(r,500));tries++}
      if(state.controller){showNotice('QQ 消息等待超时，已跳过本条。');continue}
      const response=await sendMessage(message);
      const ws=state.qqSocket;
      if(response&&ws?.readyState===WebSocket.OPEN)
        ws.send(JSON.stringify({type:'reply',text:response}));
    }
  }finally{state.qqWorking=false}
}
async function memoriesRefresh(){
  try{const result=await api('/api/app/memories');const list=$('memories');list.replaceChildren();
    for(const item of result.memories){const row=document.createElement('div');row.className='memoryItem';
      const span=document.createElement('span');span.textContent=item.content;
      const del=document.createElement('button');del.type='button';del.title='删除此记忆';del.textContent='×';
      del.onclick=async()=>{await api('/api/app/memories/'+item.id,{method:'DELETE'});await memoriesRefresh()};
      row.append(span,del);list.appendChild(row);}
  }catch(e){showNotice('记忆加载失败：'+e.message)}
}
async function addMemory(){const inp=$('memoryInput');if(!inp.value.trim())return;
  try{await api('/api/app/memories',jsonOpts({content:inp.value.trim()}));inp.value='';await memoriesRefresh();}
  catch(e){showNotice('保存记忆失败：'+e.message)}
}
function hook(){ $('composer').addEventListener('submit',e=>{e.preventDefault();void sendMessage($('text').value)});$('text').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();void sendMessage($('text').value)}});$('stop').onclick=()=>void stopAll();$('mic').onclick=()=>void recordToggle();$('newChat').onclick=()=>void newSession();$('clear').onclick=async()=>{if(confirm('删除当前会话和历史？')){await api('/api/app/sessions/'+state.session,{method:'DELETE'});await newSession();}};
 $('voices').onchange=async()=>{try{await api(V+'/api/persona/set',jsonOpts({voice:$('voices').value}));showNotice('音色已切换');}catch(e){showNotice('音色切换失败：'+e.message)}};
 $('avatars').onchange=async()=>{try{await api(V+'/api/persona/set',jsonOpts({avatar:$('avatars').value}));showNotice('数字人形象已切换');}catch(e){showNotice('形象切换失败：'+e.message)}};
 $('idle').onchange=async()=>{try{await api(V+'/api/persona/set',jsonOpts({idle:$('idle').value}));await idleMedia()}catch(e){showNotice(e.message)}};
 $('digital').onchange=async()=>{try{const x=await api(V+'/api/dh/enable',jsonOpts({enabled:$('digital').checked}));showNotice(x.enabled?'数字人已启用（启动容器可能需要额外等待）':'数字人已关闭');}catch(e){$('digital').checked=false;showNotice('数字人开关失败：'+e.message)}};
 $('speak').onchange=()=>{if(!$('speak').checked)stopTts()};$('qq').onchange=()=>{if($('qq').checked)qqConnect();else{state.qqQueue=[];state.qqSocket?.close();state.qqSocket=null}};$('autoBarge').onchange=async()=>{if($('autoBarge').checked)await startBarge();else await stopBarge()};$('addMemory').onclick=()=>void addMemory();}
async function init(){hook();try{const r=await api('/api/app/status');setStatus('api',r.api_configured,'DeepSeek '+(r.api_configured?'已配置':'未配置 API Key'));setStatus('voice',r.voice_loaded,r.voice_loaded?'语音桥接已装载':'语音未安装');if(r.voice_error)console.warn(r.voice_error);state.liveVadSupported=!!r.voice_loaded;if(!r.voice_loaded){$('speak').checked=false;$('mic').disabled=true;$('digital').disabled=true;$('autoBarge').disabled=true;$('qq').disabled=true;}if(['deepseek-flash','deepseek-v4-pro'].includes(r.model_default))$('model').value=r.model_default;}catch(e){showNotice('独立后端连接失败：'+e.message)}
 const g=await api('/api/app/gpu').catch(()=>({available:false}));$('gpuLabel').textContent=g.available?`${g.name} · ${g.used_mb} / ${g.total_mb} MB`:'GPU 未检测到（纯文字功能不受影响）';let sessions=await api('/api/app/sessions');if(sessions.sessions?.length)await openSession(sessions.sessions[0].id);else await newSession();await personas();await idleMedia();await memoriesRefresh();try{const dh=await api(V+'/api/dh/status');$('digital').checked=!!dh.enabled;}catch{$('digital').checked=false;} }
void init();
