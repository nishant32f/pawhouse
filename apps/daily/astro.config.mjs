import { defineConfig } from "astro/config"
import cloudflare from "@astrojs/cloudflare"
import { execFileSync } from "node:child_process"

export default defineConfig({
  site: "https://daily.nishantkhurana.me",
  output: "server",
  adapter: cloudflare({ imageService: "passthrough", remoteBindings: false }),
  session: false,
  trailingSlash: "always",
  vite: {
    define: {
      __DAILY_CODE_REVISION__: JSON.stringify(
        execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
      ),
    },
  },
})
