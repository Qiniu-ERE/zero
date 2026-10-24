// 离线缓存：第一次在线打开后，游戏文件都缓存下来，之后断网也能玩。
// 缓存名带版本号（打包时替换），发布新版本后旧缓存自动清掉。
const CACHE = 'tankbattle-@VERSION@'

self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys()
			.then((keys) => Promise.all(keys.filter((k) => k.startsWith('tankbattle-') && k !== CACHE).map((k) => caches.delete(k))))
			.then(() => self.clients.claim())
	)
})

self.addEventListener('fetch', (event) => {
	const req = event.request
	if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return
	event.respondWith(
		caches.open(CACHE).then(async (cache) => {
			const hit = await cache.match(req)
			if (hit) return hit
			const res = await fetch(req)
			if (res.ok) cache.put(req, res.clone())
			return res
		})
	)
})
