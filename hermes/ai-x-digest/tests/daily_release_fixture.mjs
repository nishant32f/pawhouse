// Isolated HTTP fixture for the built SSR handler and accepted local R2 objects.
import { readFileSync, readdirSync } from "node:fs"
import { join, resolve } from "node:path"
import { pathToFileURL } from "node:url"
import { createServer } from "node:http"
const [app, artifact, bundle] = process.argv.slice(2)
const { Miniflare } = await import(
  pathToFileURL(join(app, "node_modules/miniflare/dist/src/index.js"))
)
const server = join(artifact, "server")
const config = JSON.parse(readFileSync(join(server, "wrangler.json"), "utf8"))
const modules = {}
for (const file of readdirSync(server, { recursive: true, encoding: "utf8" })) {
  if (/\.m?js$/.test(file))
    modules[file] = { type: "esm", contents: readFileSync(join(server, file), "utf8") }
}
const worker = new Miniflare({
  workers: [
    {
      config: {
        name: "daily-release-fixture",
        compatibilityDate: config.compatibility_date,
        compatibilityFlags: config.compatibility_flags,
        manifest: { mainModule: config.main, modulesRoot: server, modules },
        env: {
          DAILY_CONTENT: { type: "r2", name: "daily-release-fixture", dev: { remote: false } },
          ASSETS: { type: "assets" },
        },
        assets: {
          directory: resolve(server, config.assets.directory),
          notFoundHandling: "404-page",
          hasUserWorker: true,
        },
      },
    },
  ],
})
const bucket = await worker.getR2Bucket("DAILY_CONTENT")
const metadata = JSON.parse(readFileSync(join(bundle, "bundle.json"), "utf8"))
for (const object of metadata.objects)
  await bucket.put(object.key, readFileSync(join(bundle, object.key)))
await bucket.put("v1/head.json", readFileSync(join(bundle, "v1/head.json")))
const http = createServer(async (request, response) => {
  try {
    const result = await worker.dispatchFetch("https://daily.nishantkhurana.me" + request.url, {
      method: request.method,
      headers: request.headers,
    })
    response.writeHead(result.status, Object.fromEntries(result.headers.entries()))
    if (result.body) for await (const chunk of result.body) response.write(chunk)
    response.end()
  } catch (error) {
    response.writeHead(500)
    response.end(String(error))
  }
})
http.listen(0, "127.0.0.1", () =>
  process.stdout.write("http://127.0.0.1:" + http.address().port + "\n"),
)
async function stop() {
  http.close()
  await worker.dispose()
  process.exit()
}
process.on("SIGINT", stop)
process.on("SIGTERM", stop)
