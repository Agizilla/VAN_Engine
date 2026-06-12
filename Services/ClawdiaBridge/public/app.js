// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  PivotSCADA — EventBus + WebSocketClient + 3D SCADA Scene
//  Architecture: WS → deserialize once → EventBus → DOM/Three
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/* === EventBus === */
class EventBus {
  constructor() {
    this._listeners = new Map();
    this._history = new Map();
  }
  on(event, cb) {
    if (!this._listeners.has(event)) this._listeners.set(event, new Set());
    this._listeners.get(event).add(cb);
    return () => this.off(event, cb);
  }
  off(event, cb) { this._listeners.get(event)?.delete(cb); }
  emit(event, data) {
    if (!this._history.has(event)) this._history.set(event, []);
    const h = this._history.get(event);
    h.push({ data, ts: performance.now() });
    if (h.length > 10) h.shift();
    this._listeners.get(event)?.forEach(cb => { try { cb(data); } catch (e) { console.error('[EventBus]', e); } });
  }
  once(event, cb) { const w = d => { this.off(event, w); cb(d); }; this.on(event, w); }
  last(event) { const h = this._history.get(event); return h?.length ? h[h.length - 1].data : null; }
}

/* === WebSocket Client with reconnection, backpressure, throttling === */
class WebSocketClient {
  constructor(url, bus) {
    this.url = url;
    this.bus = bus;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 30000;
    this.baseReconnectDelay = 500;
    this.queue = [];
    this.maxQueue = 200;
    this.draining = false;
    this._closed = false;
    this._lastPing = 0;
    this._pingTimer = null;
    this._throttle = {};
  }

  connect() {
    if (this._closed) return;
    this.bus.emit('connection:status', 'connecting');
    try {
      this.ws = new WebSocket(this.url);
    } catch (e) {
      this.bus.emit('connection:status', 'disconnected');
      this._scheduleReconnect();
      return;
    }
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.bus.emit('connection:status', 'connected');
      this._startPing();
      this._drainQueue();
    };
    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        this.bus.emit(`ws:${msg.type}`, msg.data);
        this.bus.emit('ws:message', msg);
        if (msg.type === 'pong') this._lastPing = Date.now();
      } catch {}
    };
    this.ws.onclose = () => {
      this._stopPing();
      this.bus.emit('connection:status', 'disconnected');
      if (!this._closed) this._scheduleReconnect();
    };
    this.ws.onerror = () => {
      this.bus.emit('connection:status', 'disconnected');
    };
  }

  close() {
    this._closed = true;
    this._stopPing();
    if (this.ws) { this.ws.onclose = null; this.ws.close(); this.ws = null; }
  }

  send(type, data) {
    const msg = JSON.stringify({ type, data });
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (this.ws.bufferedAmount > 65536) {
        this.bus.emit('event', { level: 'warning', message: 'Backpressure: queuing message' });
        this._enqueue(msg);
        return;
      }
      this.ws.send(msg);
    } else {
      this._enqueue(msg);
    }
  }

  sendThrottled(type, data, key, ms = 100) {
    const now = Date.now();
    if (this._throttle[key] && now - this._throttle[key] < ms) return;
    this._throttle[key] = now;
    this.send(type, data);
  }

  _enqueue(msg) {
    if (this.queue.length >= this.maxQueue) {
      this.queue.shift();
      this.bus.emit('event', { level: 'warning', message: 'Backpressure: dropping oldest queued message' });
    }
    this.queue.push(msg);
  }

  async _drainQueue() {
    if (this.draining || !this.queue.length) return;
    this.draining = true;
    while (this.queue.length && this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (this.ws.bufferedAmount > 32768) {
        await new Promise(r => setTimeout(r, 50));
        continue;
      }
      this.ws.send(this.queue.shift());
    }
    this.draining = false;
  }

  _scheduleReconnect() {
    const delay = Math.min(this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
    this.reconnectAttempts++;
    this.bus.emit('event', { level: 'info', message: `Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})` });
    setTimeout(() => this.connect(), delay);
  }

  _startPing() {
    this._lastPing = Date.now();
    this._pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
        if (Date.now() - this._lastPing > 15000) {
          this.bus.emit('event', { level: 'warning', message: 'Heartbeat timeout — reconnecting' });
          this.ws.close();
        }
      }
    }, 5000);
  }
  _stopPing() { if (this._pingTimer) { clearInterval(this._pingTimer); this._pingTimer = null; } }
  get latency() { return this._lastPing ? Date.now() - this._lastPing : 0; }
}

/* === THREE.js SCADA 3D Scene === */
class ScadaScene {
  constructor(container, bus) {
    this.bus = bus;
    this.container = container;
    this.clock = new THREE.Clock();
    this.flowParticles = [];

    this._setupRenderer();
    this._setupScene();
    this._setupLights();
    this._build();
    this._bindEvents();
    this._animate();
  }

  _setupRenderer() {
    const rect = this.container.getBoundingClientRect();
    this.camera = new THREE.PerspectiveCamera(40, rect.width / rect.height, 0.1, 100);
    this.camera.position.set(14, 10, 16);
    this.camera.lookAt(0, 0, 0);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setSize(rect.width, rect.height);
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    this.container.appendChild(this.renderer.domElement);

    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 1, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 4;
    this.controls.maxDistance = 40;
    this.controls.maxPolarAngle = Math.PI / 2.05;
    this.controls.update();

    new ResizeObserver(() => {
      const r = this.container.getBoundingClientRect();
      this.camera.aspect = r.width / r.height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(r.width, r.height);
    }).observe(this.container);
  }

  _setupScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0d1a2b);
    this.scene.fog = new THREE.Fog(0x0d1a2b, 25, 45);
  }

  _setupLights() {
    const amb = new THREE.AmbientLight(0x8899bb, 0.4);
    this.scene.add(amb);

    const sun = new THREE.DirectionalLight(0xffeedd, 2.0);
    sun.position.set(15, 20, 10);
    sun.castShadow = true;
    sun.shadow.mapSize.width = 2048;
    sun.shadow.mapSize.height = 2048;
    sun.shadow.camera.near = 0.5;
    sun.shadow.camera.far = 50;
    sun.shadow.camera.left = -20;
    sun.shadow.camera.right = 20;
    sun.shadow.camera.top = 20;
    sun.shadow.camera.bottom = -20;
    this.scene.add(sun);

    const fill = new THREE.DirectionalLight(0x6688cc, 0.3);
    fill.position.set(-10, 5, -10);
    this.scene.add(fill);
  }

  _build() {
    this._buildGround();
    this._buildTank();
    this._buildPipes();
    this._buildPump();
    this._buildValve();
    this._buildFlowParticles();
    this._buildGridHelpers();
  }

  _buildGround() {
    const geo = new THREE.PlaneGeometry(40, 40);
    const mat = new THREE.MeshStandardMaterial({
      color: 0x2a3d2a,
      roughness: 0.9,
      metalness: 0.0,
    });
    const ground = new THREE.Mesh(geo, mat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -1;
    ground.receiveShadow = true;
    this.scene.add(ground);

    const grid = new THREE.GridHelper(40, 40, 0x3a5a3a, 0x2a4a2a);
    grid.position.y = -0.95;
    this.scene.add(grid);
  }

  _buildTank() {
    this.tankGroup = new THREE.Group();
    this.tankGroup.position.set(-7, 0, 0);

    const mat = new THREE.MeshPhysicalMaterial({
      color: 0x5a8a6a,
      metalness: 0.2,
      roughness: 0.6,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
    });
    const geo = new THREE.BoxGeometry(2.4, 3.0, 2.0);
    const tank = new THREE.Mesh(geo, mat);
    tank.position.y = 0.5;
    tank.castShadow = true;
    this.tankGroup.add(tank);

    const edgeGeo = new THREE.EdgesGeometry(geo);
    const edgeMat = new THREE.LineBasicMaterial({ color: 0x7a9a8a, transparent: true, opacity: 0.5 });
    const edges = new THREE.LineSegments(edgeGeo, edgeMat);
    edges.position.copy(tank.position);
    this.tankGroup.add(edges);

    this.waterMat = new THREE.MeshPhysicalMaterial({
      color: 0x1a7acc,
      metalness: 0.0,
      roughness: 0.1,
      transparent: true,
      opacity: 0.5,
    });
    const waterGeo = new THREE.BoxGeometry(2.2, 1, 1.8);
    this.waterMesh = new THREE.Mesh(waterGeo, this.waterMat);
    this.waterMesh.position.set(0, 0.2, 0);
    this.tankGroup.add(this.waterMesh);

    this.scene.add(this.tankGroup);
  }

  _buildPipes() {
    this.pipes = [];
    this.pipeMat = new THREE.MeshPhysicalMaterial({
      color: 0x7a8a9a,
      metalness: 0.7,
      roughness: 0.4,
    });

    // pipe segments: { from, to, radius }
    const segments = [
      { from: [-5.8, 0.2, 0], to: [-2.0, 0.2, 0], r: 0.15 },
      { from: [-2.0, 0.2, 0], to: [0, 0.2, 0], r: 0.18 },
      { from: [0, 0.2, 0], to: [2.0, 0.2, 0], r: 0.18 },
      { from: [2.0, 0.2, 0], to: [3.8, 0.2, 0], r: 0.15 },
    ];

    for (const seg of segments) {
      const from = new THREE.Vector3(...seg.from);
      const to = new THREE.Vector3(...seg.to);
      const mid = new THREE.Vector3().addVectors(from, to).multiplyScalar(0.5);
      const dir = new THREE.Vector3().subVectors(to, from);
      const len = dir.length();
      dir.normalize();

      const geo = new THREE.CylinderGeometry(seg.r, seg.r, len, 12, 1, true);
      const mesh = new THREE.Mesh(geo, this.pipeMat);
      mesh.position.copy(mid);
      const up = new THREE.Vector3(0, 1, 0);
      const quat = new THREE.Quaternion().setFromUnitVectors(up, dir);
      mesh.quaternion.copy(quat);
      mesh.castShadow = true;
      this.scene.add(mesh);
      this.pipes.push(mesh);

      // metallic joint ring at each end
      const ringMat = new THREE.MeshPhysicalMaterial({ color: 0x5a6a7a, metalness: 0.8, roughness: 0.3 });
      for (const pos of [from, to]) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(seg.r + 0.04, 0.04, 8, 16), ringMat);
        ring.position.copy(pos);
        const rq = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir);
        ring.quaternion.copy(rq);
        this.scene.add(ring);
      }
    }
  }

  _buildFlowParticles() {
    this.flowPaths = [
      { from: [-5.8, 0.2, 0], to: [-2.0, 0.2, 0], count: 12 },
      { from: [-2.0, 0.2, 0], to: [0, 0.2, 0], count: 14 },
      { from: [0, 0.2, 0], to: [2.0, 0.2, 0], count: 14 },
      { from: [2.0, 0.2, 0], to: [3.8, 0.2, 0], count: 12 },
    ];

    this.particleSystems = [];
    const particleMat = new THREE.PointsMaterial({
      color: 0x4fc3f7,
      size: 0.08,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    for (const path of this.flowPaths) {
      const from = new THREE.Vector3(...path.from);
      const to = new THREE.Vector3(...path.to);
      const dir = new THREE.Vector3().subVectors(to, from);
      const len = dir.length();

      const positions = new Float32Array(path.count * 3);
      const offsets = new Float32Array(path.count);
      for (let i = 0; i < path.count; i++) {
        offsets[i] = i / path.count;
        const t = offsets[i];
        const p = new THREE.Vector3().copy(from).lerp(to, t);
        positions[i * 3] = p.x;
        positions[i * 3 + 1] = p.y;
        positions[i * 3 + 2] = p.z;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const points = new THREE.Points(geo, particleMat.clone());
      this.scene.add(points);
      this.particleSystems.push({ points, offsets, from, to, dir, len, geo });
    }
  }

  _buildPump() {
    this.pumpGroup = new THREE.Group();
    this.pumpGroup.position.set(0, 0, 0);

    // base plate
    const base = new THREE.Mesh(
      new THREE.BoxGeometry(1.2, 0.2, 0.8),
      new THREE.MeshPhysicalMaterial({ color: 0x3a4a5a, metalness: 0.6, roughness: 0.5 })
    );
    base.position.y = -0.1;
    base.castShadow = true;
    this.pumpGroup.add(base);

    // pump body (cylinder)
    this.pumpMat = new THREE.MeshPhysicalMaterial({
      color: 0x4a90d9,
      metalness: 0.4,
      roughness: 0.5,
    });
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.7, 0.8, 16), this.pumpMat);
    body.position.y = 0.4;
    body.castShadow = true;
    this.pumpGroup.add(body);

    // motor housing
    const motor = new THREE.Mesh(
      new THREE.CylinderGeometry(0.4, 0.5, 0.5, 12),
      new THREE.MeshPhysicalMaterial({ color: 0x5a6a7a, metalness: 0.6, roughness: 0.4 })
    );
    motor.position.y = 0.9;
    motor.castShadow = true;
    this.pumpGroup.add(motor);

    // motor fan cover (ribbed top)
    const fan = new THREE.Mesh(
      new THREE.CylinderGeometry(0.35, 0.4, 0.15, 12),
      new THREE.MeshPhysicalMaterial({ color: 0x4a5a6a, metalness: 0.7, roughness: 0.3 })
    );
    fan.position.y = 1.2;
    this.pumpGroup.add(fan);

    // status ring
    const ringMat = new THREE.MeshPhysicalMaterial({
      color: 0xef5350,
      emissive: 0xef5350,
      emissiveIntensity: 0,
      metalness: 0.1,
      roughness: 0.4,
      transparent: true,
      opacity: 0.9,
    });
    this.statusRing = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.04, 8, 24), ringMat);
    this.statusRing.position.y = 0.4;
    this.statusRing.rotation.x = Math.PI / 2;
    this.pumpGroup.add(this.statusRing);

    // inlet/outlet flanges
    const flangeMat = new THREE.MeshPhysicalMaterial({ color: 0x5a6a7a, metalness: 0.7, roughness: 0.3 });
    for (const [dx, rot] of [[-0.8, 0], [0.8, Math.PI]]) {
      const flange = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 12), flangeMat);
      flange.position.set(dx, 0.2, 0);
      flange.rotation.z = rot === 0 ? 0 : Math.PI;
      flange.rotation.x = Math.PI / 2;
      this.pumpGroup.add(flange);
    }

    this.scene.add(this.pumpGroup);
  }

  _buildValve() {
    this.valveGroup = new THREE.Group();
    this.valveGroup.position.set(3.8, 0, 0);

    // body
    const vMat = new THREE.MeshPhysicalMaterial({
      color: 0xff8a65,
      metalness: 0.3,
      roughness: 0.6,
    });
    this.valveMat = vMat;
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.5, 0.5), vMat);
    body.position.y = 0.2;
    body.castShadow = true;
    this.valveGroup.add(body);

    // handwheel
    const wheel = new THREE.Mesh(
      new THREE.TorusGeometry(0.25, 0.04, 8, 16),
      new THREE.MeshPhysicalMaterial({ color: 0x8a7a5a, metalness: 0.5, roughness: 0.5 })
    );
    wheel.position.y = 0.6;
    wheel.rotation.x = Math.PI / 2;
    this.valveGroup.add(wheel);

    // stem
    const stem = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 0.2, 6),
      new THREE.MeshPhysicalMaterial({ color: 0x6a7a8a, metalness: 0.7, roughness: 0.3 })
    );
    stem.position.y = 0.45;
    this.valveGroup.add(stem);

    this.scene.add(this.valveGroup);
  }

  _buildGridHelpers() {
    // small reference markers
    const dotMat = new THREE.PointsMaterial({ color: 0x3a5a4a, size: 0.05 });
    const dotGeo = new THREE.BufferGeometry();
    const dots = [];
    for (let x = -15; x <= 15; x += 2) {
      for (let z = -15; z <= 15; z += 2) {
        if (Math.abs(x) < 10 && Math.abs(z) < 6) continue;
        dots.push(x, -0.9, z);
      }
    }
    dotGeo.setAttribute('position', new THREE.Float32BufferAttribute(dots, 3));
    this.scene.add(new THREE.Points(dotGeo, dotMat));
  }

  _bindEvents() {
    this.bus.on('telemetry', (d) => this._update(d));
    this.bus.on('connection:status', (s) => {
      const c = this.statusRing?.material;
      if (!c) return;
      if (s === 'connected') {
        c.color.setHex(0x66bb6a);
        c.emissive.setHex(0x66bb6a);
        c.emissiveIntensity = 0.3;
      } else {
        c.color.setHex(0xef5350);
        c.emissive.setHex(0xef5350);
        c.emissiveIntensity = 0.1;
      }
    });
  }

  _update(data) {
    const speed = (data.pumpSpeed || 0) / 100;
    const running = !!data.pumpRunning;

    // pump color + status ring
    if (this.pumpMat) {
      const c = running ? 0x4a90d9 : 0x6a7a8a;
      if (this.pumpMat.color.getHex() !== c) this.pumpMat.color.setHex(c);
    }
    if (this.statusRing) {
      const m = this.statusRing.material;
      if (running) {
        m.color.setHex(0x66bb6a);
        m.emissive.setHex(0x66bb6a);
        m.emissiveIntensity = 0.6 + 0.4 * Math.sin(Date.now() / 300);
      } else {
        m.color.setHex(0x6a7a8a);
        m.emissive.setHex(0x000000);
        m.emissiveIntensity = 0;
      }
    }

    // pump rotation animation
    if (this.pumpGroup) {
      const target = running ? speed * 5 : 0;
      this.pumpGroup.children.forEach(child => {
        if (child.type === 'Mesh' && child.geometry.type === 'CylinderGeometry') {
          child.rotation.y += (target - child.rotation.y) * 0.1;
        }
      });
    }

    // valve color
    if (this.valveMat) {
      this.valveMat.color.setHex(data.valveOpen ? 0x66bb6a : 0xef5350);
    }

    // water level
    if (this.waterMesh) {
      const level = (data.tankLevel || 0) / 100;
      const maxH = 2.6;
      const h = Math.max(0.05, level * maxH);
      this.waterMesh.scale.y = h;
      this.waterMesh.position.y = (h * 0.5) + 0.05;
    }

    // flow particles
    const flowSpeed = running ? speed * 0.8 + 0.2 : 0.05;
    for (const ps of this.particleSystems) {
      const pos = ps.geo.attributes.position.array;
      for (let i = 0; i < ps.offsets.length; i++) {
        ps.offsets[i] = (ps.offsets[i] + flowSpeed * 0.008) % 1;
        const t = ps.offsets[i];
        const p = new THREE.Vector3().copy(ps.from).lerp(ps.to, t);
        pos[i * 3] = p.x;
        pos[i * 3 + 1] = p.y;
        pos[i * 3 + 2] = p.z;
      }
      ps.geo.attributes.position.needsUpdate = true;
      const opacity = running ? 0.8 : 0.15;
      ps.points.material.opacity += (opacity - ps.points.material.opacity) * 0.05;
    }
  }

  _animate() {
    requestAnimationFrame(() => this._animate());
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  dispose() {
    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
}

/* === DOM Bindings === */
class DomBindings {
  constructor(bus, ws) {
    this.bus = bus;
    this.ws = ws;
    this._unsubs = [];
    this._bindConnection();
    this._bindTelemetry();
    this._bindEvents();
    this._bindControls();
    this._bindAlerts();
  }

  _bindConnection() {
    const dot = document.getElementById('conn-dot');
    const label = document.getElementById('conn-label');
    const lat = document.getElementById('conn-latency');
    if (!dot || !label) return;

    this._unsubs.push(this.bus.on('connection:status', (s) => {
      dot.className = 'conn-dot ' + s;
      label.textContent = s.charAt(0).toUpperCase() + s.slice(1);
      document.getElementById('btn-start').disabled = s !== 'connected';
      document.getElementById('btn-stop').disabled = s !== 'connected';
    }));

    setInterval(() => {
      if (lat) {
        const l = this.ws.latency;
        lat.textContent = l ? `${l}ms` : '—';
      }
    }, 1000);
  }

  _bindTelemetry() {
    const fields = ['pumpSpeed', 'pressure', 'flowRate', 'tankLevel', 'temperature', 'power'];
    const elements = {};
    for (const f of fields) {
      const el = document.getElementById(`val-${f}`);
      if (el) elements[f] = el;
    }

    this._unsubs.push(this.bus.on('telemetry', (d) => {
      elements.pumpSpeed && (elements.pumpSpeed.textContent = d.pumpSpeed?.toFixed(1) ?? '—');
      elements.pressure && (elements.pressure.textContent = d.pressure?.toFixed(2) ?? '—');
      elements.flowRate && (elements.flowRate.textContent = d.flowRate?.toFixed(1) ?? '—');
      elements.tankLevel && (elements.tankLevel.textContent = d.tankLevel?.toFixed(1) ?? '—');
      elements.temperature && (elements.temperature.textContent = d.temperature?.toFixed(1) ?? '—');
      elements.power && (elements.power.textContent = d.power?.toFixed(1) ?? '—');

      const bar = document.getElementById('bar-speed');
      if (bar) { bar.style.width = `${d.pumpSpeed || 0}%`; bar.style.background = d.pumpRunning ? '#3b9eff' : '#6b829a'; }

      document.getElementById('slider-speed') && (document.getElementById('slider-speed').value = d.pumpSpeed || 0);
      const sv = document.getElementById('slider-val');
      if (sv) sv.textContent = `${Math.round(d.pumpSpeed || 0)}%`;
    }));
  }

  _bindEvents() {
    const log = document.getElementById('event-log');
    if (!log) return;
    this._unsubs.push(this.bus.on('event', (d) => {
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      const ts = new Date().toLocaleTimeString();
      entry.innerHTML = `<span class="log-ts">[${ts}]</span><span class="log-${d.level || 'info'}">${d.message}</span>`;
      log.appendChild(entry);
      log.scrollTop = log.scrollHeight;
      if (log.children.length > 100) log.removeChild(log.firstChild);
    }));
    this._unsubs.push(this.bus.on('alert', (d) => {
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      const ts = new Date().toLocaleTimeString();
      entry.innerHTML = `<span class="log-ts">[${ts}]</span><span class="log-alert">⚠ ${d.message}</span>`;
      log.appendChild(entry);
      log.scrollTop = log.scrollHeight;
    }));
  }

  _bindControls() {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const slider = document.getElementById('slider-speed');
    const btnValve = document.getElementById('btn-valve');

    if (btnStart) btnStart.addEventListener('click', () => this.ws.send('command', { action: 'start_pump' }));
    if (btnStop) btnStop.addEventListener('click', () => this.ws.send('command', { action: 'stop_pump' }));
    if (slider) {
      slider.addEventListener('input', (e) => {
        const v = parseInt(e.target.value);
        document.getElementById('slider-val').textContent = `${v}%`;
      });
      slider.addEventListener('change', (e) => {
        this.ws.sendThrottled('command', { action: 'set_speed', value: parseInt(e.target.value) }, 'speed', 150);
      });
    }
    if (btnValve) {
      this._unsubs.push(this.bus.on('telemetry', (d) => {
        btnValve.textContent = d.valveOpen ? 'Close Valve' : 'Open Valve';
        btnValve.className = `btn ${d.valveOpen ? 'danger' : 'ok'}`;
      }));
      btnValve.addEventListener('click', () => this.ws.send('command', { action: 'toggle_valve' }));
    }
  }

  _bindAlerts() {
    const overlay = document.getElementById('alert-overlay');
    const dismiss = document.getElementById('alert-dismiss');
    if (!overlay) return;
    this._unsubs.push(this.bus.on('alert', (d) => {
      document.getElementById('alert-title').textContent = d.severity === 'critical' ? 'CRITICAL ALERT' : 'Warning';
      document.getElementById('alert-msg').textContent = d.message;
      overlay.classList.add('visible');
    }));
    if (dismiss) dismiss.addEventListener('click', () => overlay.classList.remove('visible'));
  }

  destroy() { this._unsubs.forEach(u => u()); this._unsubs = []; }
}

/* === Boot === */
(async function boot() {
  const bus = new EventBus();
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocketClient(`${protocol}//${location.host}`, bus);
  ws.connect();

  const container = document.getElementById('scada-container');
  if (container && typeof THREE !== 'undefined') {
    new ScadaScene(container, bus);
  } else {
    console.error('THREE.js not loaded or container missing');
  }

  new DomBindings(bus, ws);
})();
