/// <reference types="astro/client" />
import type { Publication, ReadBucket } from "./lib/publication"
declare global {
  namespace App {
    interface Locals {
      publication: Publication
    }
  }
  namespace Cloudflare {
    interface Env {
      DAILY_CONTENT: ReadBucket
    }
  }
  const __DAILY_CODE_REVISION__: string
}
