// 网页外壳 tools/export/web/play.js 的测试（W01~W04），见 docs/v4/TEST_PLAN.md 第 3.7 节
//
// play.js 直接操作网页元素，这里不改它：在 Node 的 vm 里给它一个最小的假网页环境（几个元素、事件、
// 游戏画布），运行原文件，然后模拟手指按下 / 滑动 / 松开，检查发给游戏画布的键盘事件和画面布局。
// 运行：node --test tests/web/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import vm from 'node:vm'

const SRC = readFileSync(fileURLToPath(new URL('../../tools/export/web/play.js', import.meta.url)), 'utf8')

class ClassList {
	constructor() { this.set = new Set() }
	add(c) { this.set.add(c) }
	remove(c) { this.set.delete(c) }
	contains(c) { return this.set.has(c) }
	toggle(c, force) {
		const on = force === undefined ? !this.set.has(c) : force
		on ? this.set.add(c) : this.set.delete(c)
		return on
	}
}

class El {
	constructor(name, props = {}) {
		this.name = name
		this.listeners = {}
		this.style = { setProperty(k, v) { this[k] = v } }
		this.classList = new ClassList()
		this.dataset = {}
		this.hidden = false
		this.rect = { left: 0, top: 0, width: 100, height: 100 }
		this.parts = {}
		Object.assign(this, props)
	}
	addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn) }
	emit(type, e = {}) {
		const ev = { preventDefault() {}, currentTarget: this, target: this, ...e }
		for (const fn of this.listeners[type] || []) fn(ev)
	}
	getBoundingClientRect() { return this.rect }
	setPointerCapture() {}
	focus() {}
	querySelector(sel) { return this.parts[sel] }
	querySelectorAll(sel) { return this.parts[sel] || [] }
}

// 造一个网页环境并运行 play.js。touch：是不是触屏设备
function load({ touch = false, width = 1280, height = 960 } = {}) {
	const sent = [] // 发给游戏画布的键盘事件：[type, code]
	const canvas = new El('canvas', { dispatchEvent(e) { sent.push([e.type, e.code]) } })
	const gameWindow = {
		document: { getElementById: (id) => (id === 'game-canvas' ? canvas : null), readyState: 'complete' },
		KeyboardEvent: class { constructor(type, init) { this.type = type; Object.assign(this, init) } },
		focus() {},
		addEventListener() {},
	}
	const frame = new El('game', { contentWindow: gameWindow })
	const dpad1 = new El('dpad1', { dataset: { keys: 'KeyW,KeyS,KeyA,KeyD' } })
	const dpad2 = new El('dpad2', { dataset: { keys: 'ArrowUp,ArrowDown,ArrowLeft,ArrowRight' } })
	for (const d of [dpad1, dpad2]) d.rect = { left: 0, top: 0, width: 100, height: 100 } // 圆心 (50, 50)
	const btn = (key) => new El('btn-' + key, { dataset: { key } })
	const buttons = { fire: btn('KeyJ'), fire1: btn('KeyJ'), fire2: btn('Enter'), pause: btn('Escape'), theme: btn('KeyT') }
	const left = new El('left')
	const right = new El('right')
	const pad = new El('pad', { hidden: true })
	pad.parts = { '.left': left, '.right': right, '.dpad': [dpad1, dpad2], 'button[data-key]': Object.values(buttons) }
	const els = {
		game: frame, pad, startBtn: new El('startBtn'), msg: new El('msg'), bar: new El('bar'), progress: new El('progress'),
		coopBtn: new El('coopBtn'), fsBtn: new El('fsBtn'), installHint: new El('installHint'),
	}
	const body = new El('body')
	const document = {
		getElementById: (id) => els[id],
		addEventListener() {},
		body,
		documentElement: { requestFullscreen() { return Promise.resolve() } },
	}
	const window = { innerWidth: width, innerHeight: height, addEventListener() {} }
	const ctx = vm.createContext({
		document, window, location: { search: '', protocol: 'http:' }, navigator: { userAgent: 'node' },
		matchMedia: (q) => ({ matches: q.includes('pointer: coarse') ? touch : false }),
		URLSearchParams, console, Promise, Math, Object, screen: {},
	})
	vm.runInContext(SRC, ctx)
	return { ctx, window, frame, sent, dpad1, dpad2, buttons, body, els, left, right }
}

const at = (x, y, pointerId = 1) => ({ clientX: x, clientY: y, pointerId })
const box = (s) => ({ x: parseFloat(s.left), y: parseFloat(s.top), w: parseFloat(s.width), h: parseFloat(s.height) })

test('W01 方向键：按下、滑动换方向、松开', () => {
	const g = load({ touch: true })
	g.dpad1.emit('pointerdown', at(90, 50)) // 圆心右边
	assert.deepEqual(g.sent, [['keydown', 'KeyD']])
	g.dpad1.emit('pointermove', at(50, 10)) // 滑到上面：先松开右，再按上
	assert.deepEqual(g.sent.slice(1), [['keyup', 'KeyD'], ['keydown', 'KeyW']])
	g.dpad1.emit('pointermove', at(50, 15)) // 还在上面：不重复发
	assert.equal(g.sent.length, 3)
	g.dpad1.emit('pointerup', at(50, 15))
	assert.deepEqual(g.sent.at(-1), ['keyup', 'KeyW'])
	assert.equal(g.dpad1.classList.contains('active'), false)
})

test('W01 方向键：四个方向和中心空区', () => {
	const g = load({ touch: true })
	const dirs = [[50, 5, 'KeyW'], [50, 95, 'KeyS'], [5, 50, 'KeyA'], [95, 50, 'KeyD']]
	for (const [x, y, key] of dirs) {
		g.sent.length = 0
		g.dpad1.emit('pointerdown', at(x, y))
		g.dpad1.emit('pointerup', at(x, y))
		assert.deepEqual(g.sent, [['keydown', key], ['keyup', key]], key)
	}
	g.sent.length = 0
	g.dpad1.emit('pointerdown', at(52, 51)) // 圆心附近：不按任何方向
	assert.deepEqual(g.sent, [])
})

test('W02 多点触控：一边移动一边开火，互不影响', () => {
	const g = load({ touch: true })
	g.dpad1.emit('pointerdown', at(50, 5, 1)) // 手指 1 按“上”
	g.buttons.fire.emit('pointerdown', at(0, 0, 2)) // 手指 2 按开火
	g.dpad1.emit('pointermove', at(50, 4, 2)) // 别的手指的移动不影响方向键
	assert.deepEqual(g.sent, [['keydown', 'KeyW'], ['keydown', 'KeyJ']])
	g.buttons.fire.emit('pointerup', at(0, 0, 2))
	assert.deepEqual(g.sent.at(-1), ['keyup', 'KeyJ'])
	g.dpad1.emit('pointerup', at(50, 5, 2)) // 不是按方向键的那根手指：方向键还按着
	assert.equal(g.sent.filter(([t]) => t === 'keyup').length, 1)
	g.dpad1.emit('pointerup', at(50, 5, 1))
	assert.deepEqual(g.sent.at(-1), ['keyup', 'KeyW'])
})

test('W02 pointercancel（来电、切到后台）时松开所有按着的键', () => {
	const g = load({ touch: true })
	g.dpad1.emit('pointerdown', at(95, 50, 1))
	g.buttons.fire.emit('pointerdown', at(0, 0, 2))
	g.dpad1.emit('pointercancel', at(95, 50, 1))
	g.buttons.fire.emit('pointercancel', at(0, 0, 2))
	assert.deepEqual(g.sent, [['keydown', 'KeyD'], ['keydown', 'KeyJ'], ['keyup', 'KeyD'], ['keyup', 'KeyJ']])
	g.buttons.fire.emit('pointercancel') // 已经松开了：不再重复发 keyup
	assert.equal(g.sent.length, 4)
})

test('W03 双人按键：2P 方向键发方向键，2P 开火发 Enter，按钮切换双人布局', () => {
	const g = load({ touch: true })
	g.dpad2.emit('pointerdown', at(5, 50))
	g.dpad2.emit('pointerup', at(5, 50))
	g.buttons.fire2.emit('pointerdown')
	g.buttons.fire2.emit('pointerup')
	g.buttons.pause.emit('pointerdown')
	g.buttons.pause.emit('pointerup')
	assert.deepEqual(g.sent, [['keydown', 'ArrowLeft'], ['keyup', 'ArrowLeft'], ['keydown', 'Enter'], ['keyup', 'Enter'], ['keydown', 'Escape'], ['keyup', 'Escape']])
	g.els.coopBtn.emit('click')
	assert.equal(g.body.classList.contains('coop'), true)
	assert.equal(g.els.coopBtn.classList.contains('on'), true)
	g.els.coopBtn.emit('click')
	assert.equal(g.body.classList.contains('coop'), false)
	assert.equal(g.els.coopBtn.classList.contains('on'), false)
})

test('W04 布局：各种屏幕下画面都是 4:3，不超出屏幕', () => {
	const cases = [
		{ touch: false, width: 1280, height: 960, name: '电脑 4:3' },
		{ touch: false, width: 1920, height: 1080, name: '电脑 16:9' },
		{ touch: true, width: 844, height: 390, name: '手机横屏' },
		{ touch: true, width: 390, height: 844, name: '手机竖屏' },
		{ touch: true, width: 2400, height: 1080, name: '超宽屏' },
		{ touch: true, width: 1024, height: 768, name: '平板横屏' },
	]
	for (const c of cases) {
		const g = load(c)
		const f = box(g.frame.style)
		assert.ok(Math.abs(f.w / f.h - 4 / 3) < 0.01, `${c.name}：画面比例 ${f.w}×${f.h}`)
		assert.ok(f.x >= -0.5 && f.y >= -0.5 && f.x + f.w <= c.width + 0.5 && f.y + f.h <= c.height + 0.5, `${c.name}：画面超出屏幕`)
		if (c.touch && c.width >= c.height) { // 横屏：两侧按键区不和画面重叠，宽度不小于 160
			const l = box(g.left.style)
			const r = box(g.right.style)
			assert.ok(l.x + l.w <= f.x + 0.5 && r.x >= f.x + f.w - 0.5, `${c.name}：按键区和画面重叠`)
			assert.ok(l.w >= 159.5 && r.w >= 159.5, `${c.name}：按键区太窄（${l.w}、${r.w}）`)
		}
		if (c.touch && c.width < c.height) { // 竖屏：按键区在画面下面
			assert.ok(box(g.left.style).y >= f.y + f.h - 0.5, `${c.name}：按键区应该在画面下面`)
		}
	}
})
