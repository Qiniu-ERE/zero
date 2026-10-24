// 坦克大战 2026 网页版外壳：自动启动 spx 导出的游戏、按 4:3 铺满屏幕、触屏虚拟按键、PWA。
// 游戏本体是 runner.html（spx exportweb 的产物），这里只负责外面这一层，不改游戏代码。
'use strict'

const frame = document.getElementById('game')
const startBtn = document.getElementById('startBtn')
const msg = document.getElementById('msg')
const bar = document.getElementById('bar')
const pad = document.getElementById('pad')
const touch = matchMedia('(pointer: coarse)').matches || new URLSearchParams(location.search).has('pad')

// ---------- 布局：游戏画面 4:3，横屏时虚拟按键放在两侧，竖屏时放在下面 ----------
function layout() {
	const W = window.innerWidth
	const H = window.innerHeight
	const landscape = W >= H
	let gw, gh, gx, gy
	if (!touch) { // 电脑：画面尽量大，居中
		gw = Math.min(W, H * 4 / 3); gh = gw * 3 / 4
		gx = (W - gw) / 2; gy = (H - gh) / 2
	} else if (landscape) { // 横屏：两侧留给按键
		gh = H; gw = gh * 4 / 3
		const side = Math.max(160, (W - gw) / 2)
		if (W - 2 * side < gw) { gw = W - 2 * side; gh = gw * 3 / 4 }
		gx = (W - gw) / 2; gy = (H - gh) / 2
		placeSides(0, 0, gx, H, gx + gw, 0, W - gx - gw, H)
	} else { // 竖屏：上面是画面，下面是按键
		gw = W; gh = gw * 3 / 4
		gx = 0; gy = Math.max(0, Math.min((H - gh) * 0.25, 60))
		const top = gy + gh
		placeSides(0, top, W / 2, H - top, W / 2, top, W / 2, H - top)
	}
	Object.assign(frame.style, { left: gx + 'px', top: gy + 'px', width: gw + 'px', height: gh + 'px' })
}

function placeSides(lx, ly, lw, lh, rx, ry, rw, rh) {
	const left = pad.querySelector('.left')
	const right = pad.querySelector('.right')
	Object.assign(left.style, { left: lx + 'px', top: ly + 'px', width: lw + 'px', height: lh + 'px' })
	Object.assign(right.style, { left: rx + 'px', top: ry + 'px', width: rw + 'px', height: rh + 'px' })
	const size = Math.max(110, Math.min(lw * 0.85, lh * (document.body.classList.contains('coop') ? 0.5 : 0.7), 180))
	pad.style.setProperty('--dpad', size + 'px')
	pad.style.setProperty('--fire', Math.round(size * 0.62) + 'px')
}

window.addEventListener('resize', layout)
layout()

// ---------- 启动游戏 ----------
function runnerReady() {
	return new Promise((resolve) => {
		const w = frame.contentWindow
		if (w && typeof w.initEngine === 'function' && w.document.readyState === 'complete') return resolve(w)
		frame.addEventListener('load', () => resolve(frame.contentWindow), { once: true })
	})
}

async function start() {
	startBtn.disabled = true
	document.getElementById('progress').hidden = false
	try {
		msg.textContent = '正在加载引擎…'
		const w = await runnerReady()
		w.addEventListener('onProgress', (e) => { bar.style.width = Math.round(e.detail.progress * 60) + '%' })
		w.spxConfigureRunner({})
		await w.initEngine(null, {})
		msg.textContent = '正在加载游戏…'
		bar.style.width = '70%'
		const res = await fetch('game.zip')
		if (!res.ok) throw new Error('game.zip ' + res.status)
		const unzipped = fflate.unzipSync(new Uint8Array(await res.arrayBuffer()))
		const files = {}
		for (const [path, data] of Object.entries(unzipped)) {
			if (!path.endsWith('/')) files[path] = { lastModified: Date.now(), content: data.buffer }
		}
		bar.style.width = '85%'
		await w.initGame(files)
		await w.startGame({ input: w.spxCreateInputSession() })
		bar.style.width = '100%'
		document.body.classList.add('playing')
		if (touch) pad.hidden = false
		layout()
		focusGame()
	} catch (err) {
		console.error(err)
		msg.textContent = '启动失败：' + (err && err.message ? err.message : err) + '（请刷新重试）'
		startBtn.disabled = false
	}
}

startBtn.addEventListener('click', start)

// 让游戏画布拿到键盘焦点
function focusGame() {
	const w = frame.contentWindow
	frame.focus()
	if (w) {
		w.focus()
		const canvas = w.document.getElementById('game-canvas')
		if (canvas) canvas.focus()
	}
}

// 电脑上：焦点不在游戏里时（比如点到了画面外的黑边），把键盘事件转发给游戏
for (const type of ['keydown', 'keyup']) {
	document.addEventListener(type, (e) => {
		if (!document.body.classList.contains('playing')) return
		const w = frame.contentWindow
		const canvas = w && w.document.getElementById('game-canvas')
		if (!canvas) return
		canvas.dispatchEvent(new w.KeyboardEvent(type, { code: e.code, key: e.key, keyCode: e.keyCode, which: e.which, repeat: e.repeat, bubbles: true, cancelable: true }))
		e.preventDefault()
	})
}
document.addEventListener('pointerdown', (e) => { if (e.target === document.body) focusGame() })

// ---------- 虚拟按键：向游戏画布发送键盘事件 ----------
const KEYS = {
	KeyW: ['w', 87], KeyA: ['a', 65], KeyS: ['s', 83], KeyD: ['d', 68], KeyJ: ['j', 74], KeyT: ['t', 84],
	ArrowUp: ['ArrowUp', 38], ArrowDown: ['ArrowDown', 40], ArrowLeft: ['ArrowLeft', 37], ArrowRight: ['ArrowRight', 39],
	Enter: ['Enter', 13], Escape: ['Escape', 27],
}

function sendKey(code, down) {
	const w = frame.contentWindow
	const canvas = w && w.document.getElementById('game-canvas')
	if (!canvas) return
	const [key, keyCode] = KEYS[code]
	canvas.dispatchEvent(new w.KeyboardEvent(down ? 'keydown' : 'keyup', { code, key, keyCode, which: keyCode, bubbles: true, cancelable: true }))
}

// 方向键盘：按手指相对圆心的方向决定按哪个键，手指滑动时切换
pad.querySelectorAll('.dpad').forEach((el) => {
	const [up, down, left, right] = el.dataset.keys.split(',')
	let held = null
	let pointer = null
	const set = (k) => {
		if (k === held) return
		if (held) sendKey(held, false)
		held = k
		if (held) sendKey(held, true)
		el.classList.toggle('active', !!held)
	}
	const update = (e) => {
		const r = el.getBoundingClientRect()
		const dx = e.clientX - (r.left + r.width / 2)
		const dy = e.clientY - (r.top + r.height / 2)
		if (Math.hypot(dx, dy) < r.width * 0.12) return set(null) // 中心留一点空，不按任何方向
		set(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? right : left) : (dy > 0 ? down : up))
	}
	el.addEventListener('pointerdown', (e) => { pointer = e.pointerId; el.setPointerCapture(pointer); update(e); e.preventDefault() })
	el.addEventListener('pointermove', (e) => { if (e.pointerId === pointer) update(e) })
	const end = (e) => { if (e.pointerId === pointer) { pointer = null; set(null) } }
	el.addEventListener('pointerup', end)
	el.addEventListener('pointercancel', end)
})

// 普通按钮：按下发 keydown，松开发 keyup（支持多点触控：可以一边移动一边开火）
pad.querySelectorAll('button[data-key]').forEach((el) => {
	const code = el.dataset.key
	el.addEventListener('pointerdown', (e) => { el.setPointerCapture(e.pointerId); el.classList.add('down'); sendKey(code, true); e.preventDefault() })
	const up = () => { if (el.classList.contains('down')) { el.classList.remove('down'); sendKey(code, false) } }
	el.addEventListener('pointerup', up)
	el.addEventListener('pointercancel', up)
})

document.getElementById('coopBtn').addEventListener('click', (e) => {
	document.body.classList.toggle('coop')
	e.currentTarget.classList.toggle('on', document.body.classList.contains('coop'))
	layout()
})

const fsBtn = document.getElementById('fsBtn')
if (!document.documentElement.requestFullscreen) fsBtn.hidden = true // iPhone 的 Safari 不支持，用“添加到主屏幕”代替
fsBtn.addEventListener('click', () => {
	if (document.fullscreenElement) document.exitFullscreen()
	else document.documentElement.requestFullscreen({ navigationUI: 'hide' }).then(() => screen.orientation && screen.orientation.lock && screen.orientation.lock('landscape').catch(() => {}))
})

// ---------- PWA：离线缓存、安装提示 ----------
if ('serviceWorker' in navigator && location.protocol === 'https:') {
	navigator.serviceWorker.register('sw.js').catch((e) => console.warn('service worker', e))
}
const standalone = matchMedia('(display-mode: standalone), (display-mode: fullscreen)').matches || navigator.standalone
if (touch && !standalone) {
	const ios = /iPhone|iPad|iPod/.test(navigator.userAgent)
	document.getElementById('installHint').textContent = ios
		? '提示：在 Safari 里点“分享”→“添加到主屏幕”，以后像 App 一样全屏打开。'
		: '提示：在浏览器菜单里选“安装应用”或“添加到主屏幕”，以后像 App 一样全屏打开。'
}
