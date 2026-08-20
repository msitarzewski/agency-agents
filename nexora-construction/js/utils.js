/** Shared presentation and data helpers. */
const money = value => `MK ${Number(value || 0).toLocaleString('en-MW',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
const dateMW = value => { if(!value) return '—'; const d=new Date(value); return Number.isNaN(d.getTime())?'—':d.toLocaleDateString('en-GB'); };
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const toast = (message,type='success') => { const el=document.createElement('div'); el.className=`toast ${type}`; el.innerHTML=`<i class="fa-solid ${type==='success'?'fa-circle-check':type==='error'?'fa-circle-xmark':'fa-circle-info'}"></i><span>${escapeHTML(message)}</span>`; document.querySelector('#toast-root').append(el); setTimeout(()=>el.remove(),4200); };
const debounce=(fn,delay=250)=>{let t;return(...args)=>{clearTimeout(t);t=setTimeout(()=>fn(...args),delay)}};
const csv=(rows,name='export')=>{if(!rows.length)return toast('Nothing to export','warning'); const keys=Object.keys(rows[0]); const text=[keys.join(','),...rows.map(r=>keys.map(k=>`"${String(r[k]??'').replaceAll('"','""')}"`).join(','))].join('\n'); const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv'}));a.download=`${name}.csv`;a.click();};
const goHome=()=>location.href='dashboard.html'; const goBack=()=>history.length>1?history.back():goHome(); const printView=()=>window.print();
const initials=name=>(name||'N').split(' ').map(x=>x[0]).slice(0,2).join('').toUpperCase();
