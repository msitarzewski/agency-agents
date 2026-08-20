/** Lightweight session guard for static hosting and API sessions. */
const SESSION_KEY='nexora_session';
function session(){try{return JSON.parse(localStorage.getItem(SESSION_KEY)||'null')}catch{return null}}
function isLoggedIn(){const s=session();return !!s&&Date.now()-s.lastActivity<CONFIG.SESSION_TIMEOUT}
function logout(){localStorage.removeItem(SESSION_KEY);location.href='index.html'}
function guard(){if(!isLoggedIn()&&!location.pathname.endsWith('index.html')&&!location.pathname.endsWith('/'))location.href='index.html'; const s=session(); if(s){s.lastActivity=Date.now();localStorage.setItem(SESSION_KEY,JSON.stringify(s)); document.querySelectorAll('[data-user]').forEach(e=>e.textContent=s.fullname||s.username);}}
function demoLogin(username,password){const users={prashant:'Prashant Khatri',shakeel:'Shakeel Patel',bhavik:'Bhavik Tankaria',tanjani:'Tanjani Malima',davie:'Davie Chavula'};if(users[username?.toLowerCase()]&&password===CONFIG.DEMO_PASSWORD){const s={username:username.toLowerCase(),fullname:users[username.toLowerCase()],role:'Admin',token:'demo-'+Date.now(),lastActivity:Date.now()};localStorage.setItem(SESSION_KEY,JSON.stringify(s));return s}return null}
