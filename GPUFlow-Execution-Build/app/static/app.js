(() => {
  const $ = (id) => document.getElementById(id);
  const state = { token: sessionStorage.getItem('gpuflow_token') || '', socket: null, clientId: '', connected: false, room: 'gpuflow-lab', myName: 'Device' };

  const setConnection = (connected, label) => {
    state.connected = connected;
    $('connectionPill').classList.toggle('connected', connected);
    $('connectionText').textContent = label || (connected ? 'Connected' : 'Not connected');
    $('bridgeStatus').textContent = connected ? 'Bridge is connected' : 'Bridge is idle';
    $('bridgeHelp').textContent = connected ? `Connected to room “${state.room}”.` : 'Use the same room name on both devices.';
    $('connectBtn').innerHTML = connected ? 'Disconnect <span>×</span>' : 'Connect <span>→</span>';
    $('headerConnectBtn').innerHTML = connected ? 'Connected <span>✓</span>' : 'Connect device <span>↗</span>';
    $('connectBtn').classList.toggle('button-dark', !connected);
    $('connectBtn').classList.toggle('button-primary', connected);
  };

  const toast = (message) => {
    const el = $('toast');
    el.textContent = message;
    el.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.remove('show'), 2600);
  };

  const showAuthError = (message) => { $('authError').textContent = message; };

  const formatTime = (iso) => {
    try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
    catch { return ''; }
  };

  const addFeedEvent = ({ icon = '·', type = 'system', author = 'GPUFlow', text = '', time = '', badge = '' }) => {
    const feed = $('feed');
    const empty = feed.querySelector('.feed-empty');
    if (empty) empty.remove();
    const row = document.createElement('div');
    row.className = 'feed-event';
    const marker = document.createElement('div');
    marker.className = `feed-marker ${type}`;
    marker.textContent = icon;
    const body = document.createElement('div');
    body.className = 'feed-body';
    const topline = document.createElement('div');
    topline.className = 'feed-topline';
    const authorEl = document.createElement('span');
    authorEl.className = 'feed-author';
    authorEl.textContent = author;
    const timeEl = document.createElement('span');
    timeEl.className = 'feed-time';
    timeEl.textContent = time ? formatTime(time) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    topline.append(authorEl, timeEl);
    const textEl = document.createElement('div');
    textEl.className = 'feed-text';
    textEl.textContent = text;
    body.append(topline, textEl);
    if (badge) {
      const badgeEl = document.createElement('span');
      badgeEl.className = 'feed-route-badge';
      badgeEl.textContent = badge;
      body.append(badgeEl);
    }
    row.append(marker, body);
    feed.append(row);
    while (feed.children.length > 80) feed.removeChild(feed.firstElementChild);
    feed.scrollTop = feed.scrollHeight;
  };

  const renderMembers = (members = []) => {
    $('deviceCount').innerHTML = `${members.length}<span class="metric-unit"> / room</span>`;
    $('membersCountLabel').textContent = `${members.length} ${members.length === 1 ? 'device' : 'devices'}`;
    const list = $('membersList');
    list.replaceChildren();
    if (!members.length) {
      const empty = document.createElement('div');
      empty.className = 'empty-members';
      empty.textContent = 'No devices connected yet. Connect this device to begin.';
      list.append(empty);
      return;
    }
    for (const member of members) {
      const row = document.createElement('div');
      row.className = 'member-row';
      const avatar = document.createElement('div');
      avatar.className = 'member-avatar';
      avatar.textContent = (member.name || 'D').trim().slice(0, 1).toUpperCase();
      const meta = document.createElement('div');
      const name = document.createElement('div');
      name.className = 'member-name';
      name.textContent = member.name || 'Device';
      const sub = document.createElement('div');
      sub.className = 'member-sub';
      sub.textContent = member.id === state.clientId ? 'This device' : `Device · ${member.id}`;
      meta.append(name, sub);
      const online = document.createElement('div');
      online.className = 'member-online';
      const dot = document.createElement('i');
      online.append(dot, document.createTextNode('Online'));
      row.append(avatar, meta, online);
      list.append(row);
    }
  };

  const showRoute = (event) => {
    const result = event.result || {};
    const host = $('routeResult');
    host.replaceChildren();
    const wrap = document.createElement('div');
    wrap.className = 'result-live';
    const icon = document.createElement('div');
    icon.className = 'result-tier-icon';
    icon.textContent = '⤳';
    const detail = document.createElement('div');
    detail.className = 'result-detail';
    const label = document.createElement('div');
    label.className = 'result-label';
    label.textContent = `SIMULATED DECISION · ${event.from || 'DEVICE'}`;
    const tier = document.createElement('div');
    tier.className = 'result-tier';
    tier.textContent = result.tier || 'Unknown profile';
    const reason = document.createElement('div');
    reason.className = 'result-reason';
    reason.textContent = result.reason || 'No decision details available.';
    const meta = document.createElement('div');
    meta.className = 'result-meta';
    meta.textContent = result.notice || 'Simulation only.';
    detail.append(label, tier, reason, meta);
    wrap.append(icon, detail);
    host.append(wrap);
    addFeedEvent({ icon: '⤳', type: 'route', author: event.from || 'Device', text: (event.text || 'Workload test').slice(0, 150), time: event.server_time, badge: result.tier || 'Simulated route' });
  };

  const handleEvent = (event) => {
    if (event.type === 'welcome') {
      state.clientId = event.client_id;
      state.room = event.room;
      $('activeRoomMetric').textContent = event.room;
      setConnection(true, 'Connected');
      toast(`Connected to ${event.room}`);
    } else if (event.type === 'presence') {
      renderMembers(event.members || []);
    } else if (event.type === 'system') {
      addFeedEvent({ icon: '·', type: 'system', author: 'Room activity', text: event.text || '', time: event.server_time });
    } else if (event.type === 'chat') {
      addFeedEvent({ icon: '✉', type: 'chat', author: event.from || 'Device', text: event.text || '', time: event.server_time });
    } else if (event.type === 'route') {
      showRoute(event);
    } else if (event.type === 'error') {
      toast(event.text || 'An error occurred');
    }
  };

  const connect = () => {
    if (!state.token) {
      $('authOverlay').style.display = 'grid';
      return;
    }
    if (state.socket && (state.socket.readyState === WebSocket.OPEN || state.socket.readyState === WebSocket.CONNECTING)) {
      state.socket.close(1000, 'User disconnected');
      return;
    }
    const room = $('roomInput').value.trim() || 'gpuflow-lab';
    const name = $('nameInput').value.trim() || `Device ${Math.floor(10 + Math.random() * 90)}`;
    state.room = room;
    state.myName = name;
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const query = new URLSearchParams({ room, name, token: state.token });
    const socket = new WebSocket(`${scheme}//${location.host}/ws?${query.toString()}`);
    state.socket = socket;
    setConnection(false, 'Connecting…');
    $('activeRoomMetric').textContent = room;
    socket.onopen = () => setConnection(true, 'Connected');
    socket.onmessage = (message) => {
      try { handleEvent(JSON.parse(message.data)); } catch { toast('Could not read a server event'); }
    };
    socket.onerror = () => toast('Connection error. Check your Wi-Fi and firewall settings.');
    socket.onclose = (event) => {
      state.socket = null;
      state.clientId = '';
      setConnection(false, event.code === 4401 ? 'Unlock required' : 'Not connected');
      renderMembers([]);
      if (event.code === 4401) {
        sessionStorage.removeItem('gpuflow_token');
        state.token = '';
        $('authOverlay').style.display = 'grid';
        showAuthError('Your session expired. Please unlock again.');
      }
    };
  };

  const send = (payload) => {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      toast('Connect this device to the room first.');
      return false;
    }
    state.socket.send(JSON.stringify(payload));
    return true;
  };

  $('unlockForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    showAuthError('');
    const button = $('unlockForm').querySelector('button');
    button.disabled = true;
    button.textContent = 'Checking…';
    try {
      const response = await fetch('/api/unlock', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: $('passwordInput').value })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Access denied');
      state.token = data.token;
      sessionStorage.setItem('gpuflow_token', data.token);
      $('authOverlay').style.display = 'none';
      $('passwordInput').value = '';
      showAuthError('');
      toast('Workspace unlocked');
      connect();
    } catch (error) {
      showAuthError(error.message || 'Could not unlock GPUFlow');
    } finally {
      button.disabled = false;
      button.innerHTML = 'Unlock GPUFlow <span>→</span>';
    }
  });

  $('connectBtn').addEventListener('click', connect);
  $('headerConnectBtn').addEventListener('click', () => {
    document.getElementById('devices').scrollIntoView({ behavior: 'smooth', block: 'center' });
    if (!state.connected) connect();
  });

  $('chatForm').addEventListener('submit', (event) => {
    event.preventDefault();
    const input = $('chatInput');
    const text = input.value.trim();
    if (!text) return;
    if (send({ type: 'chat', text })) input.value = '';
  });

  $('routeBtn').addEventListener('click', () => {
    const text = $('promptInput').value.trim();
    if (!text) { toast('Write a test prompt first.'); $('promptInput').focus(); return; }
    send({ type: 'route', text, mode: $('modeSelect').value });
  });

  $('promptInput').addEventListener('input', () => {
    $('promptCount').textContent = `${$('promptInput').value.length} / 4000`;
  });

  $('roomInput').addEventListener('change', () => {
    const room = $('roomInput').value.trim() || 'gpuflow-lab';
    $('activeRoomMetric').textContent = room;
    if (state.connected) toast('Disconnect, then reconnect to change rooms.');
  });

  if (state.token) {
    $('authOverlay').style.display = 'none';
    connect();
  } else {
    setConnection(false, 'Not connected');
  }
})();
