/* ══════════════════════════════════════════════════════════════════
   MYSTIK — script.js | Premium + 3D Avatar System
   ══════════════════════════════════════════════════════════════════ */

// ─── City Data ───
const CITIES = [
  { name: 'London', country: 'UK', listeners: 166 },
  { name: 'Los Angeles', country: 'USA', listeners: 140 },
  { name: 'Chicago', country: 'USA', listeners: 135 },
  { name: 'New York', country: 'USA', listeners: 127 },
  { name: 'Toronto', country: 'Canada', listeners: 126 },
  { name: 'Denver', country: 'USA', listeners: 120 },
  { name: 'Berlin', country: 'Germany', listeners: 118 },
  { name: 'Sydney', country: 'Australia', listeners: 117 },
  { name: 'Philadelphia', country: 'USA', listeners: 107 },
  { name: 'Brooklyn', country: 'USA', listeners: 98 },
];

// ─── Register GSAP Plugins ───
if (window.gsap) gsap.registerPlugin(ScrollTrigger);

// ══════════════════════════════════════════════════════════════════
// 1. THREE.JS BACKGROUND PARTICLE FIELD — lazy init on visible
// ══════════════════════════════════════════════════════════════════
(function initBackgroundParticles() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && window.THREE) {
      observer.disconnect();
      _initParticles();
    }
  }, { threshold: 0.1 });
  observer.observe(canvas);
})();

function _initParticles() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas || !window.THREE) return;
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 5;
  const particleCount = 200; // reduced for performance
  const positions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i++) {
    positions[i*3]   = (Math.random()-0.5)*20;
    positions[i*3+1] = (Math.random()-0.5)*20;
    positions[i*3+2] = (Math.random()-0.5)*20;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({ size: 0.06, color: 0xc084fc, transparent: true, opacity: 0.4, blending: THREE.AdditiveBlending });
  const particles = new THREE.Points(geo, mat);
  scene.add(particles);
  let mouseX=0, mouseY=0, targetX=0, targetY=0;
  document.addEventListener('mousemove', e => { mouseX=(e.clientX/window.innerWidth-0.5)*2; mouseY=-(e.clientY/window.innerHeight-0.5)*2; });
  window.addEventListener('resize', () => { camera.aspect=window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
  let t=0;
  function animate() {
    requestAnimationFrame(animate);
    t+=0.005;
    targetX+=(mouseX-targetX)*0.02; targetY+=(mouseY-targetY)*0.02;
    camera.position.x+=(targetX*0.5-camera.position.x)*0.05;
    camera.position.y+=(targetY*0.5-camera.position.y)*0.05;
    camera.lookAt(scene.position);
    particles.rotation.y+=0.0003;
    renderer.render(scene, camera);
  }
  animate();
}

// ══════════════════════════════════════════════════════════════════
// 2. HERO LOGO — lazy init when visible
// ══════════════════════════════════════════════════════════════════
(function initLogo3D() {
  const canvas = document.getElementById('hero-logo-canvas');
  if (!canvas) return;
  const container = document.getElementById('heroLogo3D');
  if (!container) return;
  // Init immediately on load, don't lazy wait
  if (document.readyState === 'complete') {
    setTimeout(_initLogo3D, 0);
  } else {
    window.addEventListener('load', () => setTimeout(_initLogo3D, 0));
  }
  // Also try IntersectionObserver as backup
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      observer.disconnect();
      _initLogo3D();
    }
  }, { threshold: 0.01 });
  observer.observe(canvas);
  // Fallback: init after 3s no matter what
  setTimeout(() => { observer.disconnect(); _initLogo3D(); }, 3000);
})();

function _initLogo3D() {
  const canvas = document.getElementById('hero-logo-canvas');
  const container = document.getElementById('heroLogo3D');
  if (!canvas || !window.THREE || !container) return;

  const w = container.clientWidth || 500;
  const h = container.clientHeight || 500;
  canvas.width = w; canvas.height = h;

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
  camera.position.z = 5;

  // Lights
  const ambient = new THREE.AmbientLight(0x7c3aed, 0.8);
  scene.add(ambient);
  const keyLight = new THREE.DirectionalLight(0xfff8e7, 1.5);
  keyLight.position.set(2, 4, 5);
  scene.add(keyLight);
  const fillLight = new THREE.PointLight(0xc084fc, 1.0, 15);
  fillLight.position.set(-4, 0, 3);
  scene.add(fillLight);
  const rimLight = new THREE.PointLight(0x4fc3f7, 0.5, 10);
  rimLight.position.set(0, -3, -2);
  scene.add(rimLight);

  const group = new THREE.Group();
  scene.add(group);

  // ── Build depth layers (back → front) ──
  const TAN = 0xb88a58;
  const PURPLE = 0xc084fc;
  const DEPTH = 0.35;

  // Back glow plate
  const plateBack = new THREE.Mesh(
    new THREE.PlaneGeometry(3.2, 1.6),
    new THREE.MeshBasicMaterial({
      color: 0x0a0510,
      transparent: true,
      opacity: 0.7,
      side: THREE.DoubleSide,
    })
  );
  plateBack.position.z = -DEPTH * 1.5;
  group.add(plateBack);

  // Purple edge glow (back)
  const edgeMat = new THREE.MeshBasicMaterial({
    color: PURPLE,
    transparent: true,
    opacity: 0.2,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const edgeBack = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 1.8), edgeMat);
  edgeBack.position.z = -DEPTH * 2.0;
  group.add(edgeBack);
  group.userData.edgeBack = edgeBack;

  // Extruded text layers (creates depth illusion)
  const loader = new THREE.TextureLoader();
  loader.load(
    'logo-3d.png',
    (tex) => {
      tex.minFilter = THREE.LinearFilter;
      tex.magFilter = THREE.LinearFilter;

      // Detect aspect from natural dimensions if possible
      const aspect = tex.image ? tex.image.width / tex.image.height : (497 / 309);

      // Main logo plane — the image IS the 3D render, just display it
      const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
      const geo = new THREE.PlaneGeometry(aspect * 2.5, 2.5);
      const mesh = new THREE.Mesh(geo, mat);
      group.add(mesh);

      // Glow ring behind
      const ringGeo = new THREE.TorusGeometry(1.6, 0.035, 8, 80);
      const ringMat = new THREE.MeshBasicMaterial({
        color: PURPLE,
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.z = -0.05;
      group.add(ring);
      group.userData.ring = ring;
    },
    undefined,
    () => {
      // Fallback — dark rectangle
      const geo = new THREE.BoxGeometry(2, 0.8, 0.1);
      const mat = new THREE.MeshStandardMaterial({ color: 0x1a0a05, roughness: 0.5 });
      const mesh = new THREE.Mesh(geo, mat);
      group.add(mesh);
    }
  );

  // ── Floating particles ──
  const particleCount = 60;
  const particlePos = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i++) {
    const theta = Math.random() * Math.PI * 2;
    const r = 1.2 + Math.random() * 1.5;
    particlePos[i * 3] = Math.cos(theta) * r;
    particlePos[i * 3 + 1] = (Math.random() - 0.5) * 2;
    particlePos[i * 3 + 2] = (Math.random() - 0.5) * 1.5 - 1;
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
  const pMat = new THREE.PointsMaterial({
    color: PURPLE,
    size: 0.025,
    transparent: true,
    opacity: 0.7,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const particles = new THREE.Points(pGeo, pMat);
  scene.add(particles);
  group.userData.particles = particles;

  // ── Mouse parallax ──
  let targetX = 0, targetY = 0;
  let currentX = 0, currentY = 0;
  document.addEventListener('mousemove', (e) => {
    targetX = (e.clientX / window.innerWidth - 0.5) * 2;
    targetY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  // ── Resize ──
  window.addEventListener('resize', () => {
    const nw = container.clientWidth, nh = container.clientHeight;
    canvas.width = nw; canvas.height = nh;
    renderer.setSize(nw, nh);
    camera.aspect = nw / nh;
    camera.updateProjectionMatrix();
  });

  // ── Animate ──
  let t = 0;
  function animate() {
    requestAnimationFrame(animate);
    t += 0.012;

    currentX += (targetX - currentX) * 0.04;
    currentY += (targetY - currentY) * 0.04;

    // 3D rotation with parallax
    group.rotation.y = currentX * 0.25;
    group.rotation.x = -currentY * 0.18;

    // Gentle float
    group.position.y = Math.sin(t * 0.7) * 0.05;

    // Ring pulse
    if (group.userData.ring) {
      group.userData.ring.rotation.z = t * 0.25;
      group.userData.ring.material.opacity = 0.3 + Math.sin(t * 1.5) * 0.2;
      group.userData.ring.rotation.x = Math.sin(t * 0.5) * 0.1;
      group.userData.ring.rotation.y = Math.cos(t * 0.3) * 0.1;
    }

    // Particle drift
    if (group.userData.particles) {
      group.userData.particles.rotation.y = t * 0.05;
    }

    renderer.render(scene, camera);
  }
  animate();
})();

// ══════════════════════════════════════════════════════════════════
// 3. FULL PAGE 3D OVERLAY (floating icosahedron)
// ══════════════════════════════════════════════════════════════════
(function initFull3DScene() {
  const canvas = document.getElementById('logo-canvas');
  if (!canvas || !window.THREE) return;
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 100);
  camera.position.z = 6;
  const iGeo = new THREE.IcosahedronGeometry(0.8, 1);
  const iMat = new THREE.MeshPhysicalMaterial({ color: 0x7c3aed, metalness: 0.9, roughness: 0.1, transparent: true, opacity: 0.25, wireframe: true });
  const ico = new THREE.Mesh(iGeo, iMat);
  scene.add(ico);
  const iGeo2 = new THREE.IcosahedronGeometry(0.55, 0);
  const iMat2 = new THREE.MeshPhysicalMaterial({ color: 0xc084fc, metalness: 0.8, roughness: 0.2, transparent: true, opacity: 0.12 });
  scene.add(new THREE.Mesh(iGeo2, iMat2));
  const orbitCount = 60;
  const orbitPos = new Float32Array(orbitCount*3);
  for(let i=0;i<orbitCount;i++){
    const t2 = Math.random()*Math.PI*2, p = Math.random()*Math.PI, r = 1.5+Math.random()*1.5;
    orbitPos[i*3]=r*Math.sin(p)*Math.cos(t2);
    orbitPos[i*3+1]=r*Math.sin(p)*Math.sin(t2);
    orbitPos[i*3+2]=r*Math.cos(p);
  }
  const orbitGeo = new THREE.BufferGeometry();
  orbitGeo.setAttribute('position', new THREE.BufferAttribute(orbitPos, 3));
  const orbitMat = new THREE.PointsMaterial({ size: 0.025, color: 0xc084fc, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending });
  scene.add(new THREE.Points(orbitGeo, orbitMat));
  let mx=0,my=0,tx=0,ty=0;
  document.addEventListener('mousemove', e => { mx=(e.clientX/window.innerWidth-0.5); my=-(e.clientY/window.innerHeight-0.5); });
  window.addEventListener('resize', () => { camera.aspect=window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
  let t=0;
  function animate() {
    requestAnimationFrame(animate);
    t+=0.005;
    tx+=(mx-tx)*0.03; ty+=(my-ty)*0.03;
    camera.position.x+=(tx*1.5-camera.position.x)*0.05;
    camera.position.y+=(ty*1.5-camera.position.y)*0.05;
    camera.lookAt(0,0,0);
    ico.rotation.x+=0.005; ico.rotation.y+=0.008;
    iMat.opacity=0.15+Math.sin(t*2)*0.1;
    renderer.render(scene, camera);
  }
  animate();
})();

// ══════════════════════════════════════════════════════════════════
// 4. CUSTOM CURSOR
// ══════════════════════════════════════════════════════════════════
(function initCursor() {
  const cursor = document.getElementById('cursor');
  const follower = document.getElementById('cursorFollower');
  if (!cursor || !follower) return;
  if ('ontouchstart' in window) { cursor.style.display='none'; follower.style.display='none'; return; }
  let cx=window.innerWidth/2, cy=window.innerHeight/2, fx=cx, fy=cy;
  follower.style.left=fx+'px'; follower.style.top=fy+'px';
  cursor.style.left=cx+'px'; cursor.style.top=cy+'px';
  document.addEventListener('mousemove', e => { cx=e.clientX; cy=e.clientY; });
  function a() { fx+=(cx-fx)*0.15; fy+=(cy-fy)*0.15; follower.style.left=fx+'px'; follower.style.top=fy+'px'; cursor.style.left=cx+'px'; cursor.style.top=cy+'px'; requestAnimationFrame(a); }
  a();
  document.querySelectorAll('a,button,[data-hover],[data-tilt]').forEach(el => {
    el.addEventListener('mouseenter', () => cursor.classList.add('hovering'));
    el.addEventListener('mouseleave', () => cursor.classList.remove('hovering'));
  });
})();

// ══════════════════════════════════════════════════════════════════
// 5. NAV & MENU
// ══════════════════════════════════════════════════════════════════
(function initNav() {
  const nav = document.getElementById('mainNav');
  window.addEventListener('scroll', () => nav?.classList.toggle('scrolled', window.scrollY>60));
})();
(function initMobileMenu() {
  const toggle = document.getElementById('menuToggle'), menu = document.getElementById('mobileMenu');
  toggle?.addEventListener('click', () => { toggle.classList.toggle('active'); menu?.classList.toggle('open'); });
  menu?.querySelectorAll('.mobile-link').forEach(l => l.addEventListener('click', () => { toggle?.classList.remove('active'); menu?.classList.remove('open'); }));
})();

// ══════════════════════════════════════════════════════════════════
// 6. GSAP SCROLL REVEALS
// ══════════════════════════════════════════════════════════════════
(function initScrollAnimations() {
  document.querySelectorAll('[data-section]').forEach(section => {
    const children = section.querySelectorAll('.section-title,.section-sub,.section-label,.album-tile,.about-text,.about-map,.about-pillars,.connect-card,.tour-card,.signup-left,.signup-right');
    gsap.fromTo(children, { opacity:0, y:40 }, {
      opacity:1, y:0, duration:0.8, stagger:0.08, ease:'power2.out',
      scrollTrigger: { trigger:section, start:'top 82%', toggleActions:'play none none reverse' }
    });
  });
})();

// ══════════════════════════════════════════════════════════════════
// 7. 3D TILT
// ══════════════════════════════════════════════════════════════════
(function initTilt() {
  document.querySelectorAll('[data-tilt]').forEach(el => {
    el.addEventListener('mousemove', e => {
      const r = el.getBoundingClientRect();
      const dx=((e.clientX-r.left)/r.width-0.5)*2, dy=-((e.clientY-r.top)/r.height-0.5)*2;
      el.style.transform=`perspective(1000px) rotateX(${dy*6}deg) rotateY(${dx*6}deg) translateZ(8px)`;
      el.style.transition='none';
    });
    el.addEventListener('mouseleave', () => {
      el.style.transform='perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
      el.style.transition='transform 0.6s cubic-bezier(0.25,0.46,0.45,0.94)';
    });
  });
})();

// ══════════════════════════════════════════════════════════════════
// 8. STAT COUNTERS — set numbers immediately
// ══════════════════════════════════════════════════════════════════
(function initCounters() {
  document.querySelectorAll('.h-stat-num[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    if (target) el.textContent = target.toLocaleString();
  });
})();

// ══════════════════════════════════════════════════════════════════
// 9. CITY LIST
// ══════════════════════════════════════════════════════════════════
(function initCities() {
  const list = document.getElementById('cityList');
  if (!list) return;
  list.innerHTML = CITIES.map(c => `<div class="city-row"><span class="city-name">${c.name}, ${c.country}</span><span class="city-count">${c.listeners.toLocaleString()}</span></div>`).join('');

  // Cursor pulse effect — highlight row under mouse
  list.addEventListener('mousemove', e => {
    const row = e.target.closest('.city-row');
    if (!row) return;
    list.querySelectorAll('.city-row').forEach(r => r.classList.remove('pulsing'));
    row.classList.add('pulsing');
  });
  list.addEventListener('mouseleave', () => {
    list.querySelectorAll('.city-row').forEach(r => r.classList.remove('pulsing'));
  });
})();

// ══════════════════════════════════════════════════════════════════
// 10. FORM
// ══════════════════════════════════════════════════════════════════
(function initForm() {
  const form = document.getElementById('signupForm');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    const label = btn?.querySelector('.btn-label'), spinner = btn?.querySelector('.btn-spinner');
    if(label) label.style.display='none'; if(spinner) spinner.style.display='flex';
    const email = form.querySelector('[name="email"]').value.trim();
    const name = form.querySelector('[name="name"]').value.trim();
    const interest = form.querySelector('[name="interest"]')?.value;
    try { await fetch('https://buttondown.email/api/emails/embed-subscribe/mystik', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,name,tags:interest?[interest]:[]}) }); } catch(_) {}
    form.style.display='none';
    const s = document.getElementById('signupSuccess');
    if(s) { s.style.display='block'; gsap.fromTo(s,{opacity:0,y:20},{opacity:1,y:0,duration:0.6}); }
  });
})();

// ══════════════════════════════════════════════════════════════════
// 11. MARQUEE + SCROLL CUE + PARALLAX BLOBS + SMOOTH SCROLL
// ══════════════════════════════════════════════════════════════════
(function initMarquee() {
  const track = document.getElementById('marqueeTrack');
  if (!track) return;
  gsap.to(track, { x: -track.scrollWidth/2, duration: 40, ease: 'none', repeat: -1 });
})();
(function initScrollCue() {
  const cue = document.getElementById('scrollCue');
  if (!cue) return;
  window.addEventListener('scroll', () => { cue.style.opacity = window.scrollY>200?'0':'1'; cue.style.transition='opacity 0.5s'; });
})();
(function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function(e) {
      const t = document.querySelector(this.getAttribute('href'));
      if(t) t.scrollIntoView({ behavior:'smooth', block:'start' });
    });
  });
})();
(function initBlobParallax() {
  const blobs = document.querySelectorAll('.light-blob');
  let mx=0,my=0;
  document.addEventListener('mousemove', e => { mx=(e.clientX/window.innerWidth-0.5)*2; my=(e.clientY/window.innerHeight-0.5)*2; });
  function a() { blobs.forEach(b => { const s=parseFloat(b.dataset.speed)||0.3; b.style.transform=`translate(${mx*30*s}px,${my*30*s}px)`; }); requestAnimationFrame(a); }
  a();
})();

console.log('%c MYSTIK ', 'background:#7c3aed;color:white;font-size:20px;font-weight:bold;padding:8px 20px;border-radius:4px');
console.log('%cMemento Mori — Remember death. Make music that outlives you.','color:#c084fc');
