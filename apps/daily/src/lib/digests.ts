import { execFile } from "node:child_process"
import { promisify } from "node:util"
import {
  parseEditions,
  type DigestRepository,
  type Edition,
} from "../../../../hermes/ai-x-digest/content/parser.ts"
export * from "../../../../hermes/ai-x-digest/content/parser.ts"

const execFileAsync = promisify(execFile)
let repository: Promise<DigestRepository> | undefined

export function loadDigestRepository(): Promise<DigestRepository> {
  repository ??= (async () => {
    const repositoryRoot = (
      await execFileAsync("git", ["rev-parse", "--show-toplevel"], {
        cwd: process.cwd(),
        encoding: "utf8",
      })
    ).stdout.trim()
    const git = async (args: string[]) =>
      (
        await execFileAsync("git", args, {
          cwd: repositoryRoot,
          encoding: "utf8",
          maxBuffer: 32 * 1024 * 1024,
        })
      ).stdout
    const sourceRevision = (await git(["rev-parse", "HEAD"])).trim()
    const paths = (
      await git(["ls-tree", "-r", "--name-only", "-z", sourceRevision, "--", "content/digests/"])
    )
      .split("\0")
      .filter((path) => /^content\/digests\/x-ai-\d{4}-\d{2}-\d{2}\.md$/.test(path))
    const inputs = await Promise.all(
      paths.map(async (path) => ({
        filename: path.slice("content/digests/".length),
        text: await git(["show", `${sourceRevision}:${path}`]),
      })),
    )
    return { sourceRevision, editions: parseEditions(inputs) }
  })()
  return repository
}

export async function loadEditions(): Promise<Edition[]> {
  return (await loadDigestRepository()).editions
}
