"""منسّق الصوت «متكلم واحد فقط في كل لحظة» — يعمل داخل صفحة المتصفح الأم فلا يتأثر بإعادة رسم Streamlit.

وظيفة هذا الملف: كائن واحد في المتصفح (window.__floor) يوزّع «الكلمة» بين أربعة أطراف:
  • المساعد (كل ردٍّ صوتي أو ترحيب أو زر 🔊 أو أي عنصر <audio> في الصفحة)  ← يُسكت الجميع ويكمل كلامه.
  • الشخصيتان بن عبد وسعيدان                                              ← لا تتكلمان أثناء أي صوت آخر.
  • تسجيل الميكروفون                                                      ← يُسكت الجميع طوال التسجيل.
  • الكتابة في أي خانة                                                    ← تُسكت الشخصيتين وتمنعهما من البدء.
بعد انتهاء المساعد أو التسجيل تبقى الشخصيتان صامتتين نحو 20 ثانية (فترة هدوء) حتى لا تقاطعا أحداً.

التشغيل الفعلي للصوت يتم هنا في الصفحة الأم (لا داخل iframe) فلا ينقطع الصوت إن أعاد Streamlit رسم المكوّن.
exports.play_audio و characters._ENGINE يعتمدان على هذا الملف؛ كلاهما يزرع الكود تلقائياً إن لم يكن موجوداً.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

FLOOR_VER = "1"

FLOOR_JS = r"""(function(){
var P=window;
if(P.__floor&&P.__floor.ver==='__FV__')return;
try{if(P.__floor&&P.__floor.destroy)P.__floor.destroy();}catch(e){}
var D=P.document,N=function(){return Date.now();};
var F=P.__floor={ver:'__FV__',h:null,quietUntil:0,typingAt:0,focusAt:0,recs:[],clips:{},order:[],done:{},pending:null,off:[],ext:null,au:null,extN:0};
function emit(why){try{P.dispatchEvent(new P.CustomEvent('floor-change',{detail:{why:why,kind:F.kind(),id:F.nowId()}}));}catch(e){}}
function on(t,ev,fn,o){t.addEventListener(ev,fn,o);F.off.push(function(){try{t.removeEventListener(ev,fn,o);}catch(e){}});}
function isField(t){return !!(t&&t.tagName&&(/^(input|textarea|select)$/i.test(t.tagName)||t.isContentEditable));}
F.destroy=function(){F.off.forEach(function(f){f();});F.off=[];try{if(F.au)F.au.pause();}catch(e){}};
if(!D.getElementById('floor-css')){try{var cs=D.createElement('style');cs.id='floor-css';cs.textContent='.st-key-floor_js{position:fixed!important;width:0!important;height:0!important;overflow:hidden!important;margin:0!important}';D.head.appendChild(cs);}catch(e){}}

// ---- الحالة ----
F.kind=function(){return F.h?F.h.kind:'';};
F.nowId=function(){return F.h?F.h.id:'';};
F.micOn=function(){var a=[];for(var i=0;i<F.recs.length;i++){if(F.recs[i].state==='recording')a.push(F.recs[i]);}F.recs=a;return a.length>0;};
F.typing=function(){var n=N();if(n-F.typingAt<8000)return true;return isField(D.activeElement)&&n-F.focusAt<15000;};
F.hard=function(){return F.kind()==='assistant'||F.kind()==='mic'||F.micOn();};
F.canChar=function(force){return !F.hard()&&!F.ext&&(!!force||(N()>=F.quietUntil&&!F.typing()));};  // force: نقرة المستخدم على الشخصية تتجاوز فترة الهدوء والكتابة (لا صوت المساعد ولا التسجيل)

// ---- حجز الكلمة: assistant يقاطع الجميع، char يخضع للجميع، mic يُسكت الجميع ----
F.claim=function(kind,id,stop,prio,force){
 var h=F.h,rank={char:0,assistant:2,mic:9};if(prio==null)prio=rank[kind]||0;
 if(kind==='char'){
  if(h&&h.kind!=='char')return false;
  if(!(h&&h.id===id)&&!F.canChar(force))return false;
 }else if(kind==='assistant'){
  if(F.micOn()||(h&&h.kind==='mic'))return false;
  if(h&&h.kind==='assistant'&&h.id!==id&&h.prio>prio)return false;
 }
 if(h&&h.id!==id){try{if(h.stop)h.stop();}catch(e){}}
 F.h={kind:kind,id:id,stop:stop||null,prio:prio,at:N()};
 emit('claim');return true;};
F.release=function(id){var h=F.h;if(!h||h.id!==id)return;F.h=null;
 if(h.kind==='assistant'||h.kind==='mic')F.quietUntil=N()+20000;
 emit('release');};

// ---- تشغيل صوت المساعد (في الصفحة الأم؛ لا ينقطع بإعادة رسم المكوّن) ----
F.reg=function(id,src,o){o=o||{};if(!src)return;
 F.clips[id]=src;F.order=F.order.filter(function(x){return x!==id;});F.order.push(id);
 while(F.order.length>8){delete F.clips[F.order.shift()];}
 if(o.auto&&!F.done[id]){F.done[id]=1;F.play(id,{auto:true,prio:o.prio||2});}};
F.play=function(id,o){o=o||{};var src=F.clips[id];if(!src)return false;
 var prio=o.prio||(o.auto?2:3);
 if(F.micOn()||F.kind()==='mic')return false;
 if(o.auto&&!(P.navigator.userActivation&&P.navigator.userActivation.hasBeenActive)){F.pending={id:id,prio:prio,at:N()};arm();return false;}
 var au=new P.Audio(src);au.preload='auto';
 var stop=function(){try{au.onended=null;au.onerror=null;au.pause();}catch(e){}if(F.au===au)F.au=null;};
 if(!F.claim('assistant',id,stop,prio))return false;
 F.au=au;
 var fin=function(){if(F.au===au)F.au=null;F.release(id);};
 au.onended=fin;au.onerror=fin;
 var p=au.play();
 if(p&&p.catch){p.catch(function(){fin();if(o.auto){F.pending={id:id,prio:prio,at:N()};arm();}});}
 return true;};
F.toggle=function(id){if(F.kind()==='assistant'&&F.nowId()===id){F.stop();return;}F.play(id,{auto:false,prio:3});};
F.stop=function(){var h=F.h;if(h&&h.kind==='assistant'){try{if(h.stop)h.stop();}catch(e){}F.release(h.id);}};
// المتصفح منع التشغيل التلقائي (لا نقرة بعد): نؤجّله إلى أول نقرة أو ضغطة مفتاح
var armed=false;
function arm(){if(armed)return;armed=true;
 var go=function(){D.removeEventListener('pointerdown',go,true);D.removeEventListener('keydown',go,true);armed=false;
  setTimeout(function(){var p=F.pending;F.pending=null;if(!p||N()-p.at>120000||F.micOn())return;if(F.h&&F.h.prio>=p.prio)return;F.play(p.id,{auto:true,prio:p.prio});},350);};
 D.addEventListener('pointerdown',go,true);D.addEventListener('keydown',go,true);}

// ---- أي <audio>/<video> آخر في الصفحة (st.audio وغيره): يُعامل كصوت مساعد، ويُوقف أثناء التسجيل ----
on(D,'play',function(e){var el=e.target;if(!el||!/^(audio|video)$/i.test(el.tagName||''))return;
 if(el.closest&&el.closest('.st-key-cmp_audio'))return;
 var id='ext'+(++F.extN),stop=function(){try{el.pause();}catch(x){}};
 if(F.micOn()||F.kind()==='mic'){stop();return;}
 F.claim('assistant',id,stop,3);F.ext=el;
 var end=function(){el.removeEventListener('pause',end);el.removeEventListener('ended',end);if(F.ext===el)F.ext=null;F.release(id);};
 el.addEventListener('pause',end);el.addEventListener('ended',end);},true);

// ---- الميكروفون: أثناء أي تسجيل يصمت الجميع ----
function micTick(){var was=F.kind()==='mic',now=F.micOn();
 if(now&&!was){F.claim('mic','mic',null,9);}
 else if(!now&&was){F.release('mic');}}
try{var MR=P.MediaRecorder;if(MR&&MR.prototype&&!MR.prototype.__fl){MR.prototype.__fl=1;var s0=MR.prototype.start;
 MR.prototype.start=function(){var out=s0.apply(this,arguments);try{if(F.recs.indexOf(this)<0)F.recs.push(this);this.addEventListener('stop',micTick);this.addEventListener('error',micTick);micTick();}catch(e){}return out;};}}catch(e){}
var mt=P.setInterval(micTick,800);F.off.push(function(){P.clearInterval(mt);});

// ---- الكتابة: تُسكت الشخصيتين فوراً وتمنعهما من البدء ----
on(D,'keydown',function(e){var t=e.target;if(!isField(t))return;var k=e.key;if(k==='Shift'||k==='Control'||k==='Alt'||k==='Meta'||k==='CapsLock'||k==='Tab')return;
 var was=F.typing();F.typingAt=N();if(!was)emit('typing');},true);
on(D,'focusin',function(e){if(isField(e.target)){F.focusAt=N();emit('focus');}},true);
})();"""


def boot_js() -> str:
    """مقتطف جافاسكربت يزرع المنسّق في الصفحة الأم إن لم يكن موجوداً (يُضمَّن في كل iframe صوتي ومحمّل الشخصيتين)."""
    lit = json.dumps(FLOOR_JS.replace("__FV__", FLOOR_VER), ensure_ascii=False).replace("</", "<\\/")  # نص جافاسكربت آمن داخل وسم script
    return ("(function(){try{var P=window.parent;if(!P.__floor||P.__floor.ver!=='" + FLOOR_VER + "'){var s=P.document.createElement('script');"
            "s.textContent=" + lit + ";P.document.head.appendChild(s);}}catch(e){}})();")


def floor_init() -> None:
    """يزرع المنسّق مبكراً (يُستدعى مرة في app.py). الـ HTML ثابت بين الإعادات فلا يُعاد تحميل الـ iframe."""
    with st.container(key="floor_js"):
        components.html("<script>" + boot_js() + "</script>", height=0)
