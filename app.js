// Simulated ticker (example data)
(function(){
  const base=23.98, pts=[]; let p=base;
  for(let i=0;i<40;i++){p+= (Math.random()-.47)*.25; pts.push(p);}
  const line=document.getElementById('sparkline'), px=document.getElementById('px'), chg=document.getElementById('chg');
  function draw(){
    const min=Math.min(...pts), max=Math.max(...pts), r=(max-min)||1;
    line.setAttribute('points', pts.map((v,i)=>`${(i/(pts.length-1))*300},${75-((v-min)/r)*70}`).join(' '));
    const last=pts[pts.length-1], c=(last-base)/base*100;
    px.textContent='$'+last.toFixed(2);
    chg.textContent=(c>=0?'+':'')+c.toFixed(2)+'%';
    chg.className=c>=0?'up':'down';
  }
  draw();
  setInterval(()=>{pts.shift(); pts.push(pts[pts.length-1]+(Math.random()-.47)*.25); draw();},1500);
})();

// Diamond hands counter + rocket launch
(function(){
  const KEY='gme-hodl-count';
  let n=parseInt(localStorage.getItem(KEY)||'0',10);
  const counter=document.getElementById('counter'), hodl=document.getElementById('hodl'),
        launchBtn=document.getElementById('launchBtn'), rocket=document.getElementById('rocket'),
        sky=document.getElementById('sky'), status=document.getElementById('status');
  let flying=false;
  const render=()=>{counter.textContent=n.toLocaleString();};
  render();

  function burst(x,y,emojis){
    for(let i=0;i<14;i++){
      const s=document.createElement('span'); s.className='particle';
      s.textContent=emojis[i%emojis.length];
      s.style.left=x+'px'; s.style.top=y+'px';
      const a=Math.random()*Math.PI*2, d=60+Math.random()*90;
      s.style.setProperty('--dx',Math.cos(a)*d+'px'); s.style.setProperty('--dy',Math.sin(a)*d+'px');
      sky.appendChild(s); setTimeout(()=>s.remove(),1200);
    }
  }

  hodl.addEventListener('click',()=>{
    n++; localStorage.setItem(KEY,n); render();
    counter.classList.remove('bump'); void counter.offsetWidth; counter.classList.add('bump');
    const r=rocket.getBoundingClientRect(), s=sky.getBoundingClientRect();
    burst(r.left-s.left+20, r.top-s.top+20, ['💎','🙌']);
    if(n%10===0){status.textContent=`${n} HODLs! Fuel tank full 🚀`; launch();}
    else status.textContent=`${10-(n%10)} more HODL${10-(n%10)===1?'':'s'} until the next launch.`;
  });
  launchBtn.addEventListener('click',launch);

  function launch(){
    if(flying) return; flying=true;
    rocket.classList.add('shake'); status.textContent='T-minus 3… 2… 1…';
    setTimeout(()=>{
      rocket.classList.remove('shake'); rocket.classList.add('fly');
      status.textContent='LIFTOFF! 🚀 Next stop: the moon.';
      const s=sky.getBoundingClientRect();
      burst(s.width/2, s.height-60, ['🔥','✨','💨']);
    },900);
    setTimeout(()=>{
      sky.classList.add('landed'); burst(s0().width-70, 60, ['✨','🌟','💎']);
      status.textContent='🌕 Touchdown on the moon. GG!';
    },3000);
    setTimeout(()=>{
      rocket.classList.remove('fly'); sky.classList.remove('landed'); flying=false;
      status.textContent='Rocket refueled. HODL to fuel the next launch.';
    },4600);
  }
  const s0=()=>sky.getBoundingClientRect();
})();
