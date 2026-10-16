import { lstat, readFile, realpath } from "node:fs/promises"
import { S3Client } from "@aws-sdk/client-s3"
import { S3Store, inspect, publishBundle, verifyBundleObjects } from "./r2.ts"
import { parseEdition, validateRevision } from "./parser.ts"
import { basename, dirname, resolve, sep } from "node:path"
import { fileURLToPath } from "node:url"

const [action, path, extra] = process.argv.slice(2)
if (action === "validate") {
  if (!path) throw new Error("candidate path is required")
  const candidate = parseEdition({ filename: basename(path), text: await readFile(path, "utf8") })
  if (extra)
    validateRevision(
      parseEdition({ filename: basename(path), text: await readFile(extra, "utf8") }),
      candidate,
    )
} else {
  try {
    const configPath = resolve(process.env.PUBLISH_R2_CONFIG ?? "")
    const stat = await lstat(configPath)
    if (
      !stat.isFile() ||
      stat.isSymbolicLink() ||
      (stat.mode & 0o177) !== 0 ||
      (await realpath(configPath)) !== configPath
    )
      throw new Error("private S3 configuration must be a regular file with mode 0600 or stricter")
    const repository = resolve(dirname(fileURLToPath(import.meta.url)), "../../..")
    const forbidden = [
      repository,
      process.env.PUBLISH_VAULT_PUBLIC ?? "/Users/skypawalker/Dropbox/Obsidian/public",
      process.env.PUBLISH_R2_VAULT_ROOT,
    ].filter((path): path is string => typeof path === "string")
    if (
      forbidden.some(
        (root) => configPath === resolve(root) || configPath.startsWith(resolve(root) + sep),
      )
    )
      throw new Error("private S3 configuration must stay outside repository and vault")
    const config: unknown = JSON.parse(await readFile(configPath, "utf8"))
    if (
      !config ||
      typeof config !== "object" ||
      !("accountId" in config) ||
      config.accountId !== "1688bfec49a43a217df10ed33b86e300" ||
      !("bucket" in config) ||
      typeof config.bucket !== "string" ||
      !config.bucket ||
      !("accessKeyId" in config) ||
      typeof config.accessKeyId !== "string" ||
      !("secretAccessKey" in config) ||
      typeof config.secretAccessKey !== "string"
    )
      throw new Error("invalid private R2 configuration")
    const endpoint =
      "endpoint" in config
        ? config.endpoint
        : `https://${config.accountId}.r2.cloudflarestorage.com`
    if (typeof endpoint !== "string") throw new Error("invalid R2 endpoint")
    const parsedEndpoint = new URL(endpoint)
    if (
      endpoint !== `https://${config.accountId}.r2.cloudflarestorage.com` &&
      !(
        parsedEndpoint.protocol === "http:" &&
        parsedEndpoint.hostname === "127.0.0.1" &&
        parsedEndpoint.pathname === "/" &&
        !parsedEndpoint.username &&
        !parsedEndpoint.password
      )
    )
      throw new Error("R2 endpoint must match the configured account or the isolated local fixture")
    const store = new S3Store(
      new S3Client({
        region: "auto",
        endpoint,
        forcePathStyle: true,
        credentials: { accessKeyId: config.accessKeyId, secretAccessKey: config.secretAccessKey },
        requestChecksumCalculation: "WHEN_REQUIRED",
        responseChecksumValidation: "WHEN_REQUIRED",
        maxAttempts: 1,
      }),
      config.bucket,
    )
    if (action === "inspect") process.stdout.write(JSON.stringify(await inspect(store)) + "\n")
    else if (action === "objects" && path && extra)
      process.stdout.write(
        JSON.stringify(await verifyBundleObjects(store, path, JSON.parse(extra))) + "\n",
      )
    else if (action === "publish" && path && extra)
      process.stdout.write(
        JSON.stringify(await publishBundle(store, path, JSON.parse(extra))) + "\n",
      )
    else
      throw new Error(
        "usage: r2-cli.ts inspect | publish BUNDLE EXPECTED_JSON | validate CANDIDATE [PREVIOUS]",
      )
  } catch {
    // JSON parser and SDK diagnostics can contain input fragments. Keep credentials off stderr.
    process.stderr.write(
      "R2 operation failed. Inspect private configuration, credentials, and expected head.\n",
    )
    process.exitCode = 1
  }
}
